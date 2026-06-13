"""
Byzantium Auto Insurance — Standard Comprehensive Policy
Used by Kimi (inference) and Daytona ClaimAgent (hard rules).
"""

POLICY_DOCUMENT = """
=======================================================
BYZANTIUM AUTO INSURANCE — STANDARD COMPREHENSIVE POLICY
Policy Version: 2024-B1
=======================================================

SECTION 1 — COVERED EVENTS
--------------------------------------------------
The following incidents are covered under this policy:
- Rear-end collision (claimant stationary or slow-moving)
- Side-impact / T-bone collision at intersection
- Head-on collision where claimant was NOT the primary aggressor
- Multi-vehicle pile-up involvement
- Weather-induced collision (ice, flood, low visibility)
- Hit and run (requires REVIEW — not auto-approved)

SECTION 2 — HARD EXCLUSIONS (Automatic REJECT — no exceptions)
--------------------------------------------------
EXCL-01: Claimant was the at-fault driver in a head-on collision
EXCL-02: Incident occurred in a private car park at high speed
EXCL-03: Evidence of distracted driving (phone use, reckless behavior visible in footage)
EXCL-04: Vehicle type in footage does not match insured vehicle class
EXCL-05: Incident is a single-vehicle accident with no external cause (e.g. self-inflicted crash, wall, barrier)
EXCL-06: Footage shows pre-existing damage inconsistent with the claimed incident
EXCL-07: Claim filed more than 30 days after incident date
EXCL-08: Claimant identity cannot be verified

SECTION 3 — SOFT FACTORS (Inference — adjust trust score)
--------------------------------------------------
SOFT-01: Claimant vehicle was stationary at time of impact → strong indicator of non-fault → +100
SOFT-02: Adverse weather or low visibility conditions → mitigating factor → +50
SOFT-03: Multiple vehicles visible → corroborating evidence → +50
SOFT-04: Dashcam clearly shows fault of other party → high evidence quality → +100
SOFT-05: Severity LOW with no visible structural damage → reduced payout justification → -75
SOFT-06: Night-time incident, poor footage quality → reduced evidence confidence → -50
SOFT-07: Hit and run — no other party identifiable → requires human review → -100 (flag REVIEW)
SOFT-08: Single vehicle incident without clear external cause → suspicious → -150

SECTION 4 — PAYOUT LIMITS
--------------------------------------------------
Severity LOW    : Maximum payout $1,000
Severity MEDIUM : Maximum payout $5,000
Severity HIGH   : Maximum payout $15,000
Annual claim limit: $25,000 per policy

SECTION 5 — COVERAGE CONDITIONS
--------------------------------------------------
COND-01: Policy must be active at the time of the incident
COND-02: Driver must be the named insured or listed additional driver
COND-03: Incident must be reported within 30 days
COND-04: Dashcam footage must be original and unedited
COND-05: Identity must be verifiable via approved methods

SECTION 6 — DECISION GUIDELINES FOR CLAIMS OFFICERS
--------------------------------------------------
APPROVE  : Hard exclusions clear + positive soft factors + identity verified + collision confirmed
REVIEW   : Hit and run / borderline fault / poor footage quality / low confidence identity
REJECT   : Any hard exclusion triggered OR identity failed OR no collision evidence
=======================================================
"""

HARD_EXCLUSION_CODES = [
    "EXCL-01", "EXCL-02", "EXCL-03", "EXCL-04",
    "EXCL-05", "EXCL-06", "EXCL-07", "EXCL-08",
]

SOFT_FACTOR_SCORES = {
    "SOFT-01": +100,  # stationary at impact
    "SOFT-02": +50,   # adverse weather
    "SOFT-03": +50,   # multiple vehicles
    "SOFT-04": +100,  # clear fault of other party
    "SOFT-05": -75,   # low severity / no visible damage
    "SOFT-06": -50,   # night-time / poor footage
    "SOFT-07": -100,  # hit and run
    "SOFT-08": -150,  # single vehicle, no external cause
}

PAYOUT_LIMITS = {
    "high":   15000.0,
    "medium":  5000.0,
    "low":     1000.0,
    "none":       0.0,
}


def get_policy_prompt_block() -> str:
    return POLICY_DOCUMENT


def apply_soft_factors(triggered_codes: list[str]) -> tuple[int, dict]:
    """Return (total_delta, breakdown) for triggered soft factor codes."""
    delta = 0
    breakdown = {}
    for code in triggered_codes:
        if code in SOFT_FACTOR_SCORES:
            breakdown[code] = SOFT_FACTOR_SCORES[code]
            delta += SOFT_FACTOR_SCORES[code]
    return delta, breakdown


def get_payout_limit(severity: str) -> float:
    return PAYOUT_LIMITS.get(severity.lower(), 500.0)
