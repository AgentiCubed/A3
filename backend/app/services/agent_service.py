"""Agent registry, capability declarations, matching, and task assignment."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.capabilities import unknown_capabilities
from app.core.enums import AgentKind, AgentRole, AgentStatus
from app.core.roles import ActorType
from app.models.agent import Agent, AgentCapability
from app.models.task import Task
from app.orchestration.adapters.registry import UnknownProvider, get_adapter
from app.services.matching import AgentProfile, MatchResult, match_agents


class NotFound(Exception):
    pass


class UnknownCapability(Exception):
    def __init__(self, keys: list[str]):
        self.keys = keys
        super().__init__(f"unknown capabilities: {keys}")


class CapabilityMismatch(Exception):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"agent is missing required capabilities: {missing}")


async def register_agent(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    kind: AgentKind,
    provider: str | None,
    model: str | None,
    default_role: AgentRole,
    config: dict | None,
) -> Agent:
    # An AI agent's provider must be a known adapter.
    if kind == AgentKind.AI and provider is not None:
        try:
            get_adapter(provider)
        except UnknownProvider as exc:
            raise UnknownProvider(provider) from exc

    agent = Agent(
        organization_id=org_id,
        name=name,
        kind=kind,
        provider=provider,
        model=model,
        default_role=default_role,
        config=config,
    )
    session.add(agent)
    await session.flush()
    await record_audit(
        session,
        organization_id=org_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="agent.registered",
        entity_type="Agent",
        entity_id=agent.id,
        after={"name": name, "kind": kind.value, "provider": provider},
    )
    return agent


async def get_agent(session: AsyncSession, org_id: uuid.UUID, agent_id: uuid.UUID) -> Agent:
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.organization_id != org_id:
        raise NotFound("agent")
    return agent


async def add_capability(
    session: AsyncSession,
    *,
    agent: Agent,
    capability: str,
    proficiency: int,
    evidence: str | None,
) -> AgentCapability:
    unknown = unknown_capabilities([capability])
    if unknown:
        raise UnknownCapability(unknown)
    row = AgentCapability(
        organization_id=agent.organization_id,
        agent_id=agent.id,
        capability=capability,
        proficiency=proficiency,
        evidence=evidence,
    )
    session.add(row)
    return row


async def list_agents(session: AsyncSession, org_id: uuid.UUID) -> list[Agent]:
    stmt = select(Agent).where(Agent.organization_id == org_id)
    return list((await session.execute(stmt)).scalars().all())


async def _profiles(session: AsyncSession, org_id: uuid.UUID) -> list[AgentProfile]:
    agents = await list_agents(session, org_id)
    caps_by_agent: dict[uuid.UUID, dict[str, int]] = {}
    stmt = select(AgentCapability).where(AgentCapability.organization_id == org_id)
    for cap in (await session.execute(stmt)).scalars().all():
        caps_by_agent.setdefault(cap.agent_id, {})[cap.capability] = cap.proficiency
    return [
        AgentProfile(
            agent_id=a.id,
            name=a.name,
            is_active=(a.status == AgentStatus.ACTIVE),
            capabilities=caps_by_agent.get(a.id, {}),
        )
        for a in agents
    ]


async def match_for_capabilities(
    session: AsyncSession, org_id: uuid.UUID, required: list[str]
) -> list[MatchResult]:
    return match_agents(required, await _profiles(session, org_id))


async def assign_agent_to_task(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    task: Task,
    agent: Agent,
) -> Task:
    """Assign an agent to a task, enforcing capability coverage."""
    required = list(task.required_capabilities or [])
    profile = await _profiles(session, org_id)
    agent_caps = next((p.capabilities for p in profile if p.agent_id == agent.id), {})
    missing = [c for c in required if c not in agent_caps]
    if missing:
        raise CapabilityMismatch(missing)

    task.assigned_agent_id = agent.id
    await record_audit(
        session,
        organization_id=org_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="task.agent_assigned",
        entity_type="Task",
        entity_id=task.id,
        after={"agent_id": str(agent.id), "agent_name": agent.name},
    )
    return task
