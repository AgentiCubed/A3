"""Password hashing (argon2) and JWT issuance/verification.

Secrets policy: the signing key comes from Settings (env only). Tokens carry the
minimum claims; project roles are NOT trusted from the token and are resolved
per request from the database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

_ph = PasswordHasher()
_ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash, etc. — treat as auth failure, never raise out
        return False


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _create_token(
    *, subject: uuid.UUID, org_id: uuid.UUID, system_role: str, token_type: TokenType, ttl: int
) -> str:
    settings = get_settings()
    now = _now()
    claims: dict[str, Any] = {
        "sub": str(subject),
        "org": str(org_id),
        "sysrole": system_role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.secret_key, algorithm=_ALGORITHM)


def create_access_token(*, subject: uuid.UUID, org_id: uuid.UUID, system_role: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        org_id=org_id,
        system_role=system_role,
        token_type="access",  # noqa: S106 - token kind label, not a secret
        ttl=settings.access_token_ttl_seconds,
    )


def create_refresh_token(*, subject: uuid.UUID, org_id: uuid.UUID, system_role: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        org_id=org_id,
        system_role=system_role,
        token_type="refresh",  # noqa: S106 - token kind label, not a secret
        ttl=settings.refresh_token_ttl_seconds,
    )


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or the wrong type."""


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise TokenError(f"invalid token: {type(exc).__name__}") from exc
    if claims.get("type") != expected_type:
        raise TokenError("unexpected token type")
    return claims
