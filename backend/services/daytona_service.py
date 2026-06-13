import os
import json
from datetime import datetime, timedelta


def check_fraud_signals(db, claim_id: str, policy_number: str, video_analysis: dict) -> dict:
    """
    Cross-claim fraud detection. Queries DB before Daytona runs.
    Returns fraud_flags dict with any signals found.
    """
    from database import ClaimRecord

    flags = []
    details = {}

    now = datetime.utcnow()
    plate_hint = _extract_plate_hint(video_analysis)

    try:
        # 1. Same policy filed twice in past 30 days
        cutoff_30d = now - timedelta(days=30)
        recent_same_policy = (
            db.query(ClaimRecord)
            .filter(
                ClaimRecord.policy_number == policy_number,
                ClaimRecord.claim_id != claim_id,
                ClaimRecord.created_at >= cutoff_30d,
                ClaimRecord.status != "error",
            )
            .count()
        )
        if recent_same_policy > 0:
            flags.append("FRAUD-01")
            details["FRAUD-01"] = f"Policy {policy_number} has {recent_same_policy} other claim(s) in past 30 days"

        # 2. Claim filed within 24 hours of a PREVIOUS claim by same policy (very recent)
        cutoff_24h = now - timedelta(hours=24)
        very_recent = (
            db.query(ClaimRecord)
            .filter(
                ClaimRecord.policy_number == policy_number,
                ClaimRecord.claim_id != claim_id,
                ClaimRecord.created_at >= cutoff_24h,
            )
            .count()
        )
        if very_recent > 0:
            flags.append("FRAUD-02")
            details["FRAUD-02"] = f"Another claim on policy {policy_number} filed within last 24 hours"

        # 3. Multiple claims with same vehicle description (plate fingerprint)
        if plate_hint:
            plate_duplicates = (
                db.query(ClaimRecord)
                .filter(
                    ClaimRecord.claim_id != claim_id,
                    ClaimRecord.status != "error",
                )
                .all()
            )
            dupe_count = sum(
                1 for c in plate_duplicates
                if c.video_analysis and _extract_plate_hint(c.video_analysis) == plate_hint
            )
            if dupe_count > 0:
                flags.append("FRAUD-03")
                details["FRAUD-03"] = f"Vehicle fingerprint '{plate_hint}' appears in {dupe_count} other claim(s)"

    except Exception as exc:
        print(f"[Daytona/Fraud] DB query error: {exc}")

    return {
        "fraud_flags": flags,
        "fraud_details": details,
        "fraud_detected": len(flags) > 0,
    }


def _extract_plate_hint(video_analysis: dict) -> str:
    """Extract a vehicle plate fingerprint from audio evidence or damage description."""
    if not video_analysis:
        return ""
    audio = (video_analysis.get("audio_evidence") or "").lower()
    summary = (video_analysis.get("summary") or "").lower()
    # Look for plate-like patterns mentioned in audio
    import re
    plate_pattern = re.compile(r'\b[a-z]{1,3}\d{3,4}[a-z]{0,2}\b')
    for text in [audio, summary]:
        m = plate_pattern.search(text)
        if m:
            return m.group(0).upper()
    return ""


def _claim_agent_logic(video: dict, identity: dict, kimi: dict, myinfo: dict = None, fraud: dict = None) -> dict:
    """
    ClaimAgent rules engine.
    Hard exclusions → immediate REJECT with score floor of 0.
    Soft factors applied on top of base scoring.
    """
    score = 0
    breakdown = {}
    hard_reject = False
    hard_reject_reasons = []
    myinfo = myinfo or {}

    # ── HARD EXCLUSIONS (from policy EXCL-01 to EXCL-08) ──────────────────────
    exclusions = kimi.get("exclusions_triggered", [])
    identity_score = identity.get("identity_score", 0)

    # MyInfo hard checks — suspended licence = automatic reject
    if myinfo.get("licence_suspended"):
        hard_reject = True
        hard_reject_reasons.append("MYINFO: driving_licence_suspended")
        breakdown["MYINFO_licence_suspended"] = -1000

    if not identity.get("verified") or identity_score < 75:
        hard_reject = True
        hard_reject_reasons.append("EXCL-08: identity_not_verified")
        breakdown["EXCL-08_identity_failed"] = -1000

    if not video.get("collision"):
        hard_reject = True
        hard_reject_reasons.append("EXCL-05: no_collision_evidence")
        breakdown["EXCL-05_no_collision"] = -1000

    if video.get("fault") == "claimant":
        hard_reject = True
        hard_reject_reasons.append("EXCL-01: claimant_at_fault")
        breakdown["EXCL-01_claimant_fault"] = -1000

    if video.get("single_vehicle"):
        hard_reject = True
        hard_reject_reasons.append("EXCL-05: single_vehicle_no_external_cause")
        breakdown["EXCL-05_single_vehicle"] = -1000

    if "EXCL-03" in exclusions:
        hard_reject = True
        hard_reject_reasons.append("EXCL-03: distracted_driving")
        breakdown["EXCL-03_distracted_driving"] = -1000

    if hard_reject:
        return {
            "trust_score": 0,
            "risk_level": "HIGH",
            "decision": "REJECT",
            "breakdown": breakdown,
            "hard_reject": True,
            "hard_reject_reasons": hard_reject_reasons,
        }

    # ── BASE SCORING ───────────────────────────────────────────────────────────
    # T3 gradient — identity score used as a continuous signal, not just pass/fail
    if identity_score >= 95:
        score += 350
        breakdown["T3_identity_high_trust"] = 350
    elif identity_score >= 80:
        score += 300
        breakdown["T3_identity_verified"] = 300
    else:
        # 75-79: borderline pass — flag but don't reject
        score += 200
        breakdown["T3_identity_borderline"] = 200

    score += 300
    breakdown["collision_confirmed"] = 300

    sev = video.get("severity", "none")
    if sev == "high":
        score += 200
        breakdown["severity_high"] = 200
    elif sev == "medium":
        score += 150
        breakdown["severity_medium"] = 150
    elif sev == "low":
        score += 50
        breakdown["severity_low"] = 50

    # ── SOFT FACTORS (from policy SOFT-01 to SOFT-08) ─────────────────────────
    fault = video.get("fault", "unknown")
    conditions = video.get("conditions", "clear_daylight")
    vehicle_count = video.get("vehicle_count", 1)

    if fault == "other_party":
        score += 100
        breakdown["SOFT-01_not_at_fault"] = 100

    if conditions == "adverse_weather":
        score += 50
        breakdown["SOFT-02_adverse_weather"] = 50

    if vehicle_count >= 3:
        score += 50
        breakdown["SOFT-03_multiple_vehicles"] = 50

    if fault == "other_party" and vehicle_count >= 2:
        score += 100
        breakdown["SOFT-04_clear_other_fault"] = 100

    if sev == "low":
        score -= 75
        breakdown["SOFT-05_low_severity_penalty"] = -75

    if conditions == "night_low_visibility":
        score -= 50
        breakdown["SOFT-06_night_visibility"] = -50

    if fault == "unknown_hit_and_run":
        score -= 100
        breakdown["SOFT-07_hit_and_run"] = -100

    # ── MYINFO SCORING ─────────────────────────────────────────────────────────
    if myinfo.get("verified"):
        myinfo_score = myinfo.get("myinfo_score", 0)
        demerit = myinfo.get("demerit_points", 0)
        ownership = myinfo.get("vehicle_ownership_confirmed", False)

        if myinfo_score >= 90:
            score += 100
            breakdown["MYINFO_high_trust"] = 100
        elif myinfo_score >= 70:
            score += 50
            breakdown["MYINFO_verified"] = 50

        if ownership:
            score += 75
            breakdown["MYINFO_vehicle_ownership_confirmed"] = 75

        if demerit >= 12:
            score -= 80
            breakdown["MYINFO_high_demerit_points"] = -80
        elif demerit >= 6:
            score -= 30
            breakdown["MYINFO_moderate_demerit_points"] = -30

    # ── FRAUD DETECTION (cross-claim signals) ─────────────────────────────────
    fraud = fraud or {}
    fraud_flags = fraud.get("fraud_flags", [])

    if "FRAUD-01" in fraud_flags:
        # Same policy filed twice in 30 days → auto reject
        hard_reject = True
        hard_reject_reasons.append("FRAUD-01: duplicate_policy_claim_30_days")
        breakdown["FRAUD-01_duplicate_policy"] = -1000
        # Return immediately — this is a hard fraud rejection
        return {
            "trust_score": 0,
            "risk_level": "HIGH",
            "decision": "REJECT",
            "breakdown": breakdown,
            "hard_reject": True,
            "hard_reject_reasons": hard_reject_reasons,
            "fraud_flags": fraud_flags,
            "fraud_details": fraud.get("fraud_details", {}),
        }

    if "FRAUD-02" in fraud_flags:
        # Filed within 24h of another claim → heavy score penalty + force REVIEW
        score -= 200
        breakdown["FRAUD-02_rapid_refiling_penalty"] = -200

    if "FRAUD-03" in fraud_flags:
        # Same vehicle fingerprint elsewhere → suspicious, force REVIEW
        score -= 150
        breakdown["FRAUD-03_vehicle_fingerprint_match"] = -150

    # ── FINAL CLAMP + DECISION ─────────────────────────────────────────────────
    score = max(0, min(1000, score))

    # Hit and run always forces REVIEW regardless of score
    if fault == "unknown_hit_and_run":
        return {
            "trust_score": score,
            "risk_level": "MEDIUM",
            "decision": "REVIEW",
            "breakdown": breakdown,
            "hard_reject": False,
            "hard_reject_reasons": [],
            "fraud_flags": fraud_flags,
            "fraud_details": fraud.get("fraud_details", {}),
        }

    # Fraud signals that don't hard-reject still force REVIEW
    if fraud_flags and score < 700:
        return {
            "trust_score": score,
            "risk_level": "MEDIUM",
            "decision": "REVIEW",
            "breakdown": breakdown,
            "hard_reject": False,
            "hard_reject_reasons": [],
            "fraud_flags": fraud_flags,
            "fraud_details": fraud.get("fraud_details", {}),
        }

    if score >= 700:
        risk_level, decision = "LOW", "APPROVE"
    elif score >= 400:
        risk_level, decision = "MEDIUM", "REVIEW"
    else:
        risk_level, decision = "HIGH", "REJECT"

    return {
        "trust_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "breakdown": breakdown,
        "hard_reject": False,
        "hard_reject_reasons": [],
        "fraud_flags": fraud_flags,
        "fraud_details": fraud.get("fraud_details", {}),
    }


async def run_claim_agent(
    video_analysis: dict,
    identity_result: dict,
    kimi_result: dict = None,
    myinfo_result: dict = None,
    fraud_result: dict = None,
) -> dict:
    api_key = os.getenv("DAYTONA_API_KEY", "").strip()
    kimi_result = kimi_result or {}
    myinfo_result = myinfo_result or {}
    fraud_result = fraud_result or {}

    if api_key:
        try:
            return await _run_in_sandbox(api_key, video_analysis, identity_result, kimi_result, myinfo_result, fraud_result)
        except Exception as exc:
            print(f"[Daytona] Sandbox error: {exc} — falling back to local")

    return _claim_agent_logic(video_analysis, identity_result, kimi_result, myinfo_result, fraud_result)


async def _run_in_sandbox(api_key: str, video: dict, identity: dict, kimi: dict, myinfo: dict = None, fraud: dict = None) -> dict:
    from daytona import Daytona, DaytonaConfig

    config = DaytonaConfig(api_key=api_key)
    client = Daytona(config)
    print("[Daytona] Creating sandbox...")
    sandbox = client.create()

    agent_code = f"""
import json

video = {json.dumps(video)}
identity = {json.dumps(identity)}
kimi = {json.dumps(kimi)}

score = 0
breakdown = {{}}
hard_reject = False
hard_reject_reasons = []

exclusions = kimi.get("exclusions_triggered", [])
identity_score = identity.get("identity_score", 0)

if not identity.get("verified") or identity_score < 75:
    hard_reject = True
    hard_reject_reasons.append("EXCL-08: identity_not_verified")
    breakdown["EXCL-08_identity_failed"] = -1000

if not video.get("collision"):
    hard_reject = True
    hard_reject_reasons.append("EXCL-05: no_collision_evidence")
    breakdown["EXCL-05_no_collision"] = -1000

if video.get("fault") == "claimant":
    hard_reject = True
    hard_reject_reasons.append("EXCL-01: claimant_at_fault")
    breakdown["EXCL-01_claimant_fault"] = -1000

if video.get("single_vehicle"):
    hard_reject = True
    hard_reject_reasons.append("EXCL-05: single_vehicle_no_external_cause")
    breakdown["EXCL-05_single_vehicle"] = -1000

if hard_reject:
    print(json.dumps({{"trust_score": 0, "risk_level": "HIGH", "decision": "REJECT",
        "breakdown": breakdown, "hard_reject": True, "hard_reject_reasons": hard_reject_reasons}}))
else:
    if identity_score >= 95: score += 350; breakdown["T3_identity_high_trust"] = 350
    elif identity_score >= 80: score += 300; breakdown["T3_identity_verified"] = 300
    else: score += 200; breakdown["T3_identity_borderline"] = 200
    score += 300
    breakdown["collision_confirmed"] = 300

    sev = video.get("severity", "none")
    if sev == "high": score += 200; breakdown["severity_high"] = 200
    elif sev == "medium": score += 150; breakdown["severity_medium"] = 150
    elif sev == "low": score += 50; breakdown["severity_low"] = 50

    fault = video.get("fault", "unknown")
    conditions = video.get("conditions", "clear_daylight")
    vehicle_count = video.get("vehicle_count", 1)

    if fault == "other_party": score += 100; breakdown["SOFT-01_not_at_fault"] = 100
    if conditions == "adverse_weather": score += 50; breakdown["SOFT-02_adverse_weather"] = 50
    if vehicle_count >= 3: score += 50; breakdown["SOFT-03_multiple_vehicles"] = 50
    if fault == "other_party" and vehicle_count >= 2: score += 100; breakdown["SOFT-04_clear_other_fault"] = 100
    if sev == "low": score -= 75; breakdown["SOFT-05_low_severity"] = -75
    if conditions == "night_low_visibility": score -= 50; breakdown["SOFT-06_night"] = -50
    if fault == "unknown_hit_and_run": score -= 100; breakdown["SOFT-07_hit_and_run"] = -100

    score = max(0, min(1000, score))

    if fault == "unknown_hit_and_run":
        decision, risk_level = "REVIEW", "MEDIUM"
    elif score >= 700: decision, risk_level = "APPROVE", "LOW"
    elif score >= 400: decision, risk_level = "REVIEW", "MEDIUM"
    else: decision, risk_level = "REJECT", "HIGH"

    print(json.dumps({{"trust_score": score, "risk_level": risk_level, "decision": decision,
        "breakdown": breakdown, "hard_reject": False, "hard_reject_reasons": []}}))
"""

    response = sandbox.process.code_run(agent_code)
    if response.exit_code != 0:
        raise RuntimeError(f"ClaimAgent failed: {response.result}")

    print(f"[Daytona] ClaimAgent result: {response.result}")
    return json.loads(response.result)
