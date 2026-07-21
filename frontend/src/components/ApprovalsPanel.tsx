"use client";

/**
 * Approval-gate decisions (next-steps Step 1c): pending human gates from the
 * approvals API, decided in place with a justification. Approving completes
 * the escalated task; rejecting routes it back to READY for another pass.
 * Decisions are audited server-side; an already-decided gate surfaces as a
 * visible refusal, not a silent no-op.
 */

import { useCallback, useEffect, useState } from "react";
import { backend, errorDetail, type ApprovalInfo } from "@/lib/backend";

const buttonStyle: React.CSSProperties = {
  padding: "4px 12px",
  borderRadius: 6,
  border: "1px solid #4a5568",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
};

export function ApprovalsPanel({ projectId }: { projectId: string }) {
  const [approvals, setApprovals] = useState<ApprovalInfo[] | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const res = await backend<ApprovalInfo[]>(`projects/${projectId}/approvals`);
    if (res.ok) setApprovals(res.body);
  }, [projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function decide(approval: ApprovalInfo, approve: boolean) {
    setBusy(true);
    setError(null);
    setNotice(null);
    const res = await backend(`projects/${projectId}/approvals/${approval.id}/decide`, {
      method: "POST",
      body: { approve, comment: comments[approval.id] || null },
    });
    setBusy(false);
    if (!res.ok) {
      setError(errorDetail(res.body));
      await refresh();
      return;
    }
    setNotice(
      approve
        ? "Approved — the task completes."
        : "Rejected — the task returns to READY.",
    );
    await refresh();
  }

  const pending = (approvals ?? []).filter((a) => a.status === "pending");
  const decided = (approvals ?? []).filter((a) => a.status !== "pending");

  return (
    <section data-testid="approvals-panel" style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 18 }}>Approval gates</h2>

      {error && (
        <p role="alert" data-approvals-error style={{ color: "#e0883a" }}>
          {error}
        </p>
      )}
      {notice && (
        <p role="status" data-approvals-notice style={{ color: "#5ad17a" }}>
          {notice}
        </p>
      )}

      {approvals !== null && pending.length === 0 && (
        <p data-testid="no-pending-approvals" style={{ opacity: 0.7, fontSize: 14 }}>
          No pending approval gates.
        </p>
      )}

      {pending.map((approval) => (
        <div
          key={approval.id}
          data-testid="pending-approval"
          style={{
            border: "1px solid #2e3440",
            borderRadius: 8,
            padding: 14,
            marginBottom: 10,
          }}
        >
          <p style={{ marginTop: 0 }}>
            {approval.requested_action}{" "}
            <span style={{ fontSize: 12, opacity: 0.7 }}>
              (risk: {approval.risk_level})
            </span>
          </p>
          <div
            style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}
          >
            <input
              aria-label="Justification"
              placeholder="Justification (recorded with the decision)"
              value={comments[approval.id] ?? ""}
              onChange={(e) =>
                setComments((prev) => ({ ...prev, [approval.id]: e.target.value }))
              }
              style={{ padding: 6, flex: "1 1 240px" }}
            />
            <button
              style={{ ...buttonStyle, borderColor: "#5ad17a" }}
              disabled={busy}
              onClick={() => void decide(approval, true)}
            >
              Approve
            </button>
            <button
              style={{ ...buttonStyle, borderColor: "#9a1f1f" }}
              disabled={busy}
              onClick={() => void decide(approval, false)}
            >
              Reject
            </button>
          </div>
        </div>
      ))}

      {decided.length > 0 && (
        <p style={{ fontSize: 13, opacity: 0.7 }}>
          Decided:{" "}
          {decided
            .map((a) => `${a.status}${a.comment ? ` (${a.comment})` : ""}`)
            .join("; ")}
        </p>
      )}
    </section>
  );
}
