"""Vercel-compatible FastAPI entrypoint.

The primary application remains in ``main.py`` for local ``uvicorn main:app``
development. Vercel detects this conventional ``app`` export when the backend
directory is configured as the project root.
"""

from main import app

