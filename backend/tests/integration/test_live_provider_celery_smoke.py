"""Opt-in proof: HTTP dispatch -> Redis -> Celery -> live model -> Postgres.

This file is intentionally skipped by normal CI. The manual GitHub workflow
sets ``LIVE_PROVIDER_SMOKE=1`` and supplies a short-lived GitHub Models token.
No prompt, model output, credential, or raw provider receipt is written to the
sanitized evidence artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from celery.result import AsyncResult
from redis import Redis
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE_PROVIDER_SMOKE") != "1",
    reason="manual live-provider proof; set LIVE_PROVIDER_SMOKE=1",
)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    assert value, f"{name} is required for the live-provider proof"
    return value


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_live_provider_via_real_celery_and_redis():
    from fastapi.testclient import TestClient

    from app.api.deps import db_session
    from app.main import app
    from app.orchestration.engines import get_workflow_engine, reset_workflow_engine
    from app.orchestration.ports import parse_provider_diagnostic
    from app.workers.celery_app import celery_app

    _required_env("GEMINI_API_KEY")
    model = _required_env("LIVE_PROVIDER_MODEL")
    evidence_path = Path(_required_env("LIVE_PROVIDER_EVIDENCE_PATH"))
    broker_url = _required_env("CELERY_BROKER_URL")
    result_url = _required_env("CELERY_RESULT_BACKEND")

    override = app.dependency_overrides.pop(db_session, None)
    worker: subprocess.Popen | None = None
    broker = Redis.from_url(broker_url)
    result_store = Redis.from_url(result_url)
    try:
        reset_workflow_engine()
        engine = get_workflow_engine()
        assert engine is not None and engine.name == "celery"
        assert not celery_app.conf.task_always_eager

        # The workflow provides a fresh, isolated Redis service. Refuse to run
        # over an already-populated broker instead of deleting shared data.
        assert broker.llen("celery") == 0

        with TestClient(app) as client:
            email = f"live-proof-{uuid.uuid4().hex[:10]}@example.com"
            register = client.post(
                "/api/v1/auth/register",
                json={
                    "organization_name": "Live Provider Proof",
                    "email": email,
                    "password": "supersecret123",
                },
            )
            assert register.status_code == 201, register.text
            login = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "supersecret123"},
            )
            assert login.status_code == 200, login.text
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            nonce = uuid.uuid4().hex
            project = client.post(
                "/api/v1/projects",
                json={"name": "Live provider proof", "objective": "Prove real inference"},
                headers=headers,
            )
            assert project.status_code == 201, project.text
            project_id = project.json()["id"]

            task = client.post(
                f"/api/v1/projects/{project_id}/tasks",
                json={
                    "title": "Return the live proof marker",
                    "description": (
                        f"Return exactly LIVE_PROVIDER_OK:{nonce}. " "Do not add any other text."
                    ),
                },
                headers=headers,
            )
            assert task.status_code == 201, task.text
            task_id = task.json()["id"]

            agent = client.post(
                "/api/v1/agents",
                json={
                    "name": "GitHub Models live worker",
                    "kind": "ai",
                    "provider": "gemini",
                    "model": model,
                    "config": {"api_key_ref": "GEMINI_API_KEY"},
                },
                headers=headers,
            )
            assert agent.status_code == 201, agent.text
            assigned = client.patch(
                f"/api/v1/projects/{project_id}/tasks/{task_id}/assign",
                json={"agent_id": agent.json()["id"]},
                headers=headers,
            )
            assert assigned.status_code == 200, assigned.text

            # Dispatch before a worker exists. The API must return from the
            # broker publish without executing anything in-process.
            dispatch = client.post(
                f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch",
                json={
                    "max_attempts": 1,
                    "timeout_s": 90,
                    "rubric": [{"key": "live-output", "check": "non_empty"}],
                    "max_remediations": 0,
                },
                headers=headers,
            )
            assert dispatch.status_code == 200, dispatch.text
            accepted = dispatch.json()
            assert accepted["status"] == "queued"
            assert accepted["engine"] == "celery"
            handle = accepted["engine_handle"]
            assert handle
            assert (
                client.get(
                    f"/api/v1/projects/{project_id}/tasks/{task_id}/executions",
                    headers=headers,
                ).json()
                == []
            )
            broker_depth_before_worker = broker.llen("celery")
            assert broker_depth_before_worker >= 1

            # Only now may a separate worker consume the Redis message and
            # perform the external provider request.
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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            celery_result = AsyncResult(handle, app=celery_app)
            deadline = time.time() + 150
            while time.time() < deadline and not celery_result.ready():
                time.sleep(1)
            assert (
                celery_result.state == "SUCCESS"
            ), f"Celery did not succeed (state={celery_result.state})"
            assert celery_result.result == task_id
            assert result_store.exists(f"celery-task-meta-{handle}") == 1

            executions = client.get(
                f"/api/v1/projects/{project_id}/tasks/{task_id}/executions",
                headers=headers,
            ).json()
            assert len(executions) == 1
            execution = executions[0]
            if execution["state"] != "completed":
                http_status, error_category = parse_provider_diagnostic(execution.get("error"))
                failure_evidence = {
                    "schema_version": 2,
                    "proof_status": "failed",
                    "generated_at": datetime.now(UTC).isoformat(),
                    "git_sha": os.environ.get("GITHUB_SHA", "local"),
                    "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                    "github_run_url": (
                        f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/"
                        f"{os.environ['GITHUB_RUN_ID']}"
                        if os.environ.get("GITHUB_REPOSITORY") and os.environ.get("GITHUB_RUN_ID")
                        else None
                    ),
                    "execution_state": execution["state"],
                    "provider_http_status": http_status,
                    "provider_error_category": error_category,
                }
                evidence_path.parent.mkdir(parents=True, exist_ok=True)
                evidence_path.write_text(
                    json.dumps(failure_evidence, indent=2, sort_keys=True) + "\n"
                )
                status_text = str(http_status) if http_status is not None else "none"
                category_text = error_category or "unknown"
                pytest.fail(
                    "live provider request failed "
                    f"(provider_http_status={status_text} "
                    f"provider_error_category={category_text})",
                    pytrace=False,
                )
            assert execution["provider"] == "gemini"
            assert execution["error"] is None
            assert execution["output"]
            if nonce not in execution["output"]:
                raise AssertionError(
                    "provider output omitted the proof marker "
                    f"(chars={len(execution['output'])}, sha256={_sha256(execution['output'])})"
                )

            evaluations = client.get(
                f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations",
                headers=headers,
            ).json()
            assert len(evaluations) == 1
            evaluation = evaluations[0]
            assert evaluation["verdict"] == "pass"
            assert evaluation["rubric_source"] == "request"

            tasks = client.get(
                f"/api/v1/projects/{project_id}/tasks",
                headers=headers,
            ).json()
            final_task = next(row for row in tasks if row["id"] == task_id)
            assert final_task["status"] == "completed"

            # Use a separate synchronous connection rather than reusing the
            # API's async pool across TestClient's portal event loop.
            receipt_engine = create_engine(_required_env("DATABASE_URL_SYNC"))
            try:
                with receipt_engine.connect() as connection:
                    provider_request_id = connection.execute(
                        text(
                            "SELECT provider_request_id FROM task_executions "
                            "WHERE id = :execution_id"
                        ),
                        {"execution_id": uuid.UUID(execution["id"])},
                    ).scalar_one()
            finally:
                receipt_engine.dispose()
            assert provider_request_id
            evidence = {
                "schema_version": 2,
                "proof_status": "passed",
                "generated_at": datetime.now(UTC).isoformat(),
                "git_sha": os.environ.get("GITHUB_SHA", "local"),
                "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "github_run_url": (
                    f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/"
                    f"{os.environ['GITHUB_RUN_ID']}"
                    if os.environ.get("GITHUB_REPOSITORY") and os.environ.get("GITHUB_RUN_ID")
                    else None
                ),
                "project_id": project_id,
                "task_id": task_id,
                "execution_id": execution["id"],
                "engine": "celery",
                "engine_handle": handle,
                "celery_result_task_id": str(celery_result.result),
                "task_always_eager": False,
                "broker_transport": "redis",
                "broker_queue_depth_before_worker": broker_depth_before_worker,
                "result_transport": "redis",
                "result_backend_receipt_present": True,
                "celery_state": celery_result.state,
                "provider": execution["provider"],
                "model": model,
                "provider_request_id_sha256": _sha256(provider_request_id),
                "execution_state": execution["state"],
                "attempt_number": execution["attempt_number"],
                "tokens_used": execution["tokens_used"],
                "tokens_reported": execution["tokens_used"] > 0,
                "output_chars": len(execution["output"]),
                "output_sha256": _sha256(execution["output"]),
                "evaluation_verdict": evaluation["verdict"],
                "rubric_sha256": evaluation["rubric_sha256"],
            }
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    finally:
        if worker is not None:
            worker.terminate()
            try:
                worker.wait(timeout=15)
            except subprocess.TimeoutExpired:
                worker.kill()
        broker.close()
        result_store.close()
        if override is not None:
            app.dependency_overrides[db_session] = override
        reset_workflow_engine()
