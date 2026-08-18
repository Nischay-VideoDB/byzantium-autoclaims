# Byzantium AutoClaims

> AI-powered motor insurance claims — from dashcam to decision in seconds.

Byzantium AutoClaims is a multi-agent system that ingests dashcam footage, verifies the claimant's identity and vehicle against government records, cross-checks the insurance policy, detects fraud, and issues an autonomous APPROVE / REVIEW / REJECT decision with a payout figure — all streamed in real time.

---

## Demo Flow

1. Claimant enters their **name** and **vehicle plate** → policy is verified automatically via SenseNova
2. Uploads dashcam footage (MP4/MOV)
3. Seven-stage AI pipeline runs in parallel, streamed live to the UI
4. Decision page shows crash frame, trust score, Nosana GPU second opinion, SingPass identity
5. Liability receipt generated with full audit trail

---

## Pipeline Architecture

```
Upload
  │
  ├─ 1. Nosana GPU        — CLIP-based video analysis, collision signal strength, integrity score
  ├─ 2. VideoDB           — scene indexing, crash frame extraction, plate detection, audio evidence
  ├─ 3. Terminal 3        — TEE-attested identity verification (DID)
  ├─ 4. SingPass MyInfo   — government vehicle registration + driving licence check
  ├─ 4b. Plate Cross-check— VideoDB-detected plate vs MyInfo registered plate (EXCL-04 on mismatch)
  ├─ 5. Fraud Detection   — duplicate claims (30d / 24h), vehicle fingerprint (via Daytona)
  ├─ 6. Kimi AI           — policy-aware reasoning over all evidence (via TokenRouter)
  ├─ 7. Daytona           — sandboxed ClaimAgent execution, hard exclusion enforcement
  └─ 8. Byzantium Score   — trust score 0–1000 → APPROVE / REVIEW / REJECT + payout
```

---

## Sponsor Integrations

| Sponsor | Role |
|---|---|
| **VideoDB** | Dashcam video ingestion, shot-based scene indexing, crash frame thumbnail, spoken-word indexing |
| **Terminal 3** | TEE-based identity attestation; DID: `did:t3n:16d34b1887e89257702b597ef585298db72cad82` |
| **Kimi AI (k2)** | Multi-factor claims reasoning against policy terms and evidence |
| **TokenRouter** | Unified LLM routing with caching; fallback chain for Kimi → Anthropic |
| **Daytona** | Sandboxed Python execution of ClaimAgent; fraud cross-checks against claim DB |
| **Nosana** | Decentralised GPU compute; CLIP-equivalent video corroboration, integrity scoring |
| **SenseNova U1** | Multimodal policy document ingestion (.docx → structured coverage terms) |
| **SingPass MyInfo** | Government identity proxy: vehicle ownership, licence validity, demerit points |

---

## Policy Verification (No Manual Upload)

When a claimant enters their **name + vehicle plate**, the backend:
1. Scans `backend/policies/` for a matching `.docx` policy document
2. Extracts insured name, vehicle plate, NRIC, and policy number via `python-docx`
3. Returns a live verification banner — green if matched, red if mismatched
4. Blocks submission if the policy exists but the claimant details don't match

The bundled demo policy contains synthetic test data only:
- **Name:** Jane Smith · **NRIC:** S9812381D · **Plate:** SLD9775A · **Policy:** BYZ-2024-SLD9775A-001

---

## Trust Score

| Score | Decision | Risk |
|---|---|---|
| 700 – 1000 | APPROVE | LOW |
| 400 – 699 | REVIEW | MEDIUM |
| 0 – 399 | REJECT | HIGH |

Hard exclusions (EXCL-01 to EXCL-08) trigger instant REJECT regardless of score. Fraud flags (FRAUD-01/02/03) apply score penalties and force REVIEW or REJECT.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy · SQLite |
| Frontend | React 18 · Vite · TailwindCSS |
| Streaming | Server-Sent Events (SSE) |
| AI Models | `claude-sonnet-4-6` (default) · `kimi-k2` · `claude-haiku-4-5` |

---

## Project Structure

```
.
├── backend/
│   ├── main.py                     # FastAPI app — SSE pipeline, all endpoints
│   ├── models.py                   # Pydantic models
│   ├── database.py                 # SQLAlchemy ClaimRecord
│   ├── policies/                   # Policy .docx files (auto-loaded on startup)
│   │   └── JaneSmith_SLD9775A_Policy.docx
│   └── services/
│       ├── videodb_service.py      # Scene analysis, crash frame, plate extraction
│       ├── terminal3_service.py    # TEE identity verification
│       ├── myinfo_service.py       # SingPass proxy + sandbox API
│       ├── kimi_service.py         # LLM claims evaluation
│       ├── daytona_service.py      # Sandboxed ClaimAgent + fraud checks
│       ├── nosana_service.py       # GPU second opinion
│       ├── sensenova_service.py    # Policy document ingestion + auto-lookup
│       └── trustgrid_service.py    # Byzantium trust score engine
└── frontend/
    └── src/
        ├── pages/
        │   ├── Upload.jsx          # Claim form with live policy verification
        │   ├── Analysis.jsx        # Real-time SSE pipeline view
        │   ├── Decision.jsx        # Trust score, evidence cards, crash frame
        │   └── Receipt.jsx         # Liability receipt with audit trail
        └── api.js
```

---

## Running Locally

**Prerequisites:** Python 3.11+, Node 18+, Anaconda (or any venv)

**1. Backend**
```bash
cd backend
pip install -r requirements.txt
# Copy the root .env.example values into backend/.env and fill in API keys
uvicorn main:app --reload --port 8001
```

**2. Frontend**
```bash
cd frontend
npm install
# Create frontend/.env with:
# VITE_API_URL=http://localhost:8001
# VITE_LIVE_OPERATOR=true
npm run dev
```

Visit `http://localhost:5173`

---

## Synthetic Demo Credentials

| Field | Value |
|---|---|
| Full Name | Jane Smith |
| Vehicle Plate | SLD9775A |
| NRIC | S9812381D |
| Policy | BYZ-2024-SLD9775A-001 |

---

## Environment Variables

```bash
VITE_API_URL=http://localhost:8001
VITE_LIVE_OPERATOR=true     # local loopback only; public hosts always use prepared mode
DATABASE_URL=sqlite:///./byzantium_autoclaims.db
UPLOAD_DIR=uploads
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
VIDEODB_API_KEY=
TERMINAL3_API_KEY=
TERMINAL3_DID=
TOKENROUTER_API_KEY=
DAYTONA_API_KEY=
NOSANA_API_KEY=
SENSENOVA_API_KEY=          # SN-PLACEHOLDER-024 triggers proxy extraction
KIMI_API_KEY=               # optional — TokenRouter used as primary
```

## Deployment preparation

Deploy the Vite frontend and FastAPI backend as separate services unless the
Vercel Services private beta is available to the project. Set `VITE_API_URL` to
the API origin at frontend build time, and set the API's `CORS_ORIGINS` to the
frontend origin. The backend entrypoint for a Vercel FastAPI project is
`backend/app.py:app`.

Claims, uploaded dashcam files, and uploaded policy documents are durable
application data. Before a production deployment, provide a managed PostgreSQL
`DATABASE_URL` and durable object storage mounted or wired through `UPLOAD_DIR`;
the local SQLite file and local upload directory are suitable only for local
development. The current `claims` schema is defined by `backend/database.py` and
must be migrated before attaching a production database.

The public Vercel demo now keeps the prepared walkthroughs and also exposes a
fresh synthetic-only workflow. It accepts only the published Jane Smith / SLD9775A /
S9812381D persona, limits MP4/MOV/WebM uploads to 20 MB, stores footage in Vercel
Blob, persists idempotent claim state in a dedicated Azure PostgreSQL database,
and executes real VideoDB analysis plus OpenRouter policy reasoning. Missing
hackathon sponsors are shown as unavailable or local policy adapters, never as
live provider evidence. Every outcome and receipt is explicitly non-binding and
demonstration-only; this is not a consumer insurance service.

---

Built at the Agent Hackathon · June 2026
