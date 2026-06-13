from models import TrustScoreResult, VideoAnalysis, IdentityResult, KimiResult
from services.policy_service import apply_soft_factors, get_payout_limit


def calculate_trust_score(
    video: VideoAnalysis,
    identity: IdentityResult,
    kimi: KimiResult,
    daytona_result: dict,
) -> TrustScoreResult:
    """
    Daytona ran hard rules + soft factor base calculation.
    Byzantium applies Kimi's AI confidence adjustment on top.
    """
    # If Daytona hard-rejected, trust score is 0 — no overrides
    if daytona_result.get("hard_reject"):
        reasons = daytona_result.get("hard_reject_reasons", [])
        return TrustScoreResult(
            trust_score=0,
            risk_level="HIGH",
            decision="REJECT",
            reason=f"Hard policy exclusion(s) triggered: {', '.join(reasons)}. Automatic rejection per Byzantium policy.",
            breakdown=daytona_result["breakdown"],
        )

    score = daytona_result["trust_score"]
    breakdown = dict(daytona_result["breakdown"])

    # Kimi AI confidence bonus/penalty
    if kimi.decision == "APPROVE" and kimi.confidence >= 0.85:
        bonus = int(kimi.confidence * 50)
        score = min(1000, score + bonus)
        breakdown["kimi_confidence_bonus"] = bonus
    elif kimi.decision == "REJECT" and not daytona_result.get("hard_reject"):
        penalty = int(kimi.confidence * 40)
        score = max(0, score - penalty)
        breakdown["kimi_confidence_penalty"] = -penalty

    trust_score = max(0, min(1000, score))

    # Final decision — Daytona's hit-and-run REVIEW overrides score threshold
    if daytona_result.get("decision") == "REVIEW" and video.fault == "unknown_hit_and_run":
        risk_level, decision = "MEDIUM", "REVIEW"
    elif trust_score >= 700:
        risk_level, decision = "LOW", "APPROVE"
    elif trust_score >= 400:
        risk_level, decision = "MEDIUM", "REVIEW"
    else:
        risk_level, decision = "HIGH", "REJECT"

    # Build reason
    soft = kimi.soft_factors_applied or []
    excl = kimi.exclusions_triggered or []

    if decision == "APPROVE":
        reason = (
            f"Claim approved. Collision confirmed ({video.severity} severity), "
            f"identity verified ({identity.identity_score}/100), "
            f"fault: {video.fault.replace('_', ' ')}. "
            f"Policy soft factors applied: {', '.join(soft) or 'none'}. "
            f"Trust score: {trust_score}/1000."
        )
    elif decision == "REJECT":
        reason = (
            f"Claim rejected. "
            f"{kimi.reason} "
            f"Trust score: {trust_score}/1000."
        )
    else:
        reason = (
            f"Manual review required. "
            f"{kimi.reason} "
            f"Trust score: {trust_score}/1000."
        )

    return TrustScoreResult(
        trust_score=trust_score,
        risk_level=risk_level,
        decision=decision,
        reason=reason,
        breakdown=breakdown,
    )


def calculate_payout(decision: str, severity: str) -> float:
    if decision != "APPROVE":
        return 0.0
    return get_payout_limit(severity)
