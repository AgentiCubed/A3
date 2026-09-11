"""Auth endpoints: register, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import enforce_auth_rate_limit
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, session: DbSession, request: Request) -> UserResponse:
    enforce_auth_rate_limit(request, "register")
    try:
        user = await auth_service.register_organization(session, req)
    except auth_service.RegistrationClosed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "registration is closed on this deployment",
        ) from exc
    except auth_service.EmailAlreadyExists as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from exc
    await session.commit()
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, session: DbSession, request: Request) -> TokenResponse:
    enforce_auth_rate_limit(request, "login")
    try:
        user = await auth_service.authenticate(session, req.email, req.password)
    except auth_service.AmbiguousLogin as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "ambiguous login; contact admin") from exc
    except auth_service.InvalidCredentials as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials") from exc
    access, refresh = auth_service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, session: DbSession, request: Request) -> TokenResponse:
    enforce_auth_rate_limit(request, "refresh")
    from app.core.security import TokenError

    try:
        user = await auth_service.user_from_refresh(session, req.refresh_token)
    except (TokenError, auth_service.InvalidCredentials) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token") from exc
    access, refresh_token = auth_service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
