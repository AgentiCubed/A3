"""The required end-to-end demonstration project runs start to finish."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.artifacts import LocalArtifactStore
from app.seed.demo import build_and_run_demo


async def test_demo_runs_end_to_end(session, tmp_path):
    store = LocalArtifactStore(str(tmp_path / "artifacts"))
    result = await build_and_run_demo(session, store=store, now=datetime(2026, 6, 26, tzinfo=UTC))

    # Project completed and closed.
    assert result["status"] == "closed"
    assert result["task_count"] == 4
    assert result["tasks_completed"] == 4

    # One deliberate failure, then a remediation that completes the task.
    assert result["failures"] >= 1
    assert result["remediation_events"] >= 1
    assert result["deliberate_failure_state"] in ("blocked", "failed")
    assert result["remediated_final_state"] == "completed"

    # A real visualization artifact was produced and indexed.
    assert len(result["deliverables"]) >= 1
    assert any(d["content_type"] == "image/png" for d in result["deliverables"])

    # The Python analysis worker computed real statistics.
    assert result["python_stats"]["mean"] == 116.25
    assert result["python_stats"]["sum"] == 465.0

    # A closeout report was generated.
    assert "Closeout report" in result["closeout_markdown"]
    assert "Failures & remediation" in result["closeout_markdown"]
