"""EventBus port, in-memory adapter, audit-sink publication, and SSE framing."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

import pytest

from app.api.v1.routers.events import format_sse, project_event_stream
from app.core.audit import record_audit
from app.core.roles import ActorType
from app.orchestration.adapters.event_bus import (
    InMemoryEventBus,
    get_event_bus,
    reset_event_bus,
)
from app.orchestration.ports import DomainEvent


def _event(org: uuid.UUID, project: uuid.UUID | None = None, action="task.transition"):
    return DomainEvent(
        organization_id=org,
        project_id=project,
        action=action,
        entity_type="Task",
        entity_id=uuid.uuid4(),
        actor_type="system",
        occurred_at=datetime.now(UTC),
        payload={"status": "running"},
    )


async def test_publish_reaches_subscriber():
    bus = InMemoryEventBus()
    org = uuid.uuid4()
    sub = bus.subscribe(org)
    event = _event(org)
    await bus.publish(event)
    received = await asyncio.wait_for(sub.__anext__(), timeout=1)
    assert received is event
    await sub.close()


async def test_org_isolation():
    bus = InMemoryEventBus()
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    sub_b = bus.subscribe(org_b)
    await bus.publish(_event(org_a))
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(sub_b.__anext__(), timeout=0.05)
    await sub_b.close()


async def test_multiple_subscribers_all_receive():
    bus = InMemoryEventBus()
    org = uuid.uuid4()
    subs = [bus.subscribe(org) for _ in range(3)]
    await bus.publish(_event(org))
    for sub in subs:
        assert (await asyncio.wait_for(sub.__anext__(), timeout=1)).action == "task.transition"
        await sub.close()


async def test_closed_subscription_stops_receiving():
    bus = InMemoryEventBus()
    org = uuid.uuid4()
    sub = bus.subscribe(org)
    await sub.close()
    await bus.publish(_event(org))  # must not raise
    with pytest.raises(StopAsyncIteration):
        await sub.__anext__()


def test_domain_event_json_round_trip():
    event = _event(uuid.uuid4(), project=uuid.uuid4())
    raw = event.to_json_dict()
    assert raw["action"] == "task.transition"
    assert raw["project_id"] == str(event.project_id)
    assert raw["payload"] == {"status": "running"}
    json.dumps(raw)  # must be JSON-serializable as-is


async def test_record_audit_publishes_redacted_event(session):
    """The audit sink publishes a DomainEvent carrying the redacted after-image."""
    reset_event_bus()
    org, project = uuid.uuid4(), uuid.uuid4()
    sub = get_event_bus().subscribe(org)
    await record_audit(
        session,
        organization_id=org,
        project_id=project,
        actor_type=ActorType.SYSTEM,
        action="task.transition",
        entity_type="Task",
        entity_id=uuid.uuid4(),
        after={"status": "running", "api_key": "super-secret"},
    )
    event = await asyncio.wait_for(sub.__anext__(), timeout=1)
    assert event.project_id == project
    assert event.payload["status"] == "running"
    assert event.payload["api_key"] != "super-secret"  # redaction applied
    await sub.close()
    reset_event_bus()


def test_format_sse_frame():
    frame = format_sse("task.transition", {"a": 1})
    assert frame == 'event: task.transition\ndata: {"a": 1}\n\n'


async def test_project_event_stream_filters_by_project():
    reset_event_bus()
    org, project, other = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    stream = project_event_stream(org, project)
    assert (await stream.__anext__()).startswith(": connected")

    await get_event_bus().publish(_event(org, project=other))  # filtered out
    await get_event_bus().publish(_event(org, project=project, action="task.escalated"))

    frame = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert frame.startswith("event: task.escalated\n")
    assert json.loads(frame.split("data: ", 1)[1].strip())["project_id"] == str(project)
    await stream.aclose()
    reset_event_bus()
