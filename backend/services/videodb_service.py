import os
import re
import random
import logging
from models import VideoAnalysis

logger = logging.getLogger(__name__)


class VideoEvidenceUnavailable(RuntimeError):
    """Raised when verified VideoDB evidence is unavailable for a claim decision."""


def _synthetic_evidence_enabled() -> bool:
    """Allow mock output only for deliberately prepared local demonstrations."""
    return os.getenv("BYZANTIUM_ALLOW_SYNTHETIC_EVIDENCE", "").lower() in {"1", "true", "yes"}

# ── Mock fallbacks ─────────────────────────────────────────────────────────────

MOCK_ANALYSES = [
    VideoAnalysis(
        collision=True, severity="medium", timestamp="00:00:14",
        summary="[FIRST-PERSON dashcam] Rear-end collision. Camera car (claimant) stationary at red light, struck from behind at moderate speed. Other party at fault. Two vehicles. Daylight.",
        fault="other_party", vehicle_count=2, conditions="clear_daylight", single_vehicle=False,
        audio_evidence="Loud impact sound followed by horn. Driver audibly says 'he came out of nowhere'.",
        damage_description="Rear bumper crushed, boot deformed. Airbags not deployed.",
        camera_pov="first_person", point_of_impact="rear",
        source="videodb-mock"
    ),
    VideoAnalysis(
        collision=True, severity="high", timestamp="00:00:08",
        summary="[THIRD-PERSON dashcam] T-bone at intersection captured by external camera. Claimant's vehicle struck on driver side by vehicle running a red light. Multiple vehicles.",
        fault="other_party", vehicle_count=3, conditions="clear_daylight", single_vehicle=False,
        audio_evidence="Screeching brakes, heavy impact. Bystander shouts 'call an ambulance'.",
        damage_description="Driver-side door completely caved in on claimant's vehicle. Structural frame damage visible.",
        camera_pov="third_person", point_of_impact="driver_side",
        source="videodb-mock"
    ),
    VideoAnalysis(
        collision=True, severity="low", timestamp="00:00:19",
        summary="[FIRST-PERSON dashcam] Minor rear-end in slow traffic. Claimant stationary in queue, nudged from behind. Minimal damage. Night-time footage.",
        fault="other_party", vehicle_count=2, conditions="night_low_visibility", single_vehicle=False,
        audio_evidence="Light thud. Driver says 'seriously?'. No emergency sounds.",
        damage_description="Minor scratch on rear bumper. No structural damage visible.",
        camera_pov="first_person", point_of_impact="rear",
        source="videodb-mock"
    ),
    VideoAnalysis(
        collision=True, severity="medium", timestamp="00:00:11",
        summary="[FIRST-PERSON dashcam] Hit and run. Claimant struck from behind, offending vehicle fled immediately. Driver attempted to read partial plate aloud.",
        fault="unknown_hit_and_run", vehicle_count=1, conditions="clear_daylight", single_vehicle=False,
        audio_evidence="Impact sound, then acceleration of fleeing vehicle. Driver reads out partial plate.",
        damage_description="Rear damage consistent with moderate impact. Paint transfer visible.",
        camera_pov="first_person", point_of_impact="rear",
        source="videodb-mock"
    ),
]

# ── Structured scene prompt ────────────────────────────────────────────────────

STRUCTURED_SCENE_PROMPT = """
You are analyzing dashcam or CCTV footage submitted for a vehicle insurance claim.

IMPORTANT — Camera POV: The footage may be either:
  (A) FIRST-PERSON: dashcam is INSIDE the claimant's vehicle — camera car = claimant's car.
      Determine if claimant was struck (other party at fault) or caused the collision.
  (B) THIRD-PERSON: external camera (CCTV, another vehicle's dashcam) — claimant's car is
      VISIBLE in the frame. Identify which car is involved in the collision.

Identify the POV first, then assess accordingly.
Respond ONLY in this exact labeled format — one value per line, no extra text:

CAMERA_POV: first_person/third_person/unknown
COLLISION: yes/no
FAULT: claimant/other_party/unknown/unknown_hit_and_run
SEVERITY: none/low/medium/high
CONDITIONS: clear_daylight/night_low_visibility/adverse_weather/car_park
VEHICLES: (integer count visible in footage)
DAMAGE: (one sentence describing visible damage to claimant's vehicle, or 'none visible')
SPEED_AT_IMPACT: low/medium/high/unknown
CLAIMANT_STATIONARY: yes/no/unknown
POINT_OF_IMPACT: front/rear/driver_side/passenger_side/unknown
PLATE: (vehicle registration plate clearly readable in footage, e.g. SLD9775A — or 'not_visible')
SUMMARY: (one factual sentence — include which POV and which vehicle is the claimant's)
"""

AUDIO_SEARCH_TERMS = [
    "crash impact collision",
    "brakes screeching horn",
    "accident help emergency",
    "red light stop sign",
]


# ── Main entry point ───────────────────────────────────────────────────────────

async def analyze_video(video_path: str, filename: str = "") -> VideoAnalysis:
    api_key = (os.getenv("VIDEODB_API_KEY") or os.getenv("VIDEO_DB_API_KEY") or "").strip()
    if not api_key:
        if _synthetic_evidence_enabled():
            return random.choice(MOCK_ANALYSES)
        raise VideoEvidenceUnavailable("VideoDB is not configured for verified evidence.")

    try:
        import videodb
        from videodb import SceneExtractionType

        conn = videodb.connect(api_key=api_key)
        coll = conn.get_collection()

        print(f"[VideoDB] Uploading: {filename}")
        video = coll.upload(url=video_path) if video_path.startswith("https://") else coll.upload(file_path=video_path)
        print(f"[VideoDB] video_id={video.id}")

        # ── 1. Shot-based scene indexing with structured prompt ────────────────
        print("[VideoDB] Indexing scenes (shot-based, structured prompt)...")
        video.index_scenes(
            extraction_type=SceneExtractionType.shot_based,
            extraction_config={"threshold": 20, "frame_count": 3},
            prompt=STRUCTURED_SCENE_PROMPT,
        )

        # ── 2. Spoken word indexing for audio evidence ─────────────────────────
        audio_evidence = "No audio data available."
        try:
            print("[VideoDB] Indexing spoken words...")
            video.index_spoken_words()
            audio_evidence = await _extract_audio_evidence(video)
        except Exception as ae:
            print(f"[VideoDB] Audio indexing skipped: {ae}")

        # ── 3. Search for collision scenes ────────────────────────────────────
        print("[VideoDB] Searching for collision events...")
        results = video.search("vehicle collision crash accident impact")
        shots = getattr(results, "shots", []) or []
        collision = len(shots) > 0

        if not collision:
            return VideoAnalysis(
                collision=False, severity="none", timestamp="N/A",
                summary="No collision detected in dashcam footage.",
                fault="none", vehicle_count=1, conditions="clear_daylight",
                single_vehicle=True, audio_evidence=audio_evidence,
                damage_description="No damage visible.",
                source="videodb"
            )

        # ── 4. Parse structured output from shot descriptions ─────────────────
        raw_descriptions = [
            getattr(s, "description", None) or getattr(s, "text", None) or ""
            for s in shots[:5]
        ]
        combined_raw = "\n".join(raw_descriptions)
        fields = _parse_structured_output(combined_raw)

        ts_secs = int(getattr(shots[0], "start", 0) or 0)
        # Clamp to video duration awareness — avoid timestamps longer than the clip
        mins = ts_secs // 60
        secs = ts_secs % 60
        timestamp = f"00:{mins:02}:{secs:02}"

        # ── 5. Generate collision clip (±5 seconds around impact) ─────────────
        clip_url = ""
        try:
            clip_start = max(0, ts_secs - 3)
            clip_end = ts_secs + 8
            stream = video.generate_stream(timeline=[(clip_start, clip_end)])
            clip_url = str(stream) if stream else ""
            if clip_url:
                print(f"[VideoDB] Collision clip generated: {clip_url[:80]}...")
        except Exception as ce:
            print(f"[VideoDB] Clip generation skipped: {ce}")

        # ── 6. Extract crash frame thumbnail ──────────────────────────────────
        frame_url = ""
        try:
            # Try VideoDB's thumbnail method at exact impact timestamp
            thumbnail = video.generate_thumbnail(time=ts_secs)
            frame_url = str(thumbnail) if thumbnail else ""
            if frame_url:
                print(f"[VideoDB] Crash frame extracted @ {timestamp}")
        except Exception:
            try:
                # Fallback: 1-second clip at impact used as "frame"
                frame_stream = video.generate_stream(timeline=[(ts_secs, ts_secs + 1)])
                frame_url = str(frame_stream) if frame_stream else clip_url
            except Exception:
                frame_url = clip_url

        plate_detected = fields.get("PLATE", "not_visible").strip()
        if not plate_detected or plate_detected.lower() in ("", "n/a", "none"):
            plate_detected = "not_visible"

        return VideoAnalysis(
            collision=True,
            severity=fields.get("SEVERITY", "medium"),
            timestamp=timestamp,
            summary=fields.get("SUMMARY", combined_raw[:200]),
            fault=fields.get("FAULT", "unknown"),
            vehicle_count=int(fields.get("VEHICLES", "2")),
            conditions=fields.get("CONDITIONS", "clear_daylight"),
            single_vehicle=_is_single_vehicle(fields),
            audio_evidence=audio_evidence,
            damage_description=fields.get("DAMAGE", "Damage visible but unspecified."),
            clip_url=clip_url,
            frame_url=frame_url,
            plate_detected=plate_detected,
            camera_pov=fields.get("CAMERA_POV", "unknown"),
            point_of_impact=fields.get("POINT_OF_IMPACT", "unknown"),
            source="videodb"
        )

    except Exception as exc:
        logger.exception("VideoDB evidence analysis failed")
        if _synthetic_evidence_enabled():
            return random.choice(MOCK_ANALYSES)
        raise VideoEvidenceUnavailable("VideoDB evidence analysis failed.") from exc


# ── Audio evidence extraction ──────────────────────────────────────────────────

async def _extract_audio_evidence(video) -> str:
    findings = []
    for term in AUDIO_SEARCH_TERMS:
        try:
            results = video.search(term, index_type="spoken_word")
            shots = getattr(results, "shots", []) or []
            for shot in shots[:2]:
                text = getattr(shot, "text", None) or getattr(shot, "description", None) or ""
                if text and text not in findings:
                    findings.append(text.strip())
        except Exception:
            pass

    if not findings:
        return "No spoken audio evidence detected."
    return " | ".join(findings[:4])


# ── Structured output parser ───────────────────────────────────────────────────

def _parse_structured_output(raw: str) -> dict:
    """
    Parse labeled key: value lines from structured scene descriptions.
    Falls back to keyword scanning if the model didn't follow the format.
    """
    fields = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().upper()
            val = val.strip().lower()
            if key in {
                "COLLISION", "FAULT", "SEVERITY", "CONDITIONS",
                "VEHICLES", "DAMAGE", "SPEED_AT_IMPACT",
                "CLAIMANT_STATIONARY", "SUMMARY",
                "CAMERA_POV", "POINT_OF_IMPACT", "PLATE",
            }:
                fields[key] = val

    # Fill missing fields via keyword fallback
    combined = raw.lower()

    if "SEVERITY" not in fields:
        fields["SEVERITY"] = (
            "high" if any(w in combined for w in ["severe", "major", "high-speed", "significant"])
            else "medium" if any(w in combined for w in ["moderate", "rear-end", "t-bone", "side"])
            else "low"
        )

    if "FAULT" not in fields:
        fields["FAULT"] = (
            "claimant" if any(w in combined for w in ["claimant at fault", "claimant caused"])
            else "unknown_hit_and_run" if any(w in combined for w in ["hit and run", "fled"])
            else "other_party" if any(w in combined for w in ["other party", "struck from behind", "third party"])
            else "unknown"
        )

    if "CONDITIONS" not in fields:
        fields["CONDITIONS"] = (
            "night_low_visibility" if any(w in combined for w in ["night", "dark", "low visibility"])
            else "adverse_weather" if any(w in combined for w in ["rain", "ice", "snow", "fog"])
            else "car_park" if any(w in combined for w in ["car park", "parking"])
            else "clear_daylight"
        )

    if "VEHICLES" not in fields:
        fields["VEHICLES"] = (
            "3" if any(w in combined for w in ["three", "multiple vehicles", "pile"])
            else "1" if "single vehicle" in combined
            else "2"
        )

    if "DAMAGE" not in fields:
        fields["DAMAGE"] = "Damage consistent with reported collision."

    if "SUMMARY" not in fields:
        fields["SUMMARY"] = raw[:200].replace("\n", " ").strip()

    return fields


def _is_single_vehicle(fields: dict) -> bool:
    try:
        count = int(fields.get("VEHICLES", "2"))
    except ValueError:
        count = 2
    fault = fields.get("FAULT", "unknown")
    return count == 1 and fault not in ("other_party", "unknown_hit_and_run")
