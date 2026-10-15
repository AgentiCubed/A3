"""EventBus adapters: in-memory (tests / single process) and Redis pub/sub.

The domain publishes ``DomainEvent``s through the ``EventBus`` port only; this
module supplies the concrete transports. Selection is settings-driven
(``EVENT_BUS_BACKEND=memory|redis``). The in-memory bus fans out within one
process; the Redis bus fans out across api/worker processes via a channel per
organization (``events:{org_id}``).

The stream is advisory (at-most-once): consumers reconcile against the API,
which reads the database — the durable source of truth.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from datetime import datetime
from functools import lru_cache
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.orchestration.ports import DomainEvent

_QUEUE_MAX = 256  # per-subscriber buffer; slow consumers drop oldest events


def _event_from_json(raw: dict[str, Any]) -> DomainEvent:
    return DomainEvent(
        organization_id=UUID(raw["organization_id"]),
        project_id=UUID(raw["project_id"]) if raw.get("project_id") else None,
        action=raw["action"],
        entity_type=raw["entity_type"],
        entity_id=UUID(raw["entity_id"]) if raw.get("entity_id") else None,
        actor_type=raw.get("actor_type"),
        actor_id=UUID(raw["actor_id"]) if raw.get("actor_id") else None,
        occurred_at=datetime.fromisoformat(raw["occurred_at"]),
        payload=raw.get("payload") or {},
    )


class _QueueSubscription:
    """Async-iterable wrapper over a per-subscriber queue."""

    def __init__(self, queue: asyncio.Queue[DomainEvent], on_close) -> None:
        self._queue = queue
        self._on_close = on_close
        self._closed = False

    def __aiter__(self) -> _QueueSubscription:
        return self

    async def __anext__(self) -> DomainEvent:
        if self._closed:
            raise StopAsyncIteration
        return await self._queue.get()

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._on_close(self._queue)


class InMemoryEventBus:
    """Single-process fan-out. Default backend; also used by the test suite."""

    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue[DomainEvent]]] = {}

    async def publish(self, event: DomainEvent) -> None:
        for queue in self._subscribers.get(event.organization_id, set()).copy():
            if queue.full():  # drop-oldest keeps a slow reader from blocking publishers
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(event)

    def subscribe(self, organization_id: UUID) -> _QueueSubscription:
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue(maxsize=_QUEUE_MAX)
        self._subscribers.setdefault(organization_id, set()).add(queue)

        async def _remove(q: asyncio.Queue[DomainEvent]) -> None:
            self._subscribers.get(organization_id, set()).discard(q)

        return _QueueSubscription(queue, _remove)


class RedisEventBus:
    """Cross-process fan-out over Redis pub/sub (channel per organization)."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(self._redis_url)
        return self._client

    @staticmethod
    def _channel(organization_id: UUID) -> str:
        return f"events:{organization_id}"

    async def publish(self, event: DomainEvent) -> None:
        client = self._get_client()
        await client.publish(self._channel(event.organization_id), json.dumps(event.to_json_dict()))

    def subscribe(self, organization_id: UUID) -> _RedisSubscription:
        return _RedisSubscription(self._get_client(), self._channel(organization_id))


class _RedisSubscription:
    def __init__(self, client, channel: str) -> None:
        self._pubsub = client.pubsub()
        self._channel = channel
        self._subscribed = False

    def __aiter__(self) -> _RedisSubscription:
        return self

    async def __anext__(self) -> DomainEvent:
        if not self._subscribed:
            await self._pubsub.subscribe(self._channel)
            self._subscribed = True
        while True:
            message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message is not None and message.get("type") == "message":
                return _event_from_json(json.loads(message["data"]))

    async def close(self) -> None:
        if self._subscribed:
            await self._pubsub.unsubscribe(self._channel)
        await self._pubsub.aclose()


@lru_cache
def get_event_bus():
    """Composition-root accessor for the process-wide bus (settings-driven)."""
    settings = get_settings()
    if settings.event_bus_backend == "redis":
        return RedisEventBus(settings.redis_url)
    return InMemoryEventBus()


def reset_event_bus() -> None:
    """Test hook: drop the cached bus so a fresh one is built."""
    get_event_bus.cache_clear()
