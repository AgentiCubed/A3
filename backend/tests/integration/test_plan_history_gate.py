"""Plan history is governed even when no plan was approved."""

from __future__ import annotations

from tests.integration.test_decomposition import (
    _auth,
    _generate,
    _planner,
    _project,
)


def _assert_start_and_close_fail_closed(client, headers, project_id: str) -> None:
    start = client.post(
        f"/api/v1/projects/{project_id}/start",
        json={},
        headers=headers,
    )
    assert start.status_code == 409, start.text
    assert start.json()["detail"] == {
        "error": "approved_materialization_invalid",
        "reason": "decomposition plan history exists without an approved plan",
    }

    close = client.post(
        f"/api/v1/projects/{project_id}/close",
        json={"acknowledge_unmet_criteria": True},
        headers=headers,
    )
    assert close.status_code == 409, close.text
    assert close.json()["detail"] == {
        "error": "approved_materialization_invalid",
        "reason": "decomposition plan history exists without an approved plan",
    }


def test_rejected_plan_history_cannot_fall_back_to_legacy_lifecycle(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _generate(client, headers, project["id"], _planner(client, headers)).json()
    rejected = client.post(
        f"/api/v1/projects/{project['id']}/plans/{plan['id']}/reject",
        json={"comment": "Do not execute this plan"},
        headers=headers,
    )
    assert rejected.status_code == 200, rejected.text

    _assert_start_and_close_fail_closed(client, headers, project["id"])


def test_invalid_plan_history_cannot_fall_back_to_legacy_lifecycle(client):
    headers = _auth(client)
    project = _project(client, headers, "[[MALFORMED_PLAN]] produce a brief")
    generated = _generate(client, headers, project["id"], _planner(client, headers))
    assert generated.status_code == 422, generated.text
    assert generated.json()["detail"]["error"] == "plan_generation_failed"

    _assert_start_and_close_fail_closed(client, headers, project["id"])
