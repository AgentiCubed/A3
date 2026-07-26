"""Opt-in live-provider smoke (next-steps Step 3, gap G4).

Runs ONE real task through ``GitHubModelsProvider`` — dispatch → execution →
evaluation — against the live GitHub Models API, asserting **shape, not
content**. GitHub Models is the standing free inference tier, so this nightly
proof costs nothing to run. It is deliberately excluded from hermetic CI
(assumption A15): it runs only when ``LIVE_PROVIDER_SMOKE=1`` and
``GITHUB_MODELS_TOKEN`` are both present, via the manually-triggered /
nightly ``live-provider-smoke`` workflow.

The Celery-spine variant of this proof lives in
``tests/integration/test_live_provider_celery_smoke.py`` (the
``live-provider-proof`` workflow); this test covers the inline API path.
"""

from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE_PROVIDER_SMOKE") != "1" or not os.environ.get("GITHUB_MODELS_TOKEN"),
    reason="live smoke is opt-in: set LIVE_PROVIDER_SMOKE=1 and GITHUB_MODELS_TOKEN",
)


def _auth(client) -> dict[str, str]:
    email = f"live-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Live Smoke", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_one_real_task_through_the_live_provider(client):
    """Dispatch → execution → evaluation with real inference; shape asserted."""
    headers = _auth(client)
    pid = client.post(
        "/api/v1/projects",
        json={"name": "Live smoke", "objective": "prove the real inference path"},
        headers=headers,
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks",
        json={
            "title": "Confirm readiness",
            "description": "Reply with one short sentence confirming you are operational.",
        },
        headers=headers,
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={
            "name": "Live Model",
            "kind": "ai",
            "provider": "github_models",
            # credential by reference only — resolved from the env at call time
            "config": {"api_key_ref": "GITHUB_MODELS_TOKEN"},
        },
        headers=headers,
    ).json()["id"]
    assert (
        client.patch(
            f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
            json={"agent_id": agent_id},
            headers=headers,
        ).status_code
        == 200
    )

    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={
            "max_attempts": 2,
            "timeout_s": 90.0,
            "rubric": [{"key": "answered", "check": "non_empty"}],
            "max_remediations": 0,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Shape, not content: the loop completed, the output is real non-empty
    # text, and the evaluation gate passed on it.
    assert body["final_state"] == "completed", body
    assert body["verdict"] == "pass"
    assert isinstance(body["output"], str) and body["output"].strip()

    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    completed = [e for e in execs if e["state"] == "completed"]
    assert completed, execs
    final = completed[-1]
    assert final["provider"] == "github_models"
    assert final["tokens_used"] > 0
    # GitHub Models is a free tier: cost is recorded as zero, never negative.
    assert final["cost_estimate"] >= 0

    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert any(e["verdict"] == "pass" for e in evals)
