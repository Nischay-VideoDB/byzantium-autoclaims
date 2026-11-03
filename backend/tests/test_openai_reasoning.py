import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services import kimi_service


def test_openai_reasoning_uses_direct_endpoint_and_records_real_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("OPEN_ROUTER_API_KEY", "obsolete-router-key")
    monkeypatch.setattr(kimi_service, "_build_user_prompt", lambda *args: "Synthetic evidence JSON")
    create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=
        '{"decision":"REVIEW","reason":"Needs review","confidence":0.7}'))]))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with patch("openai.AsyncOpenAI", return_value=client) as constructor:
        result = asyncio.run(kimi_service.evaluate_claim(None, None))
    constructor.assert_called_once_with(api_key="openai-test-key", base_url="https://api.openai.com/v1")
    assert create.call_args.kwargs["model"] == "gpt-4.1-mini"
    assert result.decision == "REVIEW"
    assert result.source == "openai-live"
