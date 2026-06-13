# Agent Hackathon — Starter Scaffold

A minimal skeleton so you can start building immediately on hackathon day,
instead of setting up a project from scratch. Matches the structure of
`05-multi-agent-orchestrator.md` in the Templates folder.

## Folder structure

```
.
├── CLAUDE.md           # project context for Claude (stack, decisions, constraints)
├── .env                # sponsor API keys (fill in, never commit)
├── backend/
│   ├── main.py         # FastAPI app entry point (placeholder /health route)
│   ├── requirements.txt
│   └── agents/
│       └── coordinator.py   # placeholder for the coordinator agent
└── frontend/
    ├── package.json    # React + Vite + Tailwind deps (not yet installed)
    ├── vite.config.js  # proxies /api -> backend on :8000
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx      # placeholder UI (input + run button)
        └── index.css
```

## What's here vs. what's not

This is a **minimal skeleton**: files exist but dependencies are NOT
installed yet, and no real agent logic is implemented. That's intentional —
pick a project idea first, then fill in the placeholders.

## Setup commands (run these once you pick a direction)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` — you should see a placeholder input box and
"Run" button. The backend health check is at `http://localhost:8000/health`.

## Before you start building

1. Fill in `.env` with the keys you've claimed (Anthropic + 2-3 sponsor tools)
2. Update `CLAUDE.md` with your chosen theme/idea and architecture
3. Pick a template from `../Templates/` closest to your idea
4. Wire `frontend/src/App.jsx`'s `run()` function to call `backend/main.py`'s
   `/orchestrate` route (once you build it)

## Next steps

See `hackathon-day-guide.md` in the Templates folder for the hour-by-hour plan.
