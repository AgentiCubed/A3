"""Authentication & registration service.

Owns the org+owner bootstrap, login, and token refresh. Writes audit events for
material identity changes. Raises domain errors that the API maps to HTTP codes.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.audit import record_audit
from app.core.roles import ActorType, SystemRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterRequest


class AuthError(Exception):
    """Base auth failure."""


class EmailAlreadyExists(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class AmbiguousLogin(AuthError):
    """Same email exists in multiple orgs; org context required (rare)."""


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "org"
    # Suffix with a short uuid fragment to guarantee global uniqueness.
    return f"{base}-{uuid.uuid4().hex[:8]}"


async def register_organization(session: AsyncSession, req: RegisterRequest) -> User:
    """Create a new organization with its first user as OWNER."""
    existing = await session.execute(select(User).where(User.email == req.email))
    if existing.scalars().first() is not None:
        # Email is unique per org; for MVP login-by-email we also keep it globally
        # unique to avoid ambiguous logins. (Recorded in docs/assumptions.md.)
        raise EmailAlreadyExists(req.email)

    org = Organization(name=req.organization_name, slug=_slugify(req.organization_name))
    session.add(org)
    await session.flush()  # assign org.id

    user = User(
        organization_id=org.id,
        email=req.email,
        hashed_password=security.hash_password(req.password),
        system_role=SystemRole.OWNER,
        is_active=True,
    )
    session.add(user)
    await session.flush()  # assign user.id

    await record_audit(
        session,
        organization_id=org.id,
        actor_type=ActorType.USER,
        actor_id=user.id,
        action="organization.register",
        entity_type="Organization",
        entity_id=org.id,
        after={"name": org.name, "slug": org.slug, "owner_email": user.email},
    )
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    """Verify credentials and return the active user."""
    result = await session.execute(select(User).where(User.email == email))
    users = result.scalars().all()
    if len(users) > 1:
        raise AmbiguousLogin(email)
    user = users[0] if users else None

    if user is None or not user.is_active:
        # Still run a hash verify against a dummy to reduce timing oracle.
        security.verify_password(password, security.hash_password("invalid"))
        raise InvalidCredentials()
    if not security.verify_password(password, user.hashed_password):
        raise InvalidCredentials()
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    """Return (access_token, refresh_token) for a user."""
    access = security.create_access_token(
        subject=user.id, org_id=user.organization_id, system_role=user.system_role.value
    )
    refresh = security.create_refresh_token(
        subject=user.id, org_id=user.organization_id, system_role=user.system_role.value
    )
    return access, refresh


async def user_from_refresh(session: AsyncSession, refresh_token: str) -> User:
    """Validate a refresh token and return the current user from the DB."""
    claims = security.decode_token(refresh_token, expected_type="refresh")
    user_id = uuid.UUID(claims["sub"])
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise InvalidCredentials()
    return user
