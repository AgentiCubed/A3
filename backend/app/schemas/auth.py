"""Auth request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.core.roles import SystemRole


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)
    # Required when the deployment sets REGISTRATION_INVITE_CODE; ignored
    # otherwise. Comparison happens in the service, constant-time.
    invite_code: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth scheme label, not a secret


class UserResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    system_role: SystemRole
    is_active: bool

    model_config = {"from_attributes": True}
