"""Password hashing and JWT primitives."""

from __future__ import annotations

import uuid

import pytest

from app.core import security


def test_password_hash_roundtrip():
    hashed = security.hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert security.verify_password("correct horse battery staple", hashed)
    assert not security.verify_password("wrong", hashed)


def test_verify_handles_garbage_hash():
    assert security.verify_password("anything", "not-a-real-hash") is False


def test_access_token_roundtrip():
    uid, org = uuid.uuid4(), uuid.uuid4()
    token = security.create_access_token(subject=uid, org_id=org, system_role="owner")
    claims = security.decode_token(token, expected_type="access")
    assert claims["sub"] == str(uid)
    assert claims["org"] == str(org)
    assert claims["sysrole"] == "owner"
    assert claims["type"] == "access"


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
