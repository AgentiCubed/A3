"""The demo proves the governed objective-to-close path without shortcuts."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.artifacts import LocalArtifactStore
from app.seed.demo import DEMO_ACCEPTANCE_TOKEN, MOCK_DISCLOSURE, build_and_run_demo


async def test_demo_runs_governed_objective_to_close(session, tmp_path):
    store = LocalArtifactStore(str(tmp_path / "artifacts"))
    result = await build_and_run_demo(
        session,
        store=store,
        now=datetime(2026, 6, 26, tzinfo=UTC),
    )

    assert result["status"] == "closed"
    assert result["task_count"] == 2
    assert result["tasks_completed"] == 2
    assert result["execution_order"] == ["research", "deliver"]

    plan = result["plan"]
    assert plan["draft_created"] is True
    assert plan["status"] == "approved"
    assert plan["plan_spec_sha256"] == plan["approved_exact_sha256"]
    assert plan["task_keys"] == ["research", "deliver"]
    assert plan["dependency_count"] == 1
    assert plan["approval_audit_count"] == 1

    assert result["start"] == {
        "status_after_start": "active",
        "audit_count": 1,
        "plan_id": plan["id"],
    }

    evaluation_by_task = {proof["task_key"]: proof for proof in result["evaluations"]}
    assert evaluation_by_task["research"]["verdicts"] == ["pass"]
    assert evaluation_by_task["deliver"]["verdicts"] == ["needs_revision", "pass"]
    assert all(proof["final_verdict"] == "pass" for proof in result["evaluations"])
    assert all(proof["evaluation_ids"] for proof in result["evaluations"])
    assert all(proof["rubric_sha256"] for proof in result["evaluations"])

    assert result["remediation"]["count"] == 1
    assert result["remediation"]["task_key"] == "deliver"
    assert result["remediation"]["attempts"] == 2
    assert result["remediation"]["runtime_remediations"] == 1
    assert result["remediation"]["linked_attempts"] == 1

    assert len(result["tool_invocations"]) == 1
    assert result["tool_invocations"][0]["tool"] == "analysis.summary_stats"
    assert result["tool_invocations"][0]["status"] == "ok"

    artifacts = {artifact["name"]: artifact for artifact in result["artifacts"]}
    assert set(artifacts) == {"market-brief.md", "demand-chart.png"}
    assert artifacts["market-brief.md"]["content_type"] == "text/markdown"
    assert artifacts["demand-chart.png"]["content_type"] == "image/png"
    assert all(artifact["id"] and artifact["sha256"] for artifact in artifacts.values())

    brief = store.get(artifacts["market-brief.md"]["storage_key"]).decode()
    chart = store.get(artifacts["demand-chart.png"]["storage_key"])
    assert MOCK_DISCLOSURE in brief
    assert DEMO_ACCEPTANCE_TOKEN in brief
    assert chart.startswith(b"\x89PNG\r\n\x1a\n")

    assert result["python_stats"]["mean"] == 116.25
    assert result["python_stats"]["sum"] == 465.0
    assert result["acceptance"]["evaluated"] is True
    assert result["acceptance"]["satisfied"] is True
    assert all(criterion["passed"] for criterion in result["acceptance"]["results"])

    assert result["close"]["audit_count"] == 1
    close = result["close"]["details"]
    assert close["plan_id"] == plan["id"]
    assert close["all_plan_tasks_completed"] is True
    assert close["acceptance_satisfied"] is True
    assert close["unmet_acknowledged"] is False
    assert len(close["task_evaluation_ids"]) == 2

    assert result["mock_provider_disclosure"] == MOCK_DISCLOSURE
    assert "Closeout report" in result["closeout_markdown"]
    assert "Acceptance criteria" in result["closeout_markdown"]
