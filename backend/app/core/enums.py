"""Planning-domain enumerations (persisted as VARCHAR via native_enum=False)."""

from __future__ import annotations

from enum import StrEnum


class ProjectStatus(StrEnum):
    INTAKE = "intake"
    PLANNING = "planning"
    ACTIVE = "active"
    BLOCKED = "blocked"
    CLOSED = "closed"


class Methodology(StrEnum):
    KANBAN = "kanban"
    SCRUM = "scrum"
    WATERFALL = "waterfall"
    CPM = "cpm"
    CCPM = "ccpm"
    HYBRID = "hybrid"


class RecommendedBy(StrEnum):
    SYSTEM = "system"
    USER = "user"


class RequirementKind(StrEnum):
    FUNCTIONAL = "functional"
    NONFUNCTIONAL = "nonfunctional"
    CONSTRAINT = "constraint"
    ACCEPTANCE = "acceptance"


class RequirementPriority(StrEnum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


class MilestoneStatus(StrEnum):
    OPEN = "open"
    REACHED = "reached"
    MISSED = "missed"


class KanbanColumn(StrEnum):
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class DependencyType(StrEnum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class RiskStatus(StrEnum):
    OPEN = "open"
    MITIGATING = "mitigating"
    CLOSED = "closed"


class AgentKind(StrEnum):
    AI = "ai"
    HUMAN = "human"


class AgentStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class AgentRole(StrEnum):
    EXECUTOR = "executor"
    EVALUATOR = "evaluator"
    EITHER = "either"


class ToolKind(StrEnum):
    HTTP = "http"
    PYTHON_FN = "python_fn"
    SHELL = "shell"
    DATA_SOURCE = "data_source"


class ToolSensitivity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PromptRole(StrEnum):
    EXECUTOR = "executor"
    EVALUATOR = "evaluator"


class EvaluatorKind(StrEnum):
    DETERMINISTIC = "deterministic"
    AGENT = "agent"
    HUMAN = "human"


class Verdict(StrEnum):
    PASS = "pass"  # noqa: S105 - evaluation verdict, not a credential
    FAIL = "fail"
    NEEDS_REVISION = "needs_revision"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProjectRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RemediationAction(StrEnum):
    RE_PROMPT = "re_prompt"
    ADD_CONTEXT = "add_context"
    ADD_TOOL = "add_tool"
    SPLIT_TASK = "split_task"
    REPLACE_AGENT = "replace_agent"
    MULTI_AGENT = "multi_agent"
    ADD_SPECIALIST_EVALUATOR = "add_specialist_evaluator"
    ESCALATE_HUMAN = "escalate_human"
    MODIFY_PLAN = "modify_plan"
    UPDATE_ESTIMATES = "update_estimates"
