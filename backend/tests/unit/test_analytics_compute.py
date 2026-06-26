"""Pure analytics computation."""

from __future__ import annotations

from app.analytics.compute import (
    AgentExecRow,
    agent_metrics,
    project_metrics,
    risk_matrix,
)


def test_project_metrics_basic():
    pm = project_metrics(
        task_statuses=["completed", "completed", "blocked", "running"],
        execution_states=["completed", "failed", "completed"],
        evaluation_verdicts=["pass", "fail"],
        evaluation_scores=[1.0, 0.0],
        open_risk_severities=[20, 6],
        pending_approvals=1,
    )
    assert pm.metrics["tasks_total"] == 4
    assert pm.metrics["tasks_completed"] == 2
    assert pm.metrics["completion_rate"] == 0.5
    assert pm.metrics["execution_success_rate"] == round(2 / 3, 4)
    assert pm.metrics["evaluation_pass_rate"] == 0.5
    assert pm.metrics["avg_evaluation_score"] == 0.5
    assert pm.metrics["max_risk_severity"] == 20
    assert pm.metrics["pending_approvals"] == 1
    assert pm.status_breakdown["completed"] == 2


def test_project_metrics_empty_is_safe():
    pm = project_metrics(
        task_statuses=[],
        execution_states=[],
        evaluation_verdicts=[],
        evaluation_scores=[],
        open_risk_severities=[],
        pending_approvals=0,
    )
    assert pm.metrics["completion_rate"] == 0.0
    assert pm.metrics["max_risk_severity"] == 0


def test_agent_metrics_grouping():
    rows = [
        AgentExecRow("a", "Alpha", "completed", tokens=100, cost=0.01, score=1.0, passed=True),
        AgentExecRow("a", "Alpha", "failed", tokens=50, cost=0.005, score=0.0, passed=False),
        AgentExecRow("b", "Beta", "completed", tokens=200, cost=0.02, score=0.8, passed=True),
    ]
    out = agent_metrics(rows)
    alpha = next(a for a in out if a.agent_id == "a")
    assert alpha.metrics["executions"] == 2
    assert alpha.metrics["success_rate"] == 0.5
    assert alpha.metrics["avg_tokens"] == 75
    assert alpha.metrics["eval_pass_rate"] == 0.5


def test_risk_matrix_buckets_and_clamps():
    m = risk_matrix([(5, 5), (5, 5), (1, 3), (9, 9)])
    assert m["L5I5"] == 3  # the (9,9) clamps into (5,5)
    assert m["L1I3"] == 1
