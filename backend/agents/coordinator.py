"""
Coordinator agent — placeholder.

See Templates/05-multi-agent-orchestrator.md for the full reference
implementation (plan_subtasks / synthesize_results tool pattern,
async specialist runners, WebSocket progress updates).

Fill this in once you've picked a project idea:
1. Define COORDINATOR_SYSTEM prompt
2. Define coordinator_tools (plan_subtasks, synthesize_results)
3. Implement run_orchestrator()
4. Wire up a router and include it in main.py
"""

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-6"

COORDINATOR_SYSTEM = """You are a task coordinator. (fill in once project is scoped)"""
