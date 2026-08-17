"""Byzantium AutoClaims - FastAPI backend."""

import os
import uuid
import json
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import init_db, get_db, ClaimRecord
from models import (
    ClaimUploadResponse,
    AnalysisResponse,
    ReceiptResponse,
    VideoAnalysis,
    IdentityResult,
    KimiResult,
    TrustScoreResult,
)
from services.videodb_service import VideoEvidenceUnavailable, analyze_video
from services.terminal3_service import verify_identity
from services.myinfo_service import verify_myinfo, _should_trigger as myinfo_needed
from services.kimi_service import evaluate_claim
from services.daytona_service import run_claim_agent, check_fraud_signals
from services.nosana_service import submit_processing_job
from services.sensenova_service import ingest_policy_pdf, has_custom_policy, auto_load_policies, lookup_policy
from services.trustgrid_service import calculate_trust_score, calculate_payout

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

IS_VERCEL = bool(os.getenv("VERCEL"))


def _is_public_demo() -> bool:
    """Vercel hosts a prepared, synthetic-only showcase - never live claim intake."""
    return IS_VERCEL or os.getenv("BYZANTIUM_DEMO_MODE", "").lower() in {"1", "true", "yes"}


def _runtime_directory(variable: str, local_default: str, ephemeral_name: str) -> Path:
    """Resolve writable storage without creating persistent paths during import."""
    if IS_VERCEL:
        return Path("/tmp") / "byzantium-autoclaims" / ephemeral_name
    return Path(os.getenv(variable, local_default))


def _upload_directory() -> Path:
    path = _runtime_directory("UPLOAD_DIR", "uploads", "uploads")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _policy_directory() -> Path:
    path = _runtime_directory("POLICY_DIR", "policies", "policies")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _require_private_claim_workflow() -> None:
    if _is_public_demo():
        raise HTTPException(
            status_code=403,
            detail="This public showcase accepts no uploads, policy records, or personal claim data.",
        )


def _require_final_video_evidence(video_result: VideoAnalysis) -> None:
    if video_result.source == "videodb-mock":
        raise VideoEvidenceUnavailable(
            "Synthetic VideoDB evidence is a prepared-demo placeholder and cannot produce a final claim decision."
        )


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    return origins or ["http://localhost:5173", "http://localhost:3000"]

app = FastAPI(
    title="Byzantium AutoClaims API",
    description="Autonomous insurance-claim decision support with a reviewable evidence trail.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.on_event("startup")
async def startup():
    init_db()
    print("[Byzantium] Database initialized")
    if _is_public_demo():
        print("[Byzantium] Public synthetic showcase - policy auto-load disabled")
    else:
        await auto_load_policies()
        print("[Byzantium] Policy auto-load complete")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Byzantium AutoClaims",
        "env": os.getenv("APP_ENV", "development"),
        "public_demo": _is_public_demo(),
        "integrations": {
            "videodb": bool(os.getenv("VIDEODB_API_KEY", "").strip()),
            "terminal3": bool(os.getenv("TERMINAL3_API_KEY", "").strip() and os.getenv("TERMINAL3_DID", "").strip()),
            "kimi": bool(os.getenv("KIMI_API_KEY", "").strip()),
            "tokenrouter": bool(os.getenv("TOKENROUTER_API_KEY", "").strip()),
            "daytona": bool(os.getenv("DAYTONA_API_KEY", "").strip()),
            "nosana": bool(os.getenv("NOSANA_API_KEY", "").strip()),
        },
    }


# ---------------------------------------------------------------------------
# POST /upload-video
# ---------------------------------------------------------------------------


@app.post("/upload-video", response_model=ClaimUploadResponse)
async def upload_video(
    video: UploadFile = File(...),
    claimant_name: str = Form(...),
    claimant_id_number: str = Form(default=""),
    nric: str = Form(default=""),
    vehicle_plate: str = Form(default=""),
    policy_number: str = Form(default=""),
    db: Session = Depends(get_db),
):
    _require_private_claim_workflow()
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"

    # Auto-lookup policy from plate if no policy number given
    norm_plate = vehicle_plate.strip().upper().replace(" ", "")
    resolved_policy_number = policy_number.strip()
    if not resolved_policy_number and norm_plate:
        pol = await lookup_policy(claimant_name, norm_plate)
        if pol:
            resolved_policy_number = pol.get("policy_number", "")
    if not resolved_policy_number:
        resolved_policy_number = f"POL-{claim_id[-6:]}"

    # Save uploaded video
    ext = Path(video.filename).suffix or ".mp4"
    video_filename = f"{claim_id}{ext}"
    video_path = _upload_directory() / video_filename

    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Create claim record
    claim = ClaimRecord(
        claim_id=claim_id,
        claimant_name=claimant_name,
        claimant_id_number=claimant_id_number,
        nric=nric.strip().upper() or None,
        vehicle_plate=norm_plate or None,
        policy_number=resolved_policy_number,
        video_path=str(video_path),
        video_filename=video_filename,
        status="uploaded",
    )
    db.add(claim)
    db.commit()

    return ClaimUploadResponse(
        claim_id=claim_id,
        message=f"Video uploaded successfully. Claim {claim_id} created.",
        status="uploaded",
    )


# ---------------------------------------------------------------------------
# POST /upload-policy  — SenseNova: ingest custom insurance policy PDF
# ---------------------------------------------------------------------------

@app.post("/upload-policy")
async def upload_policy(policy: UploadFile = File(...)):
    """
    Upload a PDF/image insurance policy document.
    SenseNova U1 extracts coverage terms, exclusions, and payout limits.
    The extracted policy replaces the hardcoded Byzantium policy for subsequent Kimi evaluations.
    """
    _require_private_claim_workflow()
    if not policy.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(policy.filename).suffix.lower()
    if ext not in {".pdf", ".png", ".jpg", ".jpeg", ".pptx", ".docx"}:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, image, or Office format.")

    safe_name = f"policy-{uuid.uuid4().hex[:8]}{ext}"
    policy_path = _policy_directory() / safe_name

    with open(policy_path, "wb") as f:
        shutil.copyfileobj(policy.file, f)

    try:
        result = await ingest_policy_pdf(str(policy_path))
        return {
            "status": "ingested",
            "policy_name": result["policy_name"],
            "source": result["source"],
            "message": f"Policy '{result['policy_name']}' ingested via SenseNova U1. All new evaluations will use this policy.",
            "filename": policy.filename,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Policy ingestion failed: {str(exc)}")


@app.get("/active-policy")
def get_active_policy():
    return {
        "has_custom_policy": has_custom_policy(),
        "message": "Custom policy active" if has_custom_policy() else "Using default Byzantium policy",
    }


@app.get("/lookup-policy")
async def lookup_policy_endpoint(name: str = "", plate: str = ""):
    """
    Lookup a policy document by claimant name + vehicle plate.
    Returns matched policy details and name/plate verification result.
    """
    _require_private_claim_workflow()
    if not plate:
        raise HTTPException(status_code=400, detail="Vehicle plate is required")

    result = await lookup_policy(name, plate)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No policy document found for plate {plate.upper()}. "
                   "Please contact your insurer or upload your policy document manually.",
        )
    return result


# ---------------------------------------------------------------------------
# POST /verify-identity/{claim_id}
# ---------------------------------------------------------------------------


@app.post("/verify-identity/{claim_id}", response_model=IdentityResult)
async def verify_identity_endpoint(
    claim_id: str,
    db: Session = Depends(get_db),
):
    _require_private_claim_workflow()
    claim = _get_claim(db, claim_id)
    result = await verify_identity(
        claimant_name=claim.claimant_name or "",
        claimant_id=claim.claimant_id_number or "",
    )
    claim.identity_result = result.model_dump()
    db.commit()
    return result


# ---------------------------------------------------------------------------
# POST /analyze-claim/{claim_id}  — full pipeline
# ---------------------------------------------------------------------------


@app.post("/analyze-claim/{claim_id}", response_model=AnalysisResponse)
async def analyze_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    _require_private_claim_workflow()
    claim = _get_claim(db, claim_id)
    claim.status = "analyzing"
    db.commit()

    try:
        # 1. Nosana — submit GPU compute job
        nosana_job = await submit_processing_job(claim_id, claim.video_filename or "")
        claim.nosana_job = nosana_job
        db.commit()

        # 2. VideoDB — analyze dashcam footage
        video_result = await analyze_video(
            video_path=claim.video_path or "",
            filename=claim.video_filename or "",
        )
        _require_final_video_evidence(video_result)
        claim.video_analysis = video_result.model_dump()
        db.commit()

        # 3. Terminal 3 — verify identity
        identity_result = await verify_identity(
            claimant_name=claim.claimant_name or "",
            claimant_id=claim.claimant_id_number or "",
        )
        claim.identity_result = identity_result.model_dump()
        db.commit()

        # 4. Kimi — AI claims evaluation
        kimi_result = await evaluate_claim(video_result, identity_result)
        claim.kimi_result = kimi_result.model_dump()
        db.commit()

        # 5. Daytona — run ClaimAgent in secure sandbox (with Kimi's policy findings)
        daytona_result = await run_claim_agent(
            video_analysis=video_result.model_dump(),
            identity_result=identity_result.model_dump(),
            kimi_result=kimi_result.model_dump(),
        )

        # 6. TrustGrid — final trust score + decision
        trust_result = calculate_trust_score(
            video=video_result,
            identity=identity_result,
            kimi=kimi_result,
            daytona_result=daytona_result,
        )

        payout = calculate_payout(trust_result.decision, video_result.severity)

        # Persist final decision
        claim.trust_score = trust_result.trust_score
        claim.risk_level = trust_result.risk_level
        claim.decision = trust_result.decision
        claim.reason = trust_result.reason
        claim.payout_amount = payout
        claim.status = "complete"
        claim.decided_at = datetime.utcnow()
        db.commit()

        return AnalysisResponse(
            claim_id=claim_id,
            video_analysis=video_result,
            identity_result=identity_result,
            kimi_result=kimi_result,
            trust_score_result=trust_result,
            nosana_job_id=nosana_job.get("job_id"),
            payout_amount=payout,
            status="complete",
        )

    except VideoEvidenceUnavailable:
        claim.status = "error"
        db.commit()
        raise HTTPException(
            status_code=424,
            detail="Video evidence could not be verified. No final claim decision was generated.",
        )
    except Exception as exc:
        claim.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")


# ---------------------------------------------------------------------------
# GET /stream-claim/{claim_id}  — SSE: real-time pipeline events
# ---------------------------------------------------------------------------


@app.get("/stream-claim/{claim_id}")
async def stream_claim(claim_id: str):
    """
    Server-Sent Events endpoint. Streams each pipeline step as it completes
    so the frontend can update in real time rather than waiting for a single response.
    """

    _require_private_claim_workflow()

    async def event_generator():
        from database import SessionLocal

        def emit(step: str, status: str, data: dict = None) -> str:
            payload = {"step": step, "status": status, **(data or {})}
            return f"data: {json.dumps(payload)}\n\n"

        db = SessionLocal()
        try:
            claim = db.query(ClaimRecord).filter(ClaimRecord.claim_id == claim_id).first()
            if not claim:
                yield emit("error", "failed", {"message": f"Claim {claim_id} not found"})
                return

            claim.status = "analyzing"
            db.commit()

            # 1. Nosana — GPU frame analysis + second opinion
            yield emit("nosana", "running")
            nosana_job = await submit_processing_job(
                claim_id,
                claim.video_filename or "",
                video_path=claim.video_path or "",
            )
            claim.nosana_job = nosana_job
            db.commit()
            yield emit("nosana", "done", {
                "job_id": nosana_job.get("job_id"),
                "clip_verdict": nosana_job.get("clip_verdict", ""),
                "collision_signal_strength": nosana_job.get("collision_signal_strength", 0),
                "integrity_score": nosana_job.get("integrity_score", 0),
                "corroboration": nosana_job.get("corroboration", ""),
                "editing_artifacts_detected": nosana_job.get("editing_artifacts_detected", False),
                "summary": nosana_job.get("summary", ""),
            })

            # 2. VideoDB
            yield emit("videodb", "running")
            video_result = await analyze_video(claim.video_path or "", claim.video_filename or "")
            _require_final_video_evidence(video_result)
            claim.video_analysis = video_result.model_dump()
            db.commit()
            yield emit("videodb", "done", {
                "collision": video_result.collision,
                "severity": video_result.severity,
                "timestamp": video_result.timestamp,
                "summary": video_result.summary,
                "clip_url": video_result.clip_url,
                "frame_url": video_result.frame_url,
                "plate_detected": video_result.plate_detected,
                "audio_evidence": video_result.audio_evidence,
                "damage_description": video_result.damage_description,
                "camera_pov": video_result.camera_pov,
                "point_of_impact": video_result.point_of_impact,
            })

            # 3. Terminal 3
            yield emit("terminal3", "running")
            identity_result = await verify_identity(
                claimant_name=claim.claimant_name or "",
                claimant_id=claim.claimant_id_number or "",
            )
            claim.identity_result = identity_result.model_dump()
            db.commit()
            yield emit("terminal3", "done", {
                "verified": identity_result.verified,
                "identity_score": identity_result.identity_score,
                "source": identity_result.source,
            })

            # 4. MyInfo — government verification (triggered by video gaps)
            myinfo_result = None
            needs_myinfo = myinfo_needed(video_result.model_dump())
            if needs_myinfo or claim.nric:
                yield emit("myinfo", "running", {"triggered_by": video_result.fault})
                myinfo_result = await verify_myinfo(
                    nric=claim.nric or "",
                    claimant_name=claim.claimant_name or "",
                    video_analysis=video_result.model_dump(),
                )
                claim.myinfo_result = myinfo_result.model_dump()
                db.commit()
                yield emit("myinfo", "done", {
                    "verified": myinfo_result.verified,
                    "nric": myinfo_result.nric,
                    "full_name": myinfo_result.full_name,
                    "vehicle_plate": myinfo_result.vehicle_plate,
                    "vehicle_make": myinfo_result.vehicle_make,
                    "vehicle_model": myinfo_result.vehicle_model,
                    "licence_valid": myinfo_result.licence_valid,
                    "demerit_points": myinfo_result.demerit_points,
                    "licence_suspended": myinfo_result.licence_suspended,
                    "vehicle_ownership_confirmed": myinfo_result.vehicle_ownership_confirmed,
                    "myinfo_score": myinfo_result.myinfo_score,
                    "triggered_by": myinfo_result.triggered_by,
                })
            else:
                yield emit("myinfo", "skipped", {"reason": "video evidence sufficient, no NRIC provided"})

            # 4b. Plate cross-check — VideoDB detected plate vs registered plate
            plate_mismatch = False
            plate_mismatch_detail = {}
            detected_plate = (video_result.plate_detected or "").strip().upper().replace(" ", "")
            if detected_plate and detected_plate != "NOT_VISIBLE":
                expected_plate = ""
                # Priority: MyInfo registered plate → claim vehicle_plate → claimant_id_number
                if myinfo_result and myinfo_result.vehicle_plate:
                    expected_plate = myinfo_result.vehicle_plate.upper().replace(" ", "")
                elif claim.vehicle_plate:
                    expected_plate = claim.vehicle_plate.upper().replace(" ", "")
                elif claim.claimant_id_number:
                    id_val = claim.claimant_id_number.upper().replace(" ", "")
                    if any(c.isalpha() for c in id_val) and any(c.isdigit() for c in id_val):
                        expected_plate = id_val

                if expected_plate and detected_plate != expected_plate:
                    plate_mismatch = True
                    plate_mismatch_detail = {
                        "detected_plate": video_result.plate_detected,
                        "expected_plate": expected_plate,
                        "flag": "EXCL-04",
                    }
                    yield emit("videodb", "plate_mismatch", plate_mismatch_detail)
                    print(f"[Main] Plate mismatch: detected={detected_plate} expected={expected_plate}")

            # 5. Fraud check — cross-claim DB scan + plate mismatch injection
            fraud_result = check_fraud_signals(
                db=db,
                claim_id=claim_id,
                policy_number=claim.policy_number or "",
                video_analysis=video_result.model_dump(),
            )
            # Inject plate mismatch as EXCL-04 into fraud signals
            if plate_mismatch:
                fraud_result["fraud_flags"] = fraud_result.get("fraud_flags", []) + ["EXCL-04"]
                fraud_result["fraud_details"]["EXCL-04"] = (
                    f"Plate in footage ({plate_mismatch_detail['detected_plate']}) "
                    f"does not match registered plate ({plate_mismatch_detail['expected_plate']})"
                )
                fraud_result["fraud_detected"] = True

            if fraud_result.get("fraud_detected"):
                yield emit("daytona", "fraud_detected", {
                    "fraud_flags": fraud_result.get("fraud_flags", []),
                    "fraud_details": fraud_result.get("fraud_details", {}),
                })

            # 6. Kimi — with Nosana corroboration + fraud signals
            yield emit("kimi", "running")
            kimi_result = await evaluate_claim(
                video_result, identity_result, myinfo_result,
                nosana=nosana_job,
                fraud=fraud_result,
            )
            claim.kimi_result = kimi_result.model_dump()
            db.commit()
            yield emit("kimi", "done", {
                "decision": kimi_result.decision,
                "reason": kimi_result.reason,
                "confidence": kimi_result.confidence,
                "exclusions_triggered": kimi_result.exclusions_triggered,
                "soft_factors_applied": kimi_result.soft_factors_applied,
            })

            # 7. Daytona — ClaimAgent with fraud flags
            yield emit("daytona", "running")
            daytona_result = await run_claim_agent(
                video_analysis=video_result.model_dump(),
                identity_result=identity_result.model_dump(),
                kimi_result=kimi_result.model_dump(),
                myinfo_result=myinfo_result.model_dump() if myinfo_result else {},
                fraud_result=fraud_result,
            )
            yield emit("daytona", "done", {
                "hard_reject": daytona_result.get("hard_reject", False),
                "fraud_flags": daytona_result.get("fraud_flags", []),
            })

            # 6. Byzantium
            yield emit("byzantium", "running")
            trust_result = calculate_trust_score(video_result, identity_result, kimi_result, daytona_result)
            payout = calculate_payout(trust_result.decision, video_result.severity)

            claim.trust_score = trust_result.trust_score
            claim.risk_level = trust_result.risk_level
            claim.decision = trust_result.decision
            claim.reason = trust_result.reason
            claim.payout_amount = payout
            claim.status = "complete"
            claim.decided_at = datetime.utcnow()
            db.commit()

            yield emit("byzantium", "done", {
                "trust_score": trust_result.trust_score,
                "risk_level": trust_result.risk_level,
                "decision": trust_result.decision,
            })

            # Final complete event with full result
            yield emit("complete", "done", {
                "claim_id": claim_id,
                "video_analysis": video_result.model_dump(),
                "identity_result": identity_result.model_dump(),
                "myinfo_result": myinfo_result.model_dump() if myinfo_result else None,
                "nosana_analysis": nosana_job,
                "kimi_result": kimi_result.model_dump(),
                "trust_score_result": trust_result.model_dump(),
                "nosana_job_id": nosana_job.get("job_id"),
                "payout_amount": payout,
                "status": "complete",
            })

        except VideoEvidenceUnavailable:
            claim.status = "error"
            db.commit()
            yield emit("error", "failed", {"message": "Video evidence could not be verified. No final claim decision was generated."})
        except Exception as exc:
            claim.status = "error"
            db.commit()
            yield emit("error", "failed", {"message": str(exc)})
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# POST /calculate-trust
# ---------------------------------------------------------------------------


@app.post("/calculate-trust", response_model=TrustScoreResult)
async def calculate_trust_endpoint(
    video_analysis: VideoAnalysis,
    identity_result: IdentityResult,
    kimi_result: KimiResult,
):
    _require_private_claim_workflow()
    _require_final_video_evidence(video_analysis)
    daytona_result = await run_claim_agent(
        video_analysis=video_analysis.model_dump(),
        identity_result=identity_result.model_dump(),
    )
    return calculate_trust_score(video_analysis, identity_result, kimi_result, daytona_result)


# ---------------------------------------------------------------------------
# GET /decision/{claim_id}
# ---------------------------------------------------------------------------


@app.get("/decision/{claim_id}")
def get_decision(claim_id: str, db: Session = Depends(get_db)):
    _require_private_claim_workflow()
    claim = _get_claim(db, claim_id)
    if claim.status != "complete":
        raise HTTPException(status_code=202, detail=f"Claim status: {claim.status}")
    return {
        "claim_id": claim_id,
        "trust_score": claim.trust_score,
        "risk_level": claim.risk_level,
        "decision": claim.decision,
        "reason": claim.reason,
        "payout_amount": claim.payout_amount,
        "video_analysis": claim.video_analysis,
        "identity_result": claim.identity_result,
        "kimi_result": claim.kimi_result,
    }


# ---------------------------------------------------------------------------
# GET /receipt/{claim_id}
# ---------------------------------------------------------------------------


@app.get("/receipt/{claim_id}", response_model=ReceiptResponse)
def get_receipt(claim_id: str, db: Session = Depends(get_db)):
    _require_private_claim_workflow()
    claim = _get_claim(db, claim_id)
    if claim.status != "complete":
        raise HTTPException(status_code=404, detail="Receipt not available yet")

    video = claim.video_analysis or {}
    identity = claim.identity_result or {}

    return ReceiptResponse(
        claim_id=claim_id,
        claimant_name=claim.claimant_name or "Unknown",
        policy_number=claim.policy_number or "N/A",
        identity_status="VERIFIED" if identity.get("verified") else "UNVERIFIED",
        video_status="COLLISION CONFIRMED" if video.get("collision") else "NO COLLISION",
        trust_score=claim.trust_score or 0,
        risk_level=claim.risk_level or "HIGH",
        decision=claim.decision or "REJECT",
        reason=claim.reason or "",
        payout_amount=claim.payout_amount or 0.0,
        timestamp=(claim.decided_at or claim.created_at).isoformat(),
        receipt_number=f"RCP-{claim_id[-8:]}",
        frame_url=video.get("frame_url", ""),
        clip_url=video.get("clip_url", ""),
        plate_detected=video.get("plate_detected", "not_visible"),
    )


# ---------------------------------------------------------------------------
# GET /claims  — list all claims (dashboard)
# ---------------------------------------------------------------------------


@app.get("/claims")
def list_claims(db: Session = Depends(get_db)):
    if _is_public_demo():
        return []
    claims = db.query(ClaimRecord).order_by(ClaimRecord.created_at.desc()).limit(20).all()
    return [
        {
            "claim_id": c.claim_id,
            "claimant_name": c.claimant_name,
            "status": c.status,
            "decision": c.decision,
            "trust_score": c.trust_score,
            "created_at": c.created_at.isoformat(),
        }
        for c in claims
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_claim(db: Session, claim_id: str) -> ClaimRecord:
    claim = db.query(ClaimRecord).filter(ClaimRecord.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim
