# Project Context

## Hackathon Theme
[Fill in once the brief is announced]

## Stack
- Backend: Python + FastAPI (see `backend/`)
- Frontend: React + Vite + TailwindCSS (see `frontend/`)
- AI Model: claude-sonnet-4-6 (default), claude-haiku-4-5 for cheap/high-volume calls
- Multi-agent pattern: Coordinator + specialist agents (researcher / analyst / writer / coder)

## Sponsor Tools (from .env — fill in keys before use)
- Kimi AI (kimi-k2.6) — agent swarm execution
- TokenRouter — unified LLM routing + caching
- Bright Data — web scraping / browsing
- Daytona — sandboxed code execution
- Nosana — decentralized GPU compute
- SenseNova U1 — multimodal (Excel/PPT/research)
- Terminal 3 — verifiable agent identity
- VideoDB — video data infra

## Architecture
[Fill in once a project idea is chosen — see Templates folder for 5 reference architectures]

## Patterns
- Prompt caching enabled on system prompts (`cache_control: ephemeral`)
- Streaming for user-facing responses
- Tool use for agent actions

## Constraints
- 8-hour build window (see hackathon-day-guide.md in Templates)
- Must integrate at least 2-3 sponsor tools (don't try all 8)

## Decision Log
- [Date] — [Decision] — [Why]

## Team
- [Names / roles]
