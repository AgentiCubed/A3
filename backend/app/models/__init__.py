"""ORM model registry.

Importing this package registers every model on ``Base.metadata`` (so Alembic
autogenerate and test ``create_all`` see them). Add new models to ``__all__`` and
the imports below as later phases land.
"""

from __future__ import annotations

from app.models.agent import (
    Agent,
    AgentCapability,
    AgentToolPermission,
    PromptTemplate,
    Tool,
)
from app.models.approval import Approval
from app.models.audit_event import AuditEvent
from app.models.evaluation import Evaluation, EvaluationCriterion
from app.models.metric import AgentMetric, ProjectMetric
from app.models.organization import Organization
from app.models.project import (
    Milestone,
    Project,
    ProjectMethodology,
    ProjectRequirement,
)
from app.models.risk import Decision, Risk
from app.models.task import Task, TaskDependency
from app.models.task_execution import TaskExecution
from app.models.user import ProjectMember, User

__all__ = [
    "Agent",
    "AgentCapability",
    "AgentMetric",
    "AgentToolPermission",
    "Approval",
    "AuditEvent",
    "Decision",
    "Evaluation",
    "EvaluationCriterion",
    "Milestone",
    "Organization",
    "ProjectMetric",
    "Project",
    "ProjectMember",
    "ProjectMethodology",
    "ProjectRequirement",
    "PromptTemplate",
    "Risk",
    "Task",
    "TaskDependency",
    "TaskExecution",
    "Tool",
    "User",
]
