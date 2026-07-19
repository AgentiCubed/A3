"""Real-broker execution-spine smoke: HTTP dispatch → Redis → worker process → DB.

The one test in the suite that runs the spine with nothing faked: a real
Celery worker subprocess, the real broker, and the application database.
Gated behind CELERY_BROKER_SMOKE=1 (the CI backend job runs it against its
Postgres + Redis services); skipped everywhere else.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CELERY_BROKER_SMOKE") != "1",
    reason="real-broker smoke; set CELERY_BROKER_SMOKE=1 (CI backend job does)",
)


def test_spine_end_to_end_via_real_broker():
    from fastapi.testclient import TestClient

    from app.api.deps import db_session
    from app.main import app
    from app.orchestration.engines import get_workflow_engine, reset_workflow_engine

    # This test runs against the application's real database (migrated by the
    # CI job), not the sqlite test override — the worker subprocess must see
    # the same rows the API writes.
    override = app.dependency_overrides.pop(db_session, None)
    worker = None
    try:
        # Everything after the override pop lives inside the try so the
        # finally always restores state, even if worker startup raises.
        reset_workflow_engine()
        assert get_workflow_engine() is not None, "smoke requires WORKFLOW_ENGINE_BACKEND=celery"

        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "app.workers.celery_app",
                "worker",
                "--loglevel=warning",
                "--pool=solo",
                "--concurrency=1",
            ],
            env=os.environ.copy(),
        )
        with TestClient(app) as client:
            email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
            client.post(
                "/api/v1/auth/register",
                json={"organization_name": "Smoke", "email": email, "password": "supersecret123"},
            )
            token = client.post(
                "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            pid = client.post(
                "/api/v1/projects", json={"name": "Spine", "objective": "smoke"}, headers=headers
            ).json()["id"]
            task_id = client.post(
                f"/api/v1/projects/{pid}/tasks", json={"title": "Say hello"}, headers=headers
            ).json()["id"]
            agent_id = client.post(
                "/api/v1/agents",
                json={"name": "SmokeWorker", "kind": "ai", "provider": "mock"},
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
                json={"max_attempts": 1, "timeout_s": 20.0},
                headers=headers,
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            # The proof of WS-1: the API answered "queued", not a final result.
            assert body["status"] == "queued", body
            assert body["engine"] == "celery"

            deadline = time.time() + 90
            state = None
            while time.time() < deadline:
                execs = client.get(
                    f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers
                ).json()
                if execs:
                    state = execs[0]["state"]
                    if state == "completed":
                        break
                time.sleep(1)
            assert state == "completed", f"worker did not complete the task (last state={state})"
    finally:
        if worker is not None:
            worker.terminate()
            try:
                worker.wait(timeout=15)
            except subprocess.TimeoutExpired:
                worker.kill()
        if override is not None:
            app.dependency_overrides[db_session] = override
        reset_workflow_engine()
