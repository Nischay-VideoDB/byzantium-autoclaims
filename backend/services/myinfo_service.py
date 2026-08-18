"""
MyInfo adapter boundary for the synthetic public demo persona.

Real flow (production):
  1. User authenticates via SingPass OAuth
  2. connector.getMyInfoPersonData(authCode, state, txnNo)
  3. Returns decrypted, signature-validated person data

Public deployment:
  - NRIC maps only to a published synthetic fixture
  - No government system is queried unless an operator separately configures it
  - The result contract always exposes provider availability and synthetic provenance
"""

import os
import httpx
from models import MyInfoResult

# ---------------------------------------------------------------------------
# Published synthetic records. These are fixtures, not government data.
# ---------------------------------------------------------------------------

PROXY_RECORDS = {
    # Jane Smith — Toyota Vios SLD9775A, valid licence, 0 demerit points
    "S9812381D": {
        "uinfin":       {"value": "S9812381D"},
        "name":         {"value": "SMITH, JANE"},
        "dob":          {"value": "1990-07-22"},
        "sex":          {"value": "F"},
        "nationality":  {"value": "SINGAPORE CITIZEN"},
        "vehicles": [{
            "vehicleno":          {"value": "SLD9775A"},
            "type":               {"value": "MOTOR CAR"},
            "make":               {"value": "TOYOTA"},
            "model":              {"value": "VIOS"},
            "yearofmanufacture":  {"value": "2021"},
            "effectiveownership": {"value": "2022-01-10"},
        }],
        "drivinglicence": {
            "qdl": {
                "validity":   {"value": "VALID"},
                "expirydate": {"value": "2029-06-06"},
                "classes":    [{"class": {"value": "3"}}],
            },
            "totaldemeritpoints": {"value": 0},
            "suspension":         {"startdate": {"value": ""}, "enddate": {"value": ""}},
            "disqualification":   {"startdate": {"value": ""}, "enddate": {"value": ""}},
        },
    },

    # High demerit points — Honda Civic, 14 demerit points (near suspension)
    "S6005041F": {
        "uinfin":       {"value": "S6005041F"},
        "name":         {"value": "LIM KAH SENG"},
        "dob":          {"value": "1985-03-22"},
        "sex":          {"value": "M"},
        "nationality":  {"value": "SINGAPORE CITIZEN"},
        "vehicles": [{
            "vehicleno":          {"value": "SKX5512J"},
            "type":               {"value": "MOTOR CAR"},
            "make":               {"value": "HONDA"},
            "model":              {"value": "CIVIC"},
            "yearofmanufacture":  {"value": "2016"},
            "effectiveownership": {"value": "2018-07-20"},
        }],
        "drivinglicence": {
            "qdl": {
                "validity":   {"value": "VALID"},
                "expirydate": {"value": "2027-03-22"},
                "classes":    [{"class": {"value": "3"}}, {"class": {"value": "3A"}}],
            },
            "totaldemeritpoints": {"value": 14},
            "suspension":         {"startdate": {"value": ""}, "enddate": {"value": ""}},
            "disqualification":   {"startdate": {"value": ""}, "enddate": {"value": ""}},
        },
    },

    # Suspended licence — Toyota Camry
    "T0123456G": {
        "uinfin":       {"value": "T0123456G"},
        "name":         {"value": "RAHUL SHARMA"},
        "dob":          {"value": "1990-11-15"},
        "sex":          {"value": "M"},
        "nationality":  {"value": "EMPLOYMENT PASS"},
        "vehicles": [{
            "vehicleno":          {"value": "SMR4421K"},
            "type":               {"value": "MOTOR CAR"},
            "make":               {"value": "TOYOTA"},
            "model":              {"value": "CAMRY"},
            "yearofmanufacture":  {"value": "2018"},
            "effectiveownership": {"value": "2021-01-10"},
        }],
        "drivinglicence": {
            "qdl": {
                "validity":   {"value": "SUSPENDED"},
                "expirydate": {"value": "2026-11-15"},
                "classes":    [{"class": {"value": "3"}}],
            },
            "totaldemeritpoints": {"value": 24},
            "suspension":         {"startdate": {"value": "2025-09-01"}, "enddate": {"value": "2026-03-01"}},
            "disqualification":   {"startdate": {"value": ""}, "enddate": {"value": ""}},
        },
    },

    # Multiple vehicles — Nissan, valid but 8 demerit points
    "G2957839M": {
        "uinfin":       {"value": "G2957839M"},
        "name":         {"value": "PRIYA NAIR"},
        "dob":          {"value": "1993-08-30"},
        "sex":          {"value": "F"},
        "nationality":  {"value": "PERMANENT RESIDENT"},
        "vehicles": [
            {
                "vehicleno":          {"value": "SGX8888X"},
                "type":               {"value": "MOTOR CAR"},
                "make":               {"value": "NISSAN"},
                "model":              {"value": "SUNNY"},
                "yearofmanufacture":  {"value": "2017"},
                "effectiveownership": {"value": "2019-05-05"},
            },
            {
                "vehicleno":          {"value": "SCB2201Z"},
                "type":               {"value": "MOTOR CYCLE"},
                "make":               {"value": "HONDA"},
                "model":              {"value": "CB400"},
                "yearofmanufacture":  {"value": "2015"},
                "effectiveownership": {"value": "2020-08-12"},
            },
        ],
        "drivinglicence": {
            "qdl": {
                "validity":   {"value": "VALID"},
                "expirydate": {"value": "2028-08-30"},
                "classes":    [{"class": {"value": "2"}}, {"class": {"value": "3"}}],
            },
            "totaldemeritpoints": {"value": 8},
            "suspension":         {"startdate": {"value": ""}, "enddate": {"value": ""}},
            "disqualification":   {"startdate": {"value": ""}, "enddate": {"value": ""}},
        },
    },
}

# Default fallback record for any unknown NRIC
DEFAULT_RECORD_TEMPLATE = {
    "name":         {"value": "{name}"},
    "dob":          {"value": "1990-01-01"},
    "sex":          {"value": "M"},
    "nationality":  {"value": "SINGAPORE CITIZEN"},
    "vehicles": [{
        "vehicleno":          {"value": "SXX0000X"},
        "type":               {"value": "MOTOR CAR"},
        "make":               {"value": "UNKNOWN"},
        "model":              {"value": "UNKNOWN"},
        "yearofmanufacture":  {"value": "2020"},
        "effectiveownership": {"value": "2021-01-01"},
    }],
    "drivinglicence": {
        "qdl": {
            "validity":   {"value": "VALID"},
            "expirydate": {"value": "2030-01-01"},
            "classes":    [{"class": {"value": "3"}}],
        },
        "totaldemeritpoints": {"value": 0},
        "suspension":         {"startdate": {"value": ""}, "enddate": {"value": ""}},
        "disqualification":   {"startdate": {"value": ""}, "enddate": {"value": ""}},
    },
}


def _should_trigger(video_analysis: dict) -> bool:
    """Determine if MyInfo verification is needed based on video gaps."""
    fault = video_analysis.get("fault", "unknown")
    conditions = video_analysis.get("conditions", "")
    return (
        fault in ("unknown", "unknown_hit_and_run")
        or conditions == "night_low_visibility"
        or not video_analysis.get("collision")
    )


async def verify_myinfo(
    nric: str,
    claimant_name: str,
    video_analysis: dict,
) -> "MyInfoResult":
    """
    Resolve the published synthetic profile adapter. If an operator has
    configured a supported sandbox client, that result is labeled separately.
    """
    nric = (nric or "").strip().upper()
    if not nric:
        return MyInfoResult(
            verified=False,
            nric="",
            full_name="",
            vehicle_plate="",
            vehicle_make="",
            vehicle_model="",
            licence_valid=False,
            licence_class="",
            demerit_points=0,
            licence_suspended=False,
            vehicle_ownership_confirmed=False,
            myinfo_score=0,
            source="myinfo-skipped",
            provider_available=bool(os.getenv("MYINFO_CLIENT_ID", "").strip()),
            synthetic=False,
            triggered_by=_trigger_reason(video_analysis),
            raw={},
        )

    # Try real sandbox API
    sandbox_key = os.getenv("MYINFO_CLIENT_ID", "").strip()
    if sandbox_key:
        try:
            result = await _call_sandbox(nric, sandbox_key)
            if result:
                return result
        except Exception as exc:
            print(f"[MyInfo] Sandbox API error: {exc} — using the published synthetic fixture")

    # Proxy record lookup
    return _parse_record(nric, claimant_name, video_analysis)


async def _call_sandbox(nric: str, client_id: str) -> "MyInfoResult | None":
    """Attempt real SingPass MyInfo sandbox API."""
    sandbox_url = os.getenv(
        "MYINFO_SANDBOX_URL",
        "https://sandbox.api.myinfo.gov.sg/com/v3/person-sample"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{sandbox_url}/{nric}",
                headers={"x-api-key": client_id},
                params={"attributes": "name,vehicles,drivinglicence,dob,nationality"},
            )
            if resp.status_code == 200:
                raw = resp.json()
                return _build_result_from_raw(nric, raw, source="myinfo-sandbox")
    except Exception as exc:
        print(f"[MyInfo] HTTP error: {exc}")
    return None


def _parse_record(nric: str, claimant_name: str, video_analysis: dict) -> "MyInfoResult":
    raw = PROXY_RECORDS.get(nric)

    if not raw:
        # Generate a plausible record for unknown NRICs
        import copy
        raw = copy.deepcopy(DEFAULT_RECORD_TEMPLATE)
        raw["uinfin"] = {"value": nric}
        raw["name"]["value"] = claimant_name or "UNKNOWN"
        print(f"[MyInfo] Unknown NRIC {nric} — using a generated synthetic fixture")
    else:
        print(f"[MyInfo] Published synthetic fixture found for {nric}")

    return _build_result_from_raw(
        nric, raw, source="published-synthetic-myinfo-adapter",
        video_analysis=video_analysis,
    )


def _build_result_from_raw(nric: str, raw: dict, source: str, video_analysis: dict = None) -> "MyInfoResult":
    video_analysis = video_analysis or {}

    name = raw.get("name", {}).get("value", "")
    vehicles = raw.get("vehicles", [])
    dl = raw.get("drivinglicence", {})
    qdl = dl.get("qdl", {})

    # Primary vehicle
    primary_vehicle = vehicles[0] if vehicles else {}
    plate = primary_vehicle.get("vehicleno", {}).get("value", "")
    make  = primary_vehicle.get("make", {}).get("value", "")
    model = primary_vehicle.get("model", {}).get("value", "")

    licence_validity = qdl.get("validity", {}).get("value", "UNKNOWN")
    licence_valid    = licence_validity == "VALID"
    licence_class    = ", ".join(
        c.get("class", {}).get("value", "") for c in qdl.get("classes", [])
    )
    demerit_points = int(dl.get("totaldemeritpoints", {}).get("value", 0) or 0)
    suspension_start = dl.get("suspension", {}).get("startdate", {}).get("value", "")
    licence_suspended = bool(suspension_start)

    # Cross-check: does video description mention the registered plate?
    video_summary = (video_analysis.get("summary", "") + " " + video_analysis.get("damage_description", "")).upper()
    vehicle_ownership_confirmed = plate.upper() in video_summary if plate else False

    # MyInfo score (0-100)
    myinfo_score = 100
    if not licence_valid:      myinfo_score -= 40
    if licence_suspended:      myinfo_score -= 40
    if demerit_points >= 12:   myinfo_score -= 20
    elif demerit_points >= 6:  myinfo_score -= 10
    if not vehicles:           myinfo_score -= 20
    myinfo_score = max(0, myinfo_score)

    synthetic = source == "published-synthetic-myinfo-adapter"
    return MyInfoResult(
        verified=bool(name),
        nric=nric,
        full_name=name,
        vehicle_plate=plate,
        vehicle_make=make,
        vehicle_model=model,
        licence_valid=licence_valid,
        licence_class=licence_class,
        demerit_points=demerit_points,
        licence_suspended=licence_suspended,
        vehicle_ownership_confirmed=vehicle_ownership_confirmed,
        myinfo_score=myinfo_score,
        source=source,
        provider_available=not synthetic,
        synthetic=synthetic,
        triggered_by=_trigger_reason(video_analysis),
        raw=(
            {"published_synthetic_fixture": True, "fixture_id": "jane-smith-demo"}
            if synthetic else raw
        ),
    )


def _trigger_reason(video_analysis: dict) -> str:
    fault = video_analysis.get("fault", "unknown")
    conditions = video_analysis.get("conditions", "")
    if fault == "unknown_hit_and_run":
        return "hit_and_run_no_plate"
    if conditions == "night_low_visibility":
        return "poor_visibility_plate_unreadable"
    if fault == "unknown":
        return "fault_undetermined"
    return "manual_verification_requested"
