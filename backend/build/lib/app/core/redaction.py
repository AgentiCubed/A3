"""Recursive secret redaction for audit before/after payloads and logs.

A single source of truth for "what looks like a secret". Used by the audit sink
and available to logging so the two never drift.
"""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)
REDACTED = "***REDACTED***"


def redact(value: Any) -> Any:
    """Return a copy of ``value`` with secret-looking fields masked.

    Recurses through dicts and lists. Keys matching SENSITIVE_KEY have their
    values replaced wholesale (so even nested secret structures are masked).
    """
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and SENSITIVE_KEY.search(k):
                out[k] = REDACTED
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value
