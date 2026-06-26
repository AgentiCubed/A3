"""Dashboard, metric materialization, and exports (JSON / CSV / Power BI ZIP)."""

from __future__ import annotations

import io
import uuid
import zipfile


def _auth(client) -> dict[str, str]:
    email = f"an-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _project_with_run(client, headers) -> str:
    pid = client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": "Do", "estimate_hours": 4}, headers=headers
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents", json={"name": "Worker", "kind": "ai", "provider": "mock"}, headers=headers
    ).json()["id"]
    client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": [{"check": "non_empty"}]},
        headers=headers,
    )
    client.post(
        f"/api/v1/projects/{pid}/risks",
        json={"title": "r", "likelihood": 4, "impact": 5},
        headers=headers,
    )
    return pid


def test_dashboard_reports_metrics(client):
    headers = _auth(client)
    pid = _project_with_run(client, headers)
    dash = client.get(f"/api/v1/projects/{pid}/dashboard", headers=headers).json()
    assert dash["metrics"]["tasks_total"] == 1
    assert dash["metrics"]["tasks_completed"] == 1
    assert dash["metrics"]["completion_rate"] == 1.0
    assert dash["metrics"]["evaluation_pass_rate"] == 1.0
    assert len(dash["agent_metrics"]) == 1
    assert dash["risk_matrix"]["L4I5"] == 1
    assert "project_duration" in dash["timeline"]


def test_recompute_persists_metrics(client):
    headers = _auth(client)
    pid = _project_with_run(client, headers)
    resp = client.post(f"/api/v1/projects/{pid}/metrics/recompute", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_metrics_written"] > 0
    assert body["agent_metrics_written"] > 0


def test_export_json(client):
    headers = _auth(client)
    pid = _project_with_run(client, headers)
    resp = client.get(f"/api/v1/projects/{pid}/export.json", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert body["project_id"] == pid
    assert len(body["tasks"]) == 1
    assert len(body["executions"]) == 1


def test_export_tasks_csv(client):
    headers = _auth(client)
    pid = _project_with_run(client, headers)
    resp = client.get(f"/api/v1/projects/{pid}/export/tasks.csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "task_id,title,status" in resp.text


def test_export_powerbi_zip(client):
    headers = _auth(client)
    pid = _project_with_run(client, headers)
    resp = client.get(f"/api/v1/projects/{pid}/export/powerbi.zip", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = set(zf.namelist())
    assert {
        "dim_project.csv",
        "dim_agent.csv",
        "dim_task.csv",
        "fact_execution.csv",
        "fact_evaluation.csv",
    } <= names


def test_dashboard_is_org_scoped(client):
    headers_a = _auth(client)
    pid = _project_with_run(client, headers_a)
    headers_b = _auth(client)
    assert client.get(f"/api/v1/projects/{pid}/dashboard", headers=headers_b).status_code == 404
