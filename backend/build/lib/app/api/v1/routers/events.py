"""Live project event stream (Server-Sent Events).

``GET /projects/{project_id}/events`` streams DomainEvents for one project as
``text/event-stream``. Reads require authentication and the project must belong
to the caller's organization — the same access rule as every other project read.

The stream is advisory: it is fed pre-commit and at-most-once, so consumers
treat it as a live hint and reconcile against the REST API (which reads the
database, the source of truth). Heartbeat comments are emitted so proxies and
clients can detect a dead connection.
"""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.orchestration.adapters.event_bus import get_event_bus
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["events"])

HEARTBEAT_SECONDS = 15.0


def format_sse(event_name: str, data: dict) -> str:
    """Render one SSE frame (event + JSON data)."""
    return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"


async def project_event_stream(organization_id: uuid.UUID, project_id: uuid.UUID):
    """Yield SSE frames for one project; heartbeat when the feed is quiet."""
    subscription = get_event_bus().subscribe(organization_id)
    try:
        yield ": connected\n\n"
        while True:
            try:
                event = await asyncio.wait_for(subscription.__anext__(), timeout=HEARTBEAT_SECONDS)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if event.project_id == project_id:
                yield format_sse(event.action, event.to_json_dict())
    finally:
        await subscription.close()


@router.get("/{project_id}/events")
async def stream_project_events(
    project_id: uuid.UUID, session: DbSession, user: CurrentUser
) -> StreamingResponse:
    """Stream live events (task transitions, approvals, remediations) for a project."""
    try:
        await project_service.get_project(session, user.organization_id, project_id)
    except project_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found") from exc
    return StreamingResponse(
        project_event_stream(user.organization_id, project_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
