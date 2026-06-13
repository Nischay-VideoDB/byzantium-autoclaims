from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ClaimUploadResponse(BaseModel):
    claim_id: str
    message: str
    status: str


class VideoAnalysis(BaseModel):
    collision: bool
    severity: str           # none | low | medium | high
    timestamp: str
    summary: str
    fault: str = "unknown"  # claimant | other_party | unknown | unknown_hit_and_run
    vehicle_count: int = 1
    conditions: str = "clear_daylight"  # clear_daylight | night_low_visibility | adverse_weather | car_park
    single_vehicle: bool = False
    audio_evidence: str = "No audio data available."
    damage_description: str = "Not assessed."
    clip_url: str = ""
    frame_url: str = ""               # still frame at crash moment
    plate_detected: str = "not_visible"  # plate extracted from footage
    camera_pov: str = "unknown"       # first_person | third_person | unknown
    point_of_impact: str = "unknown"  # front | rear | driver_side | passenger_side | unknown
    source: str = "videodb"


class NosanaAnalysis(BaseModel):
    job_id: str
    status: str
    compute: str
    source: str = "nosana"
    clip_verdict: str = ""           # COLLISION_CONFIRMED | COLLISION_POSSIBLE | NO_COLLISION_DETECTED
    collision_signal_strength: int = 0  # 0-100
    impact_timestamp: str = ""
    motion_score: int = 0
    integrity_score: int = 0
    temporal_consistency: bool = True
    editing_artifacts_detected: bool = False
    corroboration: str = "UNKNOWN"   # STRONG | MODERATE | WEAK
    scene_labels: list = []
    summary: str = ""
    frame_count_analyzed: int = 0


class IdentityResult(BaseModel):
    verified: bool
    identity_score: int
    source: str = "terminal3"


class MyInfoResult(BaseModel):
    verified: bool
    nric: str
    full_name: str
    vehicle_plate: str
    vehicle_make: str
    vehicle_model: str
    licence_valid: bool
    licence_class: str
    demerit_points: int
    licence_suspended: bool
    vehicle_ownership_confirmed: bool
    myinfo_score: int           # 0-100
    source: str = "myinfo-proxy"
    triggered_by: str = ""
    raw: dict = {}


class KimiResult(BaseModel):
    decision: str  # APPROVE | REJECT | REVIEW
    reason: str
    confidence: float
    source: str = "kimi"
    exclusions_triggered: list = []
    soft_factors_applied: list = []


class TrustScoreResult(BaseModel):
    trust_score: int
    risk_level: str  # LOW | MEDIUM | HIGH
    decision: str    # APPROVE | REJECT | REVIEW
    reason: str
    breakdown: dict


class AnalysisResponse(BaseModel):
    claim_id: str
    video_analysis: VideoAnalysis
    identity_result: IdentityResult
    myinfo_result: Optional[MyInfoResult] = None
    kimi_result: KimiResult
    trust_score_result: TrustScoreResult
    nosana_job_id: Optional[str] = None
    payout_amount: float
    status: str


class ReceiptResponse(BaseModel):
    claim_id: str
    claimant_name: str
    policy_number: str
    identity_status: str
    video_status: str
    trust_score: int
    risk_level: str
    decision: str
    reason: str
    payout_amount: float
    timestamp: str
    receipt_number: str
    frame_url: str = ""
    clip_url: str = ""
    plate_detected: str = "not_visible"
