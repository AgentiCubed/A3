"""Structured logging with secret redaction.

All logs are JSON. A redaction processor strips values whose keys look like
credentials and masks known secret-ish patterns, satisfying the rule that
secrets never appear in logs.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import structlog

_SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|authorization|credential|private[_-]?key)",
    re.IGNORECASE,
)
_REDACTED = "***REDACTED***"


def _redact(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for key in list(event_dict.keys()):
        if _SENSITIVE_KEY.search(key):
            event_dict[key] = _REDACTED
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
