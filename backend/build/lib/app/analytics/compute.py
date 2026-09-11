"""Pure metric computation.

Operates on plain Python values (no ORM/DB), so it is exhaustively unit-testable.
The analytics service loads rows and feeds them here.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectMetrics:
    metrics: dict[str, float]
    status_breakdown: dict[str, int]


def _rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def project_metrics(
    *,
    task_statuses: list[str],
    execution_states: list[str],
    evaluation_verdicts: list[str],
    evaluation_scores: list[float],
    open_risk_severities: list[int],
    pending_approvals: int,
) -> ProjectMetrics:
    total = len(task_statuses)
    completed = task_statuses.count("completed")
    blocked = task_statuses.count("blocked")
    exec_total = len(execution_states)
    exec_ok = execution_states.count("completed")
    eval_total = len(evaluation_verdicts)
    eval_pass = evaluation_verdicts.count("pass")
    avg_score = (
        round(sum(evaluation_scores) / len(evaluation_scores), 4) if evaluation_scores else 0.0
    )

    metrics = {
        "tasks_total": float(total),
        "tasks_completed": float(completed),
        "tasks_blocked": float(blocked),
        "completion_rate": _rate(completed, total),
        "execution_count": float(exec_total),
        "execution_success_rate": _rate(exec_ok, exec_total),
        "evaluation_count": float(eval_total),
        "evaluation_pass_rate": _rate(eval_pass, eval_total),
        "avg_evaluation_score": avg_score,
        "open_risks": float(len(open_risk_severities)),
        "max_risk_severity": float(max(open_risk_severities, default=0)),
        "pending_approvals": float(pending_approvals),
    }
    return ProjectMetrics(metrics=metrics, status_breakdown=dict(Counter(task_statuses)))


@dataclass(frozen=True)
class AgentExecRow:
    agent_id: str
    agent_name: str
    state: str  # execution attempt state (completed/failed)
    tokens: int = 0
    cost: float = 0.0
    score: float | None = None  # evaluation score for this execution, if any
    passed: bool | None = None


@dataclass(frozen=True)
class AgentMetrics:
    agent_id: str
    agent_name: str
    metrics: dict[str, float] = field(default_factory=dict)


def agent_metrics(rows: list[AgentExecRow]) -> list[AgentMetrics]:
    by_agent: dict[str, list[AgentExecRow]] = {}
    for r in rows:
        by_agent.setdefault(r.agent_id, []).append(r)

    out: list[AgentMetrics] = []
    for agent_id, rs in by_agent.items():
        n = len(rs)
        successes = sum(1 for r in rs if r.state == "completed")
        scores = [r.score for r in rs if r.score is not None]
        passes = [r for r in rs if r.passed is True]
        evaluated = [r for r in rs if r.passed is not None]
        out.append(
            AgentMetrics(
                agent_id=agent_id,
                agent_name=rs[0].agent_name,
                metrics={
                    "executions": float(n),
                    "success_rate": _rate(successes, n),
                    "avg_tokens": round(sum(r.tokens for r in rs) / n, 2) if n else 0.0,
                    "avg_cost": round(sum(r.cost for r in rs) / n, 6) if n else 0.0,
                    "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                    "eval_pass_rate": _rate(len(passes), len(evaluated)),
                },
            )
        )
    out.sort(key=lambda a: a.agent_name)
    return out


def risk_matrix(cells: list[tuple[int, int]]) -> dict[str, int]:
    """Bucket (likelihood, impact) risk cells into a 5x5 matrix.

    Returns a flat map "L{likelihood}I{impact}" -> count for easy UI rendering.
    """
    counter: Counter[str] = Counter()
    for likelihood, impact in cells:
        lk = min(5, max(1, likelihood))
        im = min(5, max(1, impact))
        counter[f"L{lk}I{im}"] += 1
    return dict(counter)
