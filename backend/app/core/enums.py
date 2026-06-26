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
