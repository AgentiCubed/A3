"use client";

/**
 * Plan panel: the first governed write path in the UI (next-steps Step 1a).
 *
 * Generate a decomposition plan from the project objective, render exactly
 * what the planner proposed (tasks, per-task acceptance criteria,
 * dependencies, assumptions, warnings), then approve or reject it.
 *
 * Approval is integrity-bound: the request carries the rendered plan's
 * version and plan_spec_sha256, so the backend refuses if the plan changed
 * after it was displayed — the human approves exactly what they saw.
 * Approval also requires an executor assignment for every proposed task.
 */

import { useCallback, useEffect, useState } from "react";
import {
  backend,
  errorDetail,
  type AgentSummary,
  type DecompositionPlan,
} from "@/lib/backend";

const box: React.CSSProperties = {
  border: "1px solid #2e3440",
  borderRadius: 8,
  padding: 16,
};

const buttonStyle: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: 6,
  border: "1px solid #4a5568",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
};

function StatusPill({ status }: { status: string }) {
  const palette: Record<string, string> = {
    draft: "#e0883a",
    approved: "#5ad17a",
    rejected: "#9a1f1f",
    invalid: "#9a1f1f",
  };
  return (
    <span
      data-plan-status={status}
      style={{
        border: `1px solid ${palette[status] ?? "#4a5568"}`,
        color: palette[status] ?? "inherit",
        borderRadius: 12,
        padding: "2px 10px",
        fontSize: 12,
        textTransform: "uppercase",
      }}
    >
      {status}
    </span>
  );
}

export function PlanPanel({ projectId }: { projectId: string }) {
  const [plans, setPlans] = useState<DecompositionPlan[] | null>(null);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [plannerId, setPlannerId] = useState("");
  const [executorId, setExecutorId] = useState("");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [planRes, agentRes] = await Promise.all([
      backend<DecompositionPlan[]>(`projects/${projectId}/plans`),
      backend<AgentSummary[]>("agents"),
    ]);
    if (planRes.ok) setPlans(planRes.body);
    if (agentRes.ok) setAgents(agentRes.body.filter((a) => a.kind === "ai"));
  }, [projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const latest = plans && plans.length > 0 ? plans[plans.length - 1] : null;
  const draft = latest && latest.status === "draft" ? latest : null;

  async function generate() {
    setBusy(true);
    setError(null);
    setNotice(null);
    const res = await backend(`projects/${projectId}/plans`, {
      method: "POST",
      body: { planner_agent_id: plannerId },
    });
    setBusy(false);
    if (!res.ok) {
      setError(errorDetail(res.body));
      return;
    }
    setNotice("Plan generated — review it below.");
    await refresh();
  }

  async function approve() {
    if (!draft || !draft.plan_spec || !draft.plan_spec_sha256) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    const res = await backend(`projects/${projectId}/plans/${draft.id}/approve`, {
      method: "POST",
      body: {
        expected_version: draft.version,
        expected_plan_spec_sha256: draft.plan_spec_sha256,
        assignments: draft.plan_spec.tasks.map((task) => ({
          task_key: task.key,
          agent_id: executorId,
        })),
        comment: comment || null,
      },
    });
    setBusy(false);
    if (!res.ok) {
      setError(errorDetail(res.body));
      return;
    }
    setNotice("Plan approved — tasks materialized. The project can now start.");
    await refresh();
  }

  async function reject() {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    const res = await backend(`projects/${projectId}/plans/${draft.id}/reject`, {
      method: "POST",
      body: { comment: comment || null },
    });
    setBusy(false);
    if (!res.ok) {
      setError(errorDetail(res.body));
      return;
    }
    setNotice("Plan rejected.");
    await refresh();
  }

  return (
    <section data-testid="plan-panel" style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 18 }}>Plan</h2>

      {error && (
        <p role="alert" style={{ color: "#e0883a" }}>
          {error}
        </p>
      )}
      {notice && (
        <p role="status" data-plan-notice style={{ color: "#5ad17a" }}>
          {notice}
        </p>
      )}

      {!draft && (
        <div style={box}>
          <p style={{ marginTop: 0 }}>
            Generate a plan from the project objective. A planner agent proposes tasks,
            dependencies, and acceptance criteria; nothing runs until a human approves it.
          </p>
          <label>
            Planner agent{" "}
            <select
              aria-label="Planner agent"
              value={plannerId}
              onChange={(e) => setPlannerId(e.target.value)}
            >
              <option value="">Select an agent…</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>{" "}
          <button
            style={buttonStyle}
            disabled={busy || !plannerId}
            onClick={() => void generate()}
          >
            Generate plan
          </button>
          {latest && latest.status !== "draft" && (
            <p style={{ marginBottom: 0, fontSize: 13, opacity: 0.8 }}>
              Last plan: <StatusPill status={latest.status} />
              {latest.decision_comment ? ` — ${latest.decision_comment}` : ""}
              {latest.status === "invalid" && latest.diagnostic
                ? ` — ${latest.diagnostic}`
                : ""}
            </p>
          )}
        </div>
      )}

      {draft && draft.plan_spec && (
        <div style={box} data-testid="plan-draft">
          <p style={{ marginTop: 0 }}>
            Draft plan v{draft.version} <StatusPill status={draft.status} />
          </p>
          <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 14 }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 4 }}>Task</th>
                <th style={{ textAlign: "left", padding: 4 }}>Est. h</th>
                <th style={{ textAlign: "left", padding: 4 }}>Acceptance criteria</th>
              </tr>
            </thead>
            <tbody>
              {draft.plan_spec.tasks.map((task) => (
                <tr key={task.key} style={{ borderTop: "1px solid #2e3440" }}>
                  <td style={{ padding: 4 }}>
                    <strong>{task.title}</strong>
                    {task.description && (
                      <div style={{ opacity: 0.8 }}>{task.description}</div>
                    )}
                  </td>
                  <td style={{ padding: 4 }}>{task.estimate_hours}</td>
                  <td style={{ padding: 4 }}>
                    {task.acceptance_criteria.map((c, i) => (
                      <div key={i}>
                        {c.key ?? c.check ?? "criterion"}
                        {c.check ? ` (${c.check})` : ""}
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {draft.plan_spec.dependencies.length > 0 && (
            <p style={{ fontSize: 13 }}>
              Dependencies:{" "}
              {draft.plan_spec.dependencies
                .map((d) => `${d.predecessor_key} → ${d.successor_key}`)
                .join(", ")}
            </p>
          )}
          {draft.plan_spec.warnings.length > 0 && (
            <p style={{ fontSize: 13, color: "#e0883a" }}>
              Warnings: {draft.plan_spec.warnings.join("; ")}
            </p>
          )}
          {draft.plan_spec.assumptions.length > 0 && (
            <p style={{ fontSize: 13, opacity: 0.8 }}>
              Assumptions: {draft.plan_spec.assumptions.join("; ")}
            </p>
          )}

          <div
            style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}
          >
            <label>
              Executor agent for all tasks{" "}
              <select
                aria-label="Executor agent"
                value={executorId}
                onChange={(e) => setExecutorId(e.target.value)}
              >
                <option value="">Select an agent…</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </label>
            <input
              aria-label="Decision comment"
              placeholder="Decision comment (optional)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              style={{ flex: "1 1 200px", padding: 6 }}
            />
            <button
              style={{ ...buttonStyle, borderColor: "#5ad17a" }}
              disabled={busy || !executorId}
              onClick={() => void approve()}
            >
              Approve plan
            </button>
            <button
              style={{ ...buttonStyle, borderColor: "#9a1f1f" }}
              disabled={busy}
              onClick={() => void reject()}
            >
              Reject plan
            </button>
          </div>
          <p style={{ fontSize: 12, opacity: 0.7, marginBottom: 0 }}>
            Approval is bound to plan v{draft.version} (
            {draft.plan_spec_sha256?.slice(0, 12)}…); if the plan changes before the
            backend receives the decision, it is refused.
          </p>
        </div>
      )}
    </section>
  );
}
