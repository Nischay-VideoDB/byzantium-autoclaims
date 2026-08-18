import asyncio

from services.myinfo_service import verify_myinfo


def test_public_myinfo_fixture_is_explicitly_synthetic(monkeypatch):
    monkeypatch.delenv("MYINFO_CLIENT_ID", raising=False)
    result = asyncio.run(verify_myinfo(
        "S9812381D",
        "Jane Smith",
        {"fault": "unknown", "collision": False},
    ))

    assert result.verified is True
    assert result.source == "published-synthetic-myinfo-adapter"
    assert result.provider_available is False
    assert result.synthetic is True
    assert result.raw == {
        "published_synthetic_fixture": True,
        "fixture_id": "jane-smith-demo",
    }
