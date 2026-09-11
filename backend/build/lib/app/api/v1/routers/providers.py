"""Provider discovery and credential preflight endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.orchestration.adapters.registry import available_providers
from app.services.provider_preflight import preflight_provider

router = APIRouter(tags=["providers"])


class PreflightRequest(BaseModel):
    """Body for a non-destructive provider readiness check."""

    provider: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    # credential_ref is intentionally omitted from the public API: operators
    # use the adapter default (GEMINI_API_KEY / ANTHROPIC_API_KEY / …). Passing
    # arbitrary env-var names would expand the secret-resolution surface.


class PreflightResponse(BaseModel):
    provider: str
    ok: bool
    message: str
    category: str | None = None
    http_status: int | None = None
    diagnostic: str | None = None
    model: str | None = None


@router.get("/providers")
async def list_providers(_user: CurrentUser) -> dict[str, list[str]]:
    """Names selectable for new agents (retired providers excluded)."""
    return {"providers": available_providers()}


@router.post("/providers/preflight", response_model=PreflightResponse)
async def run_preflight(req: PreflightRequest, _user: CurrentUser) -> PreflightResponse:
    """Cheap provider ping: credential + trivial call, no project work.

    Authenticated callers only. Never echoes secrets or raw provider payloads.
    """
    result = await preflight_provider(req.provider, model=req.model)
    return PreflightResponse(**result.to_dict())
