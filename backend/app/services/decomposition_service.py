"""Objective-to-draft-plan generation (WS-6A).

Planner output is a versioned, strict JSON contract. Invalid output is stored
and audited but can never become an approvable or executable plan.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
import uuid
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.capabilities import KNOWN_CAPABILITIES, unknown_capabilities
from app.core.enums import AgentKind, AgentStatus, DecompositionPlanStatus, ProjectStatus
from app.core.roles import ActorType
from app.models.agent import Agent, AgentCapability
from app.models.decomposition_plan import DecompositionPlan
from app.models.project import Project
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import AgentRunRequest
from app.scheduling.graph import CycleError, DependencyGraph
from app.schemas.decomposition import PlanSpec

PLAN_CONTRACT = "plan_json_v1"
_SUPPORTED_CHECKS = {
    "non_empty",
    "min_length",
    "max_length",
    "contains_all",
    "contains_any",
    "is_json",
    "regex",
}
_GENERATED_CHECKS = _SUPPORTED_CHECKS - {"regex"}
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class NotFound(Exception):
    pass


class PlannerUnavailable(Exception):
    pass


class AlreadyDecided(Exception):
    pass


class ActiveDraftExists(Exception):
    pass


class ProjectNotPlannable(Exception):
    pass


def _prompt(project: Project) -> str:
    return f"""Create an executable project plan for the objective below.

Return only a JSON object matching plan_json_v1. It must contain:
- tasks: 1-50 tasks with unique keys, titles, descriptions, estimates,
  required_capabilities, priority, and deterministic acceptance_criteria
- dependencies: predecessor_key and successor_key references forming a DAG
- project_acceptance: criteria and/or named deliverables
- assumptions and warnings

Only use supported rubric checks: {', '.join(sorted(_GENERATED_CHECKS))}.
Only use governed capabilities: {', '.join(sorted(KNOWN_CAPABILITIES))}.
Do not assign agents and do not execute work. A human must approve the draft.

--- OBJECTIVE ---
{project.objective}
--- END ---"""


def parse_plan(raw: str) -> PlanSpec:
    text = raw.strip()
    fenced = _FENCE_RE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("planner output is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("planner output must be a JSON object")
    try:
        spec = PlanSpec.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"])
        raise ValueError(f"invalid plan contract at {location}: {first['msg']}") from exc
    _validate_plan(spec)
    return spec


def _validate_plan(spec: PlanSpec) -> None:
    keys = [task.key for task in spec.tasks]
    if len(keys) != len(set(keys)):
        raise ValueError("task keys must be unique")
    known = set(keys)
    graph: DependencyGraph[str] = DependencyGraph()
    for key in keys:
        graph.add_node(key)
    seen_edges: set[tuple[str, str]] = set()
    for dependency in spec.dependencies:
        edge = (dependency.predecessor_key, dependency.successor_key)
        if edge[0] not in known or edge[1] not in known:
            raise ValueError(f"dependency references unknown task: {edge[0]} -> {edge[1]}")
        if edge in seen_edges:
            raise ValueError(f"duplicate dependency: {edge[0]} -> {edge[1]}")
        if dependency.dependency_type.value != "finish_to_start" or dependency.lag_hours != 0:
            raise ValueError("generated plans support only zero-lag finish_to_start dependencies")
        seen_edges.add(edge)
        try:
            graph.add_edge(*edge)
        except CycleError as exc:
            raise ValueError(str(exc)) from exc
    cycle = graph.find_cycle()
    if cycle:
        raise ValueError("dependency cycle detected: " + " -> ".join(cycle))

    unknown = unknown_capabilities(
        [capability for task in spec.tasks for capability in task.required_capabilities]
    )
    if unknown:
        raise ValueError("unknown capabilities: " + ", ".join(sorted(set(unknown))))
    rubric_specs = [criterion for task in spec.tasks for criterion in task.acceptance_criteria]
    rubric_specs.extend(spec.project_acceptance.criteria)
    unsupported = sorted({criterion.check for criterion in rubric_specs} - _SUPPORTED_CHECKS)
    if unsupported:
        raise ValueError("unsupported rubric checks: " + ", ".join(unsupported))
    if any(criterion.check not in _GENERATED_CHECKS for criterion in rubric_specs):
        raise ValueError("generated plans cannot use regex acceptance checks")
    if any(not math.isfinite(criterion.weight) for criterion in rubric_specs):
        raise ValueError("rubric weights must be finite")
    for task in spec.tasks:
        if any(not criterion.key for criterion in task.acceptance_criteria):
            raise ValueError(f"task {task.key} acceptance criteria must have keys")
        criterion_keys = [criterion.key for criterion in task.acceptance_criteria]
        if len(criterion_keys) != len(set(criterion_keys)):
            raise ValueError(f"task {task.key} acceptance criterion keys must be unique")
    if any(not criterion.key for criterion in spec.project_acceptance.criteria):
        raise ValueError("project acceptance criteria must have keys")
    project_criterion_keys = [criterion.key for criterion in spec.project_acceptance.criteria]
    if len(project_criterion_keys) != len(set(project_criterion_keys)):
        raise ValueError("project acceptance criterion keys must be unique")
    if not spec.project_acceptance.criteria and not spec.project_acceptance.deliverables:
        raise ValueError("project_acceptance must define at least one criterion or deliverable")


async def _planner(session: AsyncSession, project: Project, planner_agent_id: uuid.UUID) -> Agent:
    agent = await session.get(Agent, planner_agent_id)
    if agent is None or agent.organization_id != project.organization_id:
        raise NotFound("planner agent")
    if agent.kind != AgentKind.AI or agent.status != AgentStatus.ACTIVE or not agent.provider:
        raise PlannerUnavailable()
    capability = await session.scalar(
        select(AgentCapability.id).where(
            AgentCapability.agent_id == agent.id,
            AgentCapability.capability == "planning.decompose",
        )
    )
    if capability is None:
        raise PlannerUnavailable()
    return agent


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def generate_plan(
    session: AsyncSession,
    *,
    project: Project,
    planner_agent_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> DecompositionPlan:
    if not project.objective.strip():
        raise ValueError("project objective is required")
    # Serialize version allocation and active-draft checks on databases that
    # support row locks. Unique indexes remain the final race-proof boundary.
    locked_project = await session.scalar(
        select(Project).where(Project.id == project.id).with_for_update()
    )
    if locked_project is None:
        raise NotFound("project")
    project = locked_project
    if project.status not in {ProjectStatus.INTAKE, ProjectStatus.PLANNING}:
        raise ProjectNotPlannable()
    existing = await session.scalar(
        select(DecompositionPlan.id).where(
            DecompositionPlan.project_id == project.id,
            DecompositionPlan.status == DecompositionPlanStatus.DRAFT,
        )
    )
    if existing is not None:
        raise ActiveDraftExists()
    version = await session.scalar(
        select(func.coalesce(func.max(DecompositionPlan.version), 0) + 1).where(
            DecompositionPlan.project_id == project.id
        )
    )
    planner = await _planner(session, project, planner_agent_id)
    raw = ""
    spec: PlanSpec | None = None
    error_code: str | None = None
    diagnostic: str | None = None
    try:
        adapter = get_adapter(planner.provider)
        credential_ref = (planner.config or {}).get("api_key_ref")
        async with asyncio.timeout(30):
            result = await adapter.run(
                AgentRunRequest(
                    prompt=_prompt(project),
                    model=planner.model,
                    credential_ref=credential_ref,
                    params={"expected_format": PLAN_CONTRACT},
                )
            )
        raw = result.output
        spec = parse_plan(raw)
    except TimeoutError:
        error_code = "planner_timeout"
        diagnostic = "planner did not return within the 30-second budget"
    except ValueError as exc:
        error_code = "invalid_plan"
        diagnostic = str(exc)[:500]
    except Exception as exc:  # noqa: BLE001 - every planner failure must fail closed
        error_code = "planner_error"
        diagnostic = f"planner failed with {type(exc).__name__}"

    spec_dict = spec.model_dump(mode="json", exclude_none=True) if spec else None
    canonical_spec = (
        json.dumps(spec_dict, sort_keys=True, separators=(",", ":")) if spec_dict else None
    )

    plan = DecompositionPlan(
        organization_id=project.organization_id,
        project_id=project.id,
        planner_agent_id=planner.id,
        contract_version=PLAN_CONTRACT,
        version=int(version or 1),
        objective=project.objective,
        objective_sha256=_digest(project.objective),
        status=DecompositionPlanStatus.DRAFT if spec else DecompositionPlanStatus.INVALID,
        plan_spec=spec_dict,
        plan_spec_sha256=_digest(canonical_spec) if canonical_spec else None,
        provider_output_sha256=_digest(raw) if raw else None,
        provider_output_chars=len(raw),
        error_code=error_code,
        diagnostic=diagnostic,
    )
    session.add(plan)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ActiveDraftExists() from exc
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="plan.generated" if spec else "plan.generation_failed",
        entity_type="DecompositionPlan",
        entity_id=plan.id,
        after={
            "status": plan.status.value,
            "contract_version": PLAN_CONTRACT,
            "version": plan.version,
            "plan_spec_sha256": plan.plan_spec_sha256,
            "provider_output_sha256": plan.provider_output_sha256,
            "provider_output_chars": plan.provider_output_chars,
            "error_code": error_code,
        },
    )
    if spec:
        before_status = project.status
        project.status = ProjectStatus.PLANNING
        if before_status != ProjectStatus.PLANNING:
            await record_audit(
                session,
                organization_id=project.organization_id,
                project_id=project.id,
                actor_type=ActorType.USER,
                actor_id=actor_id,
                action="project.status_changed",
                entity_type="Project",
                entity_id=project.id,
                before={"status": before_status.value},
                after={"status": ProjectStatus.PLANNING.value, "reason": "draft_plan_generated"},
            )
    return plan


async def list_plans(session: AsyncSession, *, project: Project) -> list[DecompositionPlan]:
    stmt = (
        select(DecompositionPlan)
        .where(DecompositionPlan.project_id == project.id)
        .order_by(DecompositionPlan.version)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_plan(
    session: AsyncSession, *, project: Project, plan_id: uuid.UUID
) -> DecompositionPlan:
    plan = await session.get(DecompositionPlan, plan_id)
    if plan is None or plan.project_id != project.id:
        raise NotFound("plan")
    return plan


async def reject_plan(
    session: AsyncSession,
    *,
    project: Project,
    plan_id: uuid.UUID,
    actor_id: uuid.UUID,
    comment: str | None,
) -> DecompositionPlan:
    plan = await get_plan(session, project=project, plan_id=plan_id)
    decided_at = datetime.now(UTC)
    result = await session.execute(
        update(DecompositionPlan)
        .where(
            DecompositionPlan.id == plan.id,
            DecompositionPlan.status == DecompositionPlanStatus.DRAFT,
        )
        .values(
            status=DecompositionPlanStatus.REJECTED,
            decided_by=actor_id,
            decided_at=decided_at,
            decision_comment=comment,
        )
    )
    if result.rowcount != 1:
        raise AlreadyDecided()
    await session.refresh(plan)
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="plan.rejected",
        entity_type="DecompositionPlan",
        entity_id=plan.id,
        after={"status": plan.status.value, "comment": comment},
    )
    return plan
