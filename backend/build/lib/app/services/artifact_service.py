"""Artifact persistence: write bytes via the ArtifactStore, index a row in the DB."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.artifacts import LocalArtifactStore
from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.roles import ActorType
from app.models.artifact import Artifact
from app.services import acceptance_boundary_service


def default_store() -> LocalArtifactStore:
    return LocalArtifactStore(get_settings().artifact_store_path)


async def store_artifact(
    session: AsyncSession,
    store: LocalArtifactStore,
    *,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    name: str,
    content_type: str,
    data: bytes,
    task_execution_id: uuid.UUID | None = None,
    produced_by_agent_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.SYSTEM,
) -> Artifact:
    # Claim the project's acceptance boundary before touching external storage.
    # A close that won the same boundary therefore leaves neither a database row
    # nor orphaned bytes from a late artifact attempt.
    await acceptance_boundary_service.claim_acceptance_write(
        session,
        project_id=project_id,
        org_id=org_id,
    )
    key = f"{project_id}/{uuid.uuid4().hex}-{name}"
    stored = store.put(key, data, content_type)
    artifact = Artifact(
        organization_id=org_id,
        project_id=project_id,
        task_execution_id=task_execution_id,
        name=name,
        content_type=content_type,
        storage_key=stored.storage_key,
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
        produced_by_agent_id=produced_by_agent_id,
    )
    session.add(artifact)
    await session.flush()
    await record_audit(
        session,
        organization_id=org_id,
        project_id=project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="artifact.created",
        entity_type="Artifact",
        entity_id=artifact.id,
        after={"name": name, "content_type": content_type, "size_bytes": stored.size_bytes},
    )
    return artifact


async def list_artifacts(
    session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID
) -> list[Artifact]:
    stmt = select(Artifact).where(
        Artifact.organization_id == org_id, Artifact.project_id == project_id
    )
    return list((await session.execute(stmt)).scalars().all())
