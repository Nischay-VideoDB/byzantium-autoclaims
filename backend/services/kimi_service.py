import os
import json
from models import KimiResult, VideoAnalysis, IdentityResult, MyInfoResult
from services.policy_service import get_policy_prompt_block
from typing import Optional, Any

SYSTEM_PROMPT = (
    "You are a senior insurance claims officer at Byzantium Insurance. "
    "You will be given a policy document, video evidence facts, and identity verification results. "
    "Your job is to cross-reference the evidence against the policy and decide: APPROVE, REJECT, or REVIEW. "
    "Apply hard exclusions strictly — if any exclusion is triggered, you MUST REJECT. "
    "Apply soft factors to adjust your reasoning. "
    "Respond ONLY with valid JSON in this exact format: "
    '{"decision": "APPROVE|REJECT|REVIEW", "reason": "...", "confidence": 0.0-1.0, '
    '"exclusions_triggered": ["EXCL-XX", ...], "soft_factors_applied": ["SOFT-XX", ...]}'
)


def _build_user_prompt(
    video: VideoAnalysis,
    identity: IdentityResult,
    myinfo: Optional[MyInfoResult] = None,
    nosana: Optional[dict] = None,
    fraud: Optional[dict] = None,
) -> str:
    # Use SenseNova-extracted policy if available, else hardcoded
    try:
        from services.sensenova_service import get_active_policy_text, has_custom_policy
        policy_block = get_active_policy_text() if has_custom_policy() else get_policy_prompt_block()
    except Exception:
        policy_block = get_policy_prompt_block()

    return f"""
{policy_block}

=== CLAIM EVIDENCE ===

VIDEO ANALYSIS — Visual (camera POV: {video.camera_pov}):
- Camera perspective: {'FIRST-PERSON (camera car = claimant vehicle)' if video.camera_pov == 'first_person' else 'THIRD-PERSON (claimant vehicle visible in frame)' if video.camera_pov == 'third_person' else 'unknown POV'}
- Collision detected: {video.collision}
- Severity: {video.severity}
- Timestamp: {video.timestamp}
- Point of impact: {video.point_of_impact}
- Fault determination: {video.fault}
- Vehicles involved: {video.vehicle_count}
- Conditions: {video.conditions}
- Single-vehicle incident: {video.single_vehicle}
- Visible damage: {video.damage_description}
- Scene summary: {video.summary}

VIDEO ANALYSIS — Audio (extracted by VideoDB spoken word indexing):
- Audio evidence: {video.audio_evidence}

NOSANA GPU CORROBORATION (CLIP-ViT-B/32 frame analysis):
{_nosana_block(nosana)}

IDENTITY VERIFICATION (Terminal 3 TEE attestation):
- Verified: {identity.verified}
- Identity score: {identity.identity_score}/100

MYINFO GOVERNMENT VERIFICATION (SingPass):
{_myinfo_block(myinfo)}

FRAUD DETECTION (Daytona cross-claim analysis):
{_fraud_block(fraud)}

=== YOUR TASK ===
1. Consider camera POV — first-person means camera car IS the claimant's vehicle.
2. Use visual, audio, Nosana GPU corroboration, AND MyInfo government data.
3. Check every hard exclusion (EXCL-01 through EXCL-08). List any triggered.
4. Identify applicable soft factors (SOFT-01 through SOFT-08). List them.
5. Make a final decision: APPROVE / REJECT / REVIEW with a clear reason.
6. If ANY hard exclusion is triggered → decision MUST be REJECT.
7. If hit-and-run (fault=unknown_hit_and_run) → decision MUST be REVIEW.
8. If MyInfo shows SUSPENDED licence → trigger EXCL-08 equivalent and REJECT.
9. If fraud flags present → include in reasoning, bias toward REVIEW or REJECT.
10. If Nosana corroboration is WEAK and VideoDB shows collision → flag for REVIEW.

Respond with JSON only.
"""


def _nosana_block(nosana: Optional[dict]) -> str:
    if not nosana or not nosana.get("clip_verdict"):
        return "- Not available"
    lines = [
        f"- Collision verdict: {nosana.get('clip_verdict')}",
        f"- Signal strength: {nosana.get('collision_signal_strength', 0)}/100",
        f"- Impact timestamp: {nosana.get('impact_timestamp', 'N/A')}",
        f"- Footage integrity: {nosana.get('integrity_score', 0)}/100",
        f"- Temporal consistency: {'PASS' if nosana.get('temporal_consistency') else 'FAIL — possible editing'}",
        f"- Editing artifacts: {'Detected — CAUTION' if nosana.get('editing_artifacts_detected') else 'None detected'}",
        f"- Scene labels: {', '.join(nosana.get('scene_labels', []))}",
        f"- Corroboration vs VideoDB: {nosana.get('corroboration', 'UNKNOWN')}",
    ]
    return "\n".join(lines)


def _fraud_block(fraud: Optional[dict]) -> str:
    if not fraud or not fraud.get("fraud_detected"):
        return "- No fraud signals detected"
    flags = fraud.get("fraud_flags", [])
    details = fraud.get("fraud_details", {})
    lines = [f"- FRAUD FLAGS DETECTED: {', '.join(flags)}"]
    for flag, detail in details.items():
        lines.append(f"  {flag}: {detail}")
    lines.append("- ACTION: Bias toward REVIEW or REJECT. Do not auto-approve.")
    return "\n".join(lines)


def _myinfo_block(myinfo: Optional[MyInfoResult]) -> str:
    if not myinfo or not myinfo.verified:
        return "- Not available (NRIC not provided or verification skipped)"
    lines = [
        f"- Full name: {myinfo.full_name}",
        f"- Registered vehicle: {myinfo.vehicle_make} {myinfo.vehicle_model} ({myinfo.vehicle_plate})",
        f"- Vehicle ownership confirmed in video: {myinfo.vehicle_ownership_confirmed}",
        f"- Driving licence: {('VALID' if myinfo.licence_valid else 'INVALID/SUSPENDED')} — Class {myinfo.licence_class}",
        f"- Demerit points: {myinfo.demerit_points}/24",
        f"- Licence suspended: {myinfo.licence_suspended}",
        f"- MyInfo trust score: {myinfo.myinfo_score}/100",
        f"- Triggered by: {myinfo.triggered_by}",
    ]
    return "\n".join(lines)


def _mock_decision(video: VideoAnalysis, identity: IdentityResult, myinfo: Optional[MyInfoResult] = None, nosana: Optional[dict] = None, fraud: Optional[dict] = None) -> KimiResult:
    exclusions = []
    soft_factors = []

    # Hard exclusion checks
    if not identity.verified:
        exclusions.append("EXCL-08")
    if not video.collision:
        exclusions.append("EXCL-05")
    if video.fault == "claimant":
        exclusions.append("EXCL-01")
    if video.single_vehicle:
        exclusions.append("EXCL-05")
    # MyInfo hard checks
    if myinfo and myinfo.licence_suspended:
        exclusions.append("EXCL-MYINFO-SUSPENDED")

    # Soft factor checks
    if video.fault == "other_party" and video.vehicle_count >= 2:
        soft_factors.append("SOFT-01")
    if video.conditions == "adverse_weather":
        soft_factors.append("SOFT-02")
    if video.vehicle_count >= 3:
        soft_factors.append("SOFT-03")
    if video.fault == "other_party":
        soft_factors.append("SOFT-04")
    if video.severity == "low":
        soft_factors.append("SOFT-05")
    if video.conditions == "night_low_visibility":
        soft_factors.append("SOFT-06")
    if video.fault == "unknown_hit_and_run":
        soft_factors.append("SOFT-07")
    if video.single_vehicle:
        soft_factors.append("SOFT-08")

    # Fraud signals
    fraud_flags = (fraud or {}).get("fraud_flags", [])
    if fraud_flags:
        if "FRAUD-01" in fraud_flags:
            exclusions.append("FRAUD-01")
        elif "FRAUD-02" in fraud_flags or "FRAUD-03" in fraud_flags:
            soft_factors.append("FRAUD-SUSPICIOUS")

    if exclusions:
        reason = f"Hard exclusion(s) triggered: {', '.join(exclusions)}. "
        if "EXCL-08" in exclusions:
            reason += "Identity verification failed. "
        if "EXCL-01" in exclusions:
            reason += "Claimant was at fault in collision. "
        if "EXCL-05" in exclusions:
            reason += "Single-vehicle incident with no external cause. "
        if "FRAUD-01" in exclusions:
            reason += "Duplicate policy claim filed within 30 days — auto-rejected as fraudulent. "
        return KimiResult(
            decision="REJECT", reason=reason.strip(), confidence=0.95,
            source="kimi-mock",
            exclusions_triggered=exclusions, soft_factors_applied=soft_factors
        )

    # Nosana weak corroboration forces REVIEW
    nosana_corroboration = (nosana or {}).get("corroboration", "UNKNOWN")
    if nosana_corroboration == "WEAK" and video.collision:
        return KimiResult(
            decision="REVIEW",
            reason=f"VideoDB detected collision but Nosana GPU corroboration is WEAK (signal strength low). Requires human review.",
            confidence=0.72,
            source="kimi-mock",
            exclusions_triggered=[], soft_factors_applied=soft_factors
        )

    if video.fault == "unknown_hit_and_run":
        return KimiResult(
            decision="REVIEW",
            reason="Hit and run incident — no second party identifiable. Requires human verification per SOFT-07.",
            confidence=0.80,
            source="kimi-mock",
            exclusions_triggered=[], soft_factors_applied=soft_factors
        )

    if fraud_flags:
        return KimiResult(
            decision="REVIEW",
            reason=f"Fraud signals detected ({', '.join(fraud_flags)}). Claim requires manual review before approval.",
            confidence=0.78,
            source="kimi-mock",
            exclusions_triggered=[], soft_factors_applied=soft_factors
        )

    severity_map = {"high": "full coverage approved", "medium": "standard payout approved", "low": "minor incident, limited payout"}
    return KimiResult(
        decision="APPROVE",
        reason=f"No exclusions triggered. {severity_map.get(video.severity, 'claim approved')}. Soft factors: {', '.join(soft_factors) or 'none'}.",
        confidence=0.88,
        source="kimi-mock",
        exclusions_triggered=[], soft_factors_applied=soft_factors
    )


async def evaluate_claim(
    video: VideoAnalysis,
    identity: IdentityResult,
    myinfo: Optional[MyInfoResult] = None,
    nosana: Optional[dict] = None,
    fraud: Optional[dict] = None,
) -> KimiResult:
    kimi_key = os.getenv("KIMI_API_KEY", "").strip()
    kimi_base = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1").strip()
    tokenrouter_key = os.getenv("TOKENROUTER_API_KEY", "").strip()
    tokenrouter_base = os.getenv("TOKENROUTER_BASE_URL", "https://api.tokenrouter.com/v1").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    openrouter_key = os.getenv("OPEN_ROUTER_API_KEY", "").strip()

    user_prompt = _build_user_prompt(video, identity, myinfo, nosana, fraud)

    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
        result = await _call_openai_compatible(openrouter_key, "https://openrouter.ai/api/v1", model, user_prompt, "openrouter-live")
        if result:
            return result

    if kimi_key:
        result = await _call_openai_compatible(kimi_key, kimi_base, "moonshot-v1-8k", user_prompt, "kimi")
        if result:
            return result

    if tokenrouter_key:
        result = await _call_openai_compatible(tokenrouter_key, tokenrouter_base, "claude-sonnet-4-6", user_prompt, "tokenrouter")
        if result:
            return result

    if anthropic_key:
        result = await _call_anthropic(anthropic_key, user_prompt)
        if result:
            return result

    print("[Kimi] No API keys available — using policy-aware mock")
    return _mock_decision(video, identity, myinfo, nosana, fraud)


async def _call_openai_compatible(api_key, base_url, model, user_prompt, source) -> KimiResult | None:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return KimiResult(
            decision=data["decision"].upper(),
            reason=data["reason"],
            confidence=float(data.get("confidence", 0.85)),
            source=source,
            exclusions_triggered=data.get("exclusions_triggered", []),
            soft_factors_applied=data.get("soft_factors_applied", []),
        )
    except Exception as exc:
        print(f"[Kimi/{source}] Error: {exc}")
        return None


async def _call_anthropic(api_key, user_prompt) -> KimiResult | None:
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return KimiResult(
            decision=data["decision"].upper(),
            reason=data["reason"],
            confidence=float(data.get("confidence", 0.85)),
            source="claude",
            exclusions_triggered=data.get("exclusions_triggered", []),
            soft_factors_applied=data.get("soft_factors_applied", []),
        )
    except Exception as exc:
        print(f"[Anthropic] Error: {exc}")
        return None
