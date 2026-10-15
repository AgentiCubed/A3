"""Artifact schema."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_execution_id: uuid.UUID | None
    name: str
    content_type: str
    storage_key: str
    size_bytes: int
    sha256: str
    produced_by_agent_id: uuid.UUID | None

    model_config = {"from_attributes": True}
