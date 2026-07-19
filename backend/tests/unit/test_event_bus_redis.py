"""EventBus adapters: the Redis transport, JSON (de)serialization, the
drop-oldest back-pressure policy, and settings-driven bus selection.

The in-memory happy path lives in ``test_event_bus.py``; this file covers the
Redis pub/sub path (with a fake client), ``_event_from_json`` round-tripping,
the slow-consumer drop-oldest behavior, and ``get_event_bus`` backend routing.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

from app.orchestration.adapters import event_bus
from app.orchestration.adapters.event_bus import (
    InMemoryEventBus,
    RedisEventBus,
    _event_from_json,
    get_event_bus,
    reset_event_bus,
)
from app.orchestration.ports import DomainEvent


def _event(org, project=None, action="task.transition") -> DomainEvent:
    return DomainEvent(
        organization_id=org,
        project_id=project,
        action=action,
        entity_type="Task",
        entity_id=uuid.uuid4(),
        actor_type="system",
        actor_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        payload={"status": "running"},
    )


def test_event_from_json_round_trip():
    ev = _event(uuid.uuid4(), project=uuid.uuid4())
    restored = _event_from_json(ev.to_json_dict())

    assert restored.organization_id == ev.organization_id
    assert restored.project_id == ev.project_id
    assert restored.entity_id == ev.entity_id
    assert restored.actor_id == ev.actor_id
    assert restored.actor_type == ev.actor_type
    assert restored.action == ev.action
    assert restored.entity_type == ev.entity_type
    assert restored.occurred_at == ev.occurred_at
    assert restored.payload == {"status": "running"}


def test_event_from_json_handles_null_optionals():
    org = uuid.uuid4()
    raw = {
        "organization_id": str(org),
        "project_id": None,
        "action": "a",
        "entity_type": "Task",
        "entity_id": None,
        "actor_type": None,
        "actor_id": None,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": None,
    }
    ev = _event_from_json(raw)
    assert ev.project_id is None
    assert ev.entity_id is None
    assert ev.actor_id is None
    assert ev.payload == {}


async def test_inmemory_drops_oldest_when_subscriber_queue_full(monkeypatch):
    # A small buffer makes the drop-oldest policy observable: the earliest event
    # is evicted so a slow reader can never block the publisher.
    monkeypatch.setattr(event_bus, "_QUEUE_MAX", 2)
    bus = InMemoryEventBus()
    org = uuid.uuid4()
    sub = bus.subscribe(org)

    await bus.publish(_event(org, action="a"))  # evicted
    await bus.publish(_event(org, action="b"))
    await bus.publish(_event(org, action="c"))

    first = await asyncio.wait_for(sub.__anext__(), timeout=1)
    second = await asyncio.wait_for(sub.__anext__(), timeout=1)
    assert [first.action, second.action] == ["b", "c"]
    await sub.close()


def test_redis_channel_is_per_organization():
    org = uuid.uuid4()
    assert RedisEventBus._channel(org) == f"events:{org}"


def test_redis_get_client_is_lazy_and_cached():
    bus = RedisEventBus("redis://localhost:6379/0")
    client_a = bus._get_client()
    client_b = bus._get_client()
    assert client_a is client_b  # constructed once, reused


async def test_redis_publish_writes_json_to_org_channel(monkeypatch):
    class _FakeRedis:
        def __init__(self):
            self.published: list[tuple[str, str]] = []

        async def publish(self, channel, data):
            self.published.append((channel, data))

    fake = _FakeRedis()
    bus = RedisEventBus("redis://x")
    monkeypatch.setattr(bus, "_get_client", lambda: fake)

    org = uuid.uuid4()
    await bus.publish(_event(org, action="task.escalated"))

    assert len(fake.published) == 1
    channel, data = fake.published[0]
    assert channel == f"events:{org}"
    assert json.loads(data)["action"] == "task.escalated"


async def test_redis_subscription_iterates_message_events():
    org = uuid.uuid4()
    ev = _event(org, action="task.escalated")

    class _FakePubSub:
        def __init__(self, messages):
            self._messages = list(messages)
            self.subscribed: list[str] = []
            self.unsubscribed: list[str] = []
            self.closed = False

        async def subscribe(self, channel):
            self.subscribed.append(channel)

        async def unsubscribe(self, channel):
            self.unsubscribed.append(channel)

        async def aclose(self):
            self.closed = True

        async def get_message(self, ignore_subscribe_messages, timeout):
            return self._messages.pop(0) if self._messages else None

    class _FakeClient:
        def __init__(self, pubsub):
            self._pubsub = pubsub

        def pubsub(self):
            return self._pubsub

    pubsub = _FakePubSub(
        [
            None,  # transient miss — the loop keeps polling
            {"type": "subscribe"},  # control frame — ignored
            {"type": "message", "data": json.dumps(ev.to_json_dict())},
        ]
    )
    bus = RedisEventBus("redis://x")
    bus._client = _FakeClient(pubsub)

    sub = bus.subscribe(org)
    received = await asyncio.wait_for(sub.__anext__(), timeout=1)
    assert received.action == "task.escalated"
    assert pubsub.subscribed == [f"events:{org}"]

    await sub.close()
    assert pubsub.unsubscribed == [f"events:{org}"]
    assert pubsub.closed is True


class _FakeSettings:
    def __init__(self, backend):
        self.event_bus_backend = backend
        self.redis_url = "redis://localhost:6379/0"


def test_get_event_bus_selects_redis_backend(monkeypatch):
    reset_event_bus()
    monkeypatch.setattr(event_bus, "get_settings", lambda: _FakeSettings("redis"))
    try:
        assert isinstance(get_event_bus(), RedisEventBus)
    finally:
        reset_event_bus()


def test_get_event_bus_defaults_to_memory(monkeypatch):
    reset_event_bus()
    monkeypatch.setattr(event_bus, "get_settings", lambda: _FakeSettings("memory"))
    try:
        assert isinstance(get_event_bus(), InMemoryEventBus)
    finally:
        reset_event_bus()
