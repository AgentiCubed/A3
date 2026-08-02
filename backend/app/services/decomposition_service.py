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
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.capabilities import KNOWN_CAPABILITIES, unknown_capabilities
from app.core.enums import (
    AgentKind,
    AgentRole,
    AgentStatus,
    DecompositionPlanStatus,
    ProjectStatus,
)
from app.core.roles import ActorType
from app.db.queries import get_by_org
from app.evaluation.specs import normalize_rubric_specs, rubric_sha256
from app.models.agent import Agent, AgentCapability
from app.models.audit_event import AuditEvent
from app.models.decomposition_plan import DecompositionPlan
from app.models.project import Project
from app.models.task import Task, TaskDependency
from app.orchestration.adapters.registry import get_adapter, retirement_guidance
from app.orchestration.ports import AgentRunRequest, ProviderCallError
from app.orchestration.state_machine.states import ExecutionState
from app.scheduling.graph import CycleError, DependencyGraph
from app.schemas.decomposition import PlanSpec, PlanTaskAssignmentIn
from app.schemas.project import normalize_deliverable_name, validate_acceptance_criteria
from app.services.errors import NotFound

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


class PlannerUnavailable(Exception):
    pass


class AlreadyDecided(Exception):
    pass


class ActiveDraftExists(Exception):
    pass


class ProjectNotPlannable(Exception):
    pass


class PlanMismatch(Exception):
    pass


class StaleObjective(Exception):
    pass


class MaterializationConflict(Exception):
    pass


class AssignmentError(Exception):
    pass


class AcceptanceConflict(Exception):
    pass


class PlanApprovalRequired(Exception):
    """A draft exists but has not received the explicit lifecycle decision required."""


class MaterializationInvalid(Exception):
    """Approved plan provenance no longer matches the executable project graph."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class GovernedProjectNotStartable(Exception):
    """A governed project has already started or its initial state is no longer intact."""


@dataclass(frozen=True)
class ApprovedMaterialization:
    plan: DecompositionPlan
    spec: PlanSpec
    tasks: list[Task]
    dependencies: list[TaskDependency]


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
    agent = await get_by_org(session, Agent, planner_agent_id, project.organization_id)
    if agent is None:
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


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _merge_project_acceptance(existing: object, generated: object) -> tuple[dict, str]:
    """Monotonically combine user-authored and generated project gates."""
    try:
        existing_spec = validate_acceptance_criteria({} if existing is None else existing)
        generated_spec = validate_acceptance_criteria(generated)
    except ValidationError as exc:
        raise AcceptanceConflict("project acceptance criteria are malformed") from exc

    merged_criteria: list[dict] = []
    canonical_seen: set[str] = set()
    keyed: dict[str, str] = {}
    for criterion in [*existing_spec.criteria, *generated_spec.criteria]:
        raw = criterion.model_dump(mode="json", exclude_none=True)
        canonical = _canonical_json(raw)
        if canonical in canonical_seen:
            continue
        if criterion.key and criterion.key in keyed and keyed[criterion.key] != canonical:
            raise AcceptanceConflict(
                f"project acceptance criterion key '{criterion.key}' conflicts"
            )
        canonical_seen.add(canonical)
        if criterion.key:
            keyed[criterion.key] = canonical
        merged_criteria.append(raw)

    merged_deliverables: list[str] = []
    deliverable_seen: set[str] = set()
    for deliverable in [*existing_spec.deliverables, *generated_spec.deliverables]:
        normalized = normalize_deliverable_name(deliverable)
        if normalized in deliverable_seen:
            continue
        deliverable_seen.add(normalized)
        merged_deliverables.append(deliverable)

    merged = {"criteria": merged_criteria, "deliverables": merged_deliverables}
    # Revalidate the exact JSON that will be persisted.
    validated = validate_acceptance_criteria(merged).model_dump(mode="json", exclude_none=True)
    canonical = _canonical_json(validated)
    return validated, _digest(canonical)


async def _validate_assignments(
    session: AsyncSession,
    *,
    project: Project,
    spec: PlanSpec,
    assignments: list[PlanTaskAssignmentIn],
) -> dict[str, PlanTaskAssignmentIn]:
    assignment_by_key = {assignment.task_key: assignment for assignment in assignments}
    if len(assignment_by_key) != len(assignments):
        raise AssignmentError("assignment task keys must be unique")
    task_by_key = {task.key: task for task in spec.tasks}
    if set(assignment_by_key) != set(task_by_key):
        missing = sorted(set(task_by_key) - set(assignment_by_key))
        extra = sorted(set(assignment_by_key) - set(task_by_key))
        raise AssignmentError(
            f"assignments must exactly cover plan tasks; missing={missing}, extra={extra}"
        )

    agent_ids = {
        agent_id
        for assignment in assignments
        for agent_id in (assignment.agent_id, assignment.evaluator_agent_id)
        if agent_id is not None
    }
    agents = {
        agent.id: agent
        for agent in (await session.execute(select(Agent).where(Agent.id.in_(agent_ids)))).scalars()
    }
    capabilities: dict[uuid.UUID, set[str]] = {}
    if agent_ids:
        rows = (
            await session.execute(
                select(AgentCapability).where(AgentCapability.agent_id.in_(agent_ids))
            )
        ).scalars()
        for capability in rows:
            capabilities.setdefault(capability.agent_id, set()).add(capability.capability)

    for task_key, assignment in assignment_by_key.items():
        task_spec = task_by_key[task_key]
        executor = agents.get(assignment.agent_id)
        if (
            executor is None
            or executor.organization_id != project.organization_id
            or executor.kind != AgentKind.AI
            or executor.status != AgentStatus.ACTIVE
            or executor.default_role not in {AgentRole.EXECUTOR, AgentRole.EITHER}
            or not executor.provider
        ):
            raise AssignmentError(f"executor for task '{task_key}' is unavailable or ineligible")
        missing = sorted(
            set(task_spec.required_capabilities) - capabilities.get(executor.id, set())
        )
        if missing:
            raise AssignmentError(f"executor for task '{task_key}' lacks capabilities: {missing}")

        if assignment.evaluator_agent_id is None:
            continue
        evaluator = agents.get(assignment.evaluator_agent_id)
        if (
            evaluator is None
            or evaluator.organization_id != project.organization_id
            or evaluator.kind != AgentKind.AI
            or evaluator.status != AgentStatus.ACTIVE
            or evaluator.default_role not in {AgentRole.EVALUATOR, AgentRole.EITHER}
            or not evaluator.provider
            or "evaluation.rubric" not in capabilities.get(evaluator.id, set())
        ):
            raise AssignmentError(f"evaluator for task '{task_key}' is unavailable or ineligible")
        if evaluator.id == executor.id:
            raise AssignmentError(f"task '{task_key}' evaluator must differ from its executor")
    return assignment_by_key


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
    approved_plan = await session.scalar(
        select(DecompositionPlan.id).where(
            DecompositionPlan.project_id == project.id,
            DecompositionPlan.status == DecompositionPlanStatus.APPROVED,
        )
    )
    if approved_plan is not None:
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
        async with asyncio.timeout(60):
            result = await adapter.run(
                AgentRunRequest(
                    prompt=_prompt(project),
                    model=planner.model,
                    credential_ref=credential_ref,
                    params={
                        "expected_format": PLAN_CONTRACT,
                        # A full multi-task plan is thousands of JSON tokens;
                        # the previous default truncated it into invalid JSON.
                        "max_tokens": 4096,
                        # Force pure JSON so the strict contract parser never
                        # trips over prose or code fences.
                        "response_format": {"type": "json_object"},
                    },
                )
            )
        raw = result.output
        spec = parse_plan(raw)
    except TimeoutError:
        error_code = "planner_timeout"
        diagnostic = "planner did not return within the 60-second budget"
    except ValueError as exc:
        error_code = "invalid_plan"
        diagnostic = str(exc)[:500]
    except Exception as exc:  # noqa: BLE001 - every planner failure must fail closed
        error_code = "planner_error"
        # A ProviderCallError already carries a public-safe status/category
        # (e.g. provider_http_status=410 provider_error_category=not_found).
        # Recording only the class name discarded exactly the discriminator an
        # operator needs — a retired endpoint and a malformed plan both read as
        # "plan_generation_failed" — so keep the diagnostic the executor path
        # has always kept. Retirement guidance is appended when the provider is
        # a known tombstone.
        if isinstance(exc, ProviderCallError):
            guidance = retirement_guidance(planner.provider)
            diagnostic = f"{exc.public_message} ({guidance})" if guidance else exc.public_message
        else:
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


async def approve_plan(
    session: AsyncSession,
    *,
    project: Project,
    plan_id: uuid.UUID,
    expected_version: int,
    expected_plan_spec_sha256: str,
    assignments: list[PlanTaskAssignmentIn],
    actor_id: uuid.UUID,
    comment: str | None,
) -> tuple[DecompositionPlan, list[Task], int]:
    """Approve exact reviewed bytes and atomically materialize their task graph."""
    locked_project = await session.scalar(
        select(Project).where(Project.id == project.id).with_for_update()
    )
    plan = await session.scalar(
        select(DecompositionPlan)
        .where(
            DecompositionPlan.id == plan_id,
            DecompositionPlan.project_id == project.id,
        )
        .with_for_update()
    )
    if locked_project is None or plan is None:
        raise NotFound("plan")
    project = locked_project
    if project.status != ProjectStatus.PLANNING:
        raise ProjectNotPlannable()
    if plan.status != DecompositionPlanStatus.DRAFT:
        raise AlreadyDecided()
    if plan.contract_version != PLAN_CONTRACT:
        raise PlanMismatch()
    if plan.version != expected_version or plan.plan_spec_sha256 != expected_plan_spec_sha256:
        raise PlanMismatch()
    if _digest(project.objective) != plan.objective_sha256:
        raise StaleObjective()
    if not isinstance(plan.plan_spec, dict):
        raise PlanMismatch()
    canonical_plan = _canonical_json(plan.plan_spec)
    if _digest(canonical_plan) != plan.plan_spec_sha256:
        raise PlanMismatch()
    try:
        spec = PlanSpec.model_validate(plan.plan_spec)
        _validate_plan(spec)
    except (ValidationError, ValueError) as exc:
        raise PlanMismatch() from exc

    existing_task = await session.scalar(select(Task.id).where(Task.project_id == project.id))
    if existing_task is not None:
        raise MaterializationConflict()
    assignment_by_key = await _validate_assignments(
        session, project=project, spec=spec, assignments=assignments
    )
    merged_acceptance, acceptance_sha256 = _merge_project_acceptance(
        project.acceptance_criteria,
        spec.project_acceptance.model_dump(mode="json", exclude_none=True),
    )

    materialized: list[Task] = []
    for index, task_spec in enumerate(spec.tasks):
        assignment = assignment_by_key[task_spec.key]
        task = Task(
            organization_id=project.organization_id,
            project_id=project.id,
            title=task_spec.title,
            description=task_spec.description,
            assigned_agent_id=assignment.agent_id,
            evaluator_agent_id=assignment.evaluator_agent_id,
            required_capabilities=task_spec.required_capabilities,
            acceptance_criteria=[
                criterion.model_dump(mode="json", exclude_none=True)
                for criterion in task_spec.acceptance_criteria
            ],
            max_remediations=assignment.max_remediations,
            estimate_hours=task_spec.estimate_hours,
            priority=task_spec.priority,
            order_index=index,
            source_plan_id=plan.id,
            source_plan_task_key=task_spec.key,
        )
        session.add(task)
        materialized.append(task)
    await session.flush()
    task_by_key = {task.source_plan_task_key: task for task in materialized}
    for dependency in spec.dependencies:
        session.add(
            TaskDependency(
                organization_id=project.organization_id,
                project_id=project.id,
                predecessor_task_id=task_by_key[dependency.predecessor_key].id,
                successor_task_id=task_by_key[dependency.successor_key].id,
                dependency_type=dependency.dependency_type,
                lag_hours=dependency.lag_hours,
            )
        )
    project.acceptance_criteria = merged_acceptance
    await session.flush()

    decided_at = datetime.now(UTC)
    decision = await session.execute(
        update(DecompositionPlan)
        .where(
            DecompositionPlan.id == plan.id,
            DecompositionPlan.status == DecompositionPlanStatus.DRAFT,
        )
        .values(
            status=DecompositionPlanStatus.APPROVED,
            decided_by=actor_id,
            decided_at=decided_at,
            decision_comment=comment,
        )
    )
    if decision.rowcount != 1:
        raise AlreadyDecided()
    await session.refresh(plan)
    task_ids = {task.source_plan_task_key: str(task.id) for task in materialized}
    task_policies = {
        task.source_plan_task_key: {
            "executor_agent_id": str(task.assigned_agent_id),
            "evaluator_agent_id": (
                str(task.evaluator_agent_id) if task.evaluator_agent_id is not None else None
            ),
            "max_remediations": task.max_remediations,
            "rubric_sha256": rubric_sha256(task.acceptance_criteria),
        }
        for task in materialized
    }
    policy_sha256 = _digest(_canonical_json(task_policies))
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="plan.approved",
        entity_type="DecompositionPlan",
        entity_id=plan.id,
        after={
            "status": DecompositionPlanStatus.APPROVED.value,
            "version": plan.version,
            "plan_spec_sha256": plan.plan_spec_sha256,
            "task_ids": task_ids,
            "task_policies": task_policies,
            "policy_sha256": policy_sha256,
            "dependency_count": len(spec.dependencies),
            "acceptance_sha256": acceptance_sha256,
            "comment": comment,
        },
    )
    return plan, materialized, len(spec.dependencies)


async def load_approved_materialization(
    session: AsyncSession,
    *,
    project: Project,
    require_executable_assignments: bool = True,
) -> ApprovedMaterialization | None:
    """Verify the approved plan still exactly matches its executable graph.

    Only projects with no plan history and no plan-derived tasks retain the
    legacy manual workflow. Once any plan decision or plan-derived task exists,
    every provenance link is fail-closed.
    """
    plans = list(
        (
            await session.execute(
                select(DecompositionPlan).where(DecompositionPlan.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    tasks = list(
        (
            await session.execute(
                select(Task).where(Task.project_id == project.id).order_by(Task.order_index)
            )
        )
        .scalars()
        .all()
    )
    approved = [plan for plan in plans if plan.status == DecompositionPlanStatus.APPROVED]
    source_tasks = [task for task in tasks if task.source_plan_id is not None]
    drafts = [plan for plan in plans if plan.status == DecompositionPlanStatus.DRAFT]

    if not approved and not source_tasks:
        if drafts:
            raise PlanApprovalRequired()
        if plans:
            raise MaterializationInvalid(
                "decomposition plan history exists without an approved plan"
            )
        return None
    if len(approved) != 1:
        raise MaterializationInvalid("governed project must have exactly one approved plan")
    if drafts:
        raise MaterializationInvalid("a newer draft must be decided before execution")

    plan = approved[0]
    if plan.organization_id != project.organization_id:
        raise MaterializationInvalid("approved plan organization does not match project")
    if plan.contract_version != PLAN_CONTRACT:
        raise MaterializationInvalid("approved plan contract version is unsupported")
    if plan.objective_sha256 != _digest(plan.objective) or plan.objective != project.objective:
        raise MaterializationInvalid("project objective changed after approval")
    if not isinstance(plan.plan_spec, dict):
        raise MaterializationInvalid("approved plan specification is missing")
    if plan.plan_spec_sha256 != _digest(_canonical_json(plan.plan_spec)):
        raise MaterializationInvalid("approved plan specification hash does not match")
    try:
        spec = PlanSpec.model_validate(plan.plan_spec)
        _validate_plan(spec)
    except (ValidationError, ValueError) as exc:
        raise MaterializationInvalid("approved plan specification no longer validates") from exc

    approval_events = list(
        (
            await session.execute(
                select(AuditEvent).where(
                    AuditEvent.organization_id == project.organization_id,
                    AuditEvent.entity_id == plan.id,
                    AuditEvent.entity_type == "DecompositionPlan",
                    AuditEvent.action == "plan.approved",
                )
            )
        )
        .scalars()
        .all()
    )
    if len(approval_events) != 1 or not isinstance(approval_events[0].after, dict):
        raise MaterializationInvalid("approved plan audit provenance is missing or ambiguous")
    approval = approval_events[0].after
    if approval.get("plan_spec_sha256") != plan.plan_spec_sha256:
        raise MaterializationInvalid("approved plan audit hash does not match")
    if approval.get("version") != plan.version:
        raise MaterializationInvalid("approved plan audit version does not match")

    try:
        acceptance = validate_acceptance_criteria(project.acceptance_criteria)
    except ValidationError as exc:
        raise MaterializationInvalid("project acceptance policy is malformed") from exc
    acceptance_json = acceptance.model_dump(mode="json", exclude_none=True)
    if approval.get("acceptance_sha256") != _digest(_canonical_json(acceptance_json)):
        raise MaterializationInvalid("project acceptance policy changed after approval")

    expected_by_key = {task.key: task for task in spec.tasks}
    actual_by_key = {
        task.source_plan_task_key: task for task in tasks if task.source_plan_task_key is not None
    }
    if len(tasks) != len(spec.tasks) or set(actual_by_key) != set(expected_by_key):
        raise MaterializationInvalid("materialized task set does not exactly match approved plan")
    current_task_ids = {key: str(actual_by_key[key].id) for key in expected_by_key}
    if approval.get("task_ids") != current_task_ids:
        raise MaterializationInvalid("materialized task identities changed after approval")

    assignments: list[PlanTaskAssignmentIn] = []
    current_policies: dict[str, dict] = {}
    for index, expected in enumerate(spec.tasks):
        task = actual_by_key[expected.key]
        expected_rubric = [
            criterion.model_dump(mode="json", exclude_none=True)
            for criterion in expected.acceptance_criteria
        ]
        try:
            actual_rubric = normalize_rubric_specs(task.acceptance_criteria)
        except ValueError as exc:
            raise MaterializationInvalid(
                f"task '{expected.key}' acceptance policy is malformed"
            ) from exc
        exact_fields_match = (
            task.organization_id == project.organization_id
            and task.project_id == project.id
            and task.source_plan_id == plan.id
            and task.title == expected.title
            and task.description == expected.description
            and list(task.required_capabilities or []) == expected.required_capabilities
            and actual_rubric == expected_rubric
            and task.estimate_hours == expected.estimate_hours
            and task.priority == expected.priority
            and task.order_index == index
            and not task.is_human_task
        )
        if not exact_fields_match:
            raise MaterializationInvalid(
                f"task '{expected.key}' differs from its approved specification"
            )
        if task.assigned_agent_id is None:
            raise MaterializationInvalid(f"task '{expected.key}' has no approved executor")
        assignments.append(
            PlanTaskAssignmentIn(
                task_key=expected.key,
                agent_id=task.assigned_agent_id,
                evaluator_agent_id=task.evaluator_agent_id,
                max_remediations=task.max_remediations,
            )
        )
        current_policies[expected.key] = {
            "executor_agent_id": str(task.assigned_agent_id),
            "evaluator_agent_id": (
                str(task.evaluator_agent_id) if task.evaluator_agent_id is not None else None
            ),
            "max_remediations": task.max_remediations,
            "rubric_sha256": rubric_sha256(actual_rubric),
        }

    if approval.get("policy_sha256") != _digest(_canonical_json(current_policies)):
        raise MaterializationInvalid("materialized task policy changed after approval")
    if approval.get("task_policies") != current_policies:
        raise MaterializationInvalid("materialized task policy audit does not match")
    if require_executable_assignments:
        try:
            await _validate_assignments(
                session,
                project=project,
                spec=spec,
                assignments=assignments,
            )
        except AssignmentError as exc:
            raise MaterializationInvalid(
                "approved agent assignment is no longer executable"
            ) from exc

    dependencies = list(
        (
            await session.execute(
                select(TaskDependency).where(TaskDependency.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    if any(dependency.organization_id != project.organization_id for dependency in dependencies):
        raise MaterializationInvalid("dependency organization does not match project")
    key_by_id = {task.id: key for key, task in actual_by_key.items()}
    try:
        actual_dependencies = sorted(
            (
                key_by_id[dependency.predecessor_task_id],
                key_by_id[dependency.successor_task_id],
                dependency.dependency_type.value,
                dependency.lag_hours,
            )
            for dependency in dependencies
        )
    except KeyError as exc:
        raise MaterializationInvalid(
            "dependency references a task outside the approved plan"
        ) from exc
    expected_dependencies = sorted(
        (
            dependency.predecessor_key,
            dependency.successor_key,
            dependency.dependency_type.value,
            dependency.lag_hours,
        )
        for dependency in spec.dependencies
    )
    if actual_dependencies != expected_dependencies:
        raise MaterializationInvalid("dependency graph differs from approved plan")
    if approval.get("dependency_count") != len(dependencies):
        raise MaterializationInvalid("dependency audit count does not match")

    return ApprovedMaterialization(
        plan=plan,
        spec=spec,
        tasks=tasks,
        dependencies=dependencies,
    )


async def begin_project_execution(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID,
) -> ApprovedMaterialization | None:
    """Start a governed project exactly once after revalidating its approved graph."""
    locked = await session.scalar(select(Project).where(Project.id == project.id).with_for_update())
    if locked is None:
        raise NotFound("project")
    materialization = await load_approved_materialization(
        session,
        project=locked,
    )
    if materialization is None:
        return None
    if locked.status != ProjectStatus.PLANNING:
        raise GovernedProjectNotStartable()
    if any(task.status != ExecutionState.PLANNED for task in materialization.tasks):
        raise GovernedProjectNotStartable()

    result = await session.execute(
        update(Project)
        .where(Project.id == locked.id, Project.status == ProjectStatus.PLANNING)
        .values(status=ProjectStatus.ACTIVE)
    )
    if result.rowcount != 1:
        raise GovernedProjectNotStartable()
    await session.refresh(locked)
    await record_audit(
        session,
        organization_id=locked.organization_id,
        project_id=locked.id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="project.started",
        entity_type="Project",
        entity_id=locked.id,
        before={"status": ProjectStatus.PLANNING.value},
        after={
            "status": ProjectStatus.ACTIVE.value,
            "plan_id": str(materialization.plan.id),
            "plan_version": materialization.plan.version,
            "plan_spec_sha256": materialization.plan.plan_spec_sha256,
            "materialized_task_count": len(materialization.tasks),
            "dependency_count": len(materialization.dependencies),
        },
    )
    return materialization
