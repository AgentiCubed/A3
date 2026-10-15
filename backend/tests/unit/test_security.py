"""Password hashing and JWT primitives."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import timedelta

import jwt
import pytest

from app.core import security
from app.core.config import get_settings


def test_password_hash_roundtrip():
    hashed = security.hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert security.verify_password("correct horse battery staple", hashed)
    assert not security.verify_password("wrong", hashed)


def test_verify_handles_garbage_hash():
    assert security.verify_password("anything", "not-a-real-hash") is False


@pytest.mark.parametrize("token_type", ["access", "refresh"])
def test_token_roundtrip(token_type):
    uid, org = uuid.uuid4(), uuid.uuid4()
    create_token = getattr(security, f"create_{token_type}_token")
    token = create_token(subject=uid, org_id=org, system_role="owner")
    claims = security.decode_token(token, expected_type=token_type)
    assert claims["sub"] == str(uid)
    assert claims["org"] == str(org)
    assert claims["sysrole"] == "owner"
    assert claims["type"] == token_type


def test_wrong_token_type_rejected():
    uid, org = uuid.uuid4(), uuid.uuid4()
    refresh = security.create_refresh_token(subject=uid, org_id=org, system_role="member")
    with pytest.raises(security.TokenError):
        security.decode_token(refresh, expected_type="access")


def test_tampered_token_rejected():
    uid, org = uuid.uuid4(), uuid.uuid4()
    token = security.create_access_token(subject=uid, org_id=org, system_role="member")
    with pytest.raises(security.TokenError):
        security.decode_token(token + "x", expected_type="access")


@pytest.mark.parametrize("token_type", ["access", "refresh"])
def test_expired_token_rejected(monkeypatch, token_type):
    past = security._now() - timedelta(days=365)
    monkeypatch.setattr(security, "_now", lambda: past)
    create_token = getattr(security, f"create_{token_type}_token")
    token = create_token(subject=uuid.uuid4(), org_id=uuid.uuid4(), system_role="member")
    with pytest.raises(security.TokenError):
        security.decode_token(token, expected_type=token_type)


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
def test_malformed_token_rejected(token):
    with pytest.raises(security.TokenError):
        security.decode_token(token, expected_type="access")


@pytest.mark.parametrize("algorithm", ["none", "HS384"])
def test_unexpected_algorithm_rejected(algorithm):
    key = "" if algorithm == "none" else get_settings().secret_key
    token = jwt.encode({"type": "access"}, key, algorithm=algorithm)
    with pytest.raises(security.TokenError):
        security.decode_token(token, expected_type="access")


def test_existing_hs256_token_compatible():
    # Build the previous issuer's JWT wire format independently of the new library.
    now = int(security._now().timestamp())
    claims = {
        "sub": str(uuid.uuid4()),
        "org": str(uuid.uuid4()),
        "sysrole": "member",
        "type": "access",
        "iat": now,
        "exp": now + 60,
        "jti": str(uuid.uuid4()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = b".".join(
        base64.urlsafe_b64encode(json.dumps(part, separators=(",", ":")).encode()).rstrip(b"=")
        for part in (header, claims)
    )
    signature = hmac.new(get_settings().secret_key.encode(), signing_input, hashlib.sha256).digest()
    token = (signing_input + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()
    assert security.decode_token(token, expected_type="access") == claims
