"""Secret redaction used by the audit sink."""

from __future__ import annotations

from app.core.redaction import REDACTED, redact


def test_masks_top_level_secret_keys():
    out = redact({"api_key": "sk-123", "name": "ok"})
    assert out["api_key"] == REDACTED
    assert out["name"] == "ok"


def test_masks_nested_and_listed_secrets():
    out = redact(
        {
            "config": {"password": "hunter2", "host": "db"},
            "agents": [{"token": "abc", "id": 1}],
        }
    )
    assert out["config"]["password"] == REDACTED
    assert out["config"]["host"] == "db"
    assert out["agents"][0]["token"] == REDACTED
    assert out["agents"][0]["id"] == 1


def test_passthrough_non_secret():
    assert redact({"a": 1, "b": [1, 2, 3]}) == {"a": 1, "b": [1, 2, 3]}
