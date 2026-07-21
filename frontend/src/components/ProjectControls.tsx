"use client";

/**
 * Project run controls: start, halt, resume (next-steps Step 1b).
 *
 * Start kicks the governed loop (refused with a visible reason while a plan
 * awaits approval or the project is halted). Halt closes the intake of new
 * work while in-flight tasks conclude cleanly; resume lifts it and runs a
 * work-conserving pass so the loop picks up exactly where it left off. Every
 * action lands in the audit trail server-side; refusals render as outcomes,
 * never silent failures.
 */

import { useCallback, useEffect, useState } from "react";
import { backend, errorDetail, type ProjectInfo, type StartResult } from "@/lib/backend";

const buttonStyle: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: 6,
  border: "1px solid #4a5568",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
};

export function ProjectControls({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [haltReason, setHaltReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const res = await backend<ProjectInfo>(`projects/${projectId}`);
    if (res.ok) setProject(res.body);
  }, [projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function act(action: () => Promise<{ ok: boolean; body: unknown }>) {
    setBusy(true);
    setError(null);
    setNotice(null);
    const res = await action();
    setBusy(false);
    if (!res.ok) {
      setError(errorDetail(res.body));
      await refresh();
      return null;
    }
    await refresh();
    return res.body;
  }

  async function start() {
    const body = (await act(() =>
      backend<StartResult>(`projects/${projectId}/start`, { method: "POST", body: {} }),
    )) as StartResult | null;
    if (body) {
      const completed = body.tasks.filter((t) => t.status === "completed").length;
      setNotice(
        body.tasks.length === 0
          ? "Started — no dispatchable tasks right now."
          : completed === body.tasks.length
            ? `Started — ${body.tasks.length} task(s) ran to completion.`
            : `Started — ${body.tasks.length} task(s) dispatched via ${body.engine}.`,
      );
    }
  }

  async function halt() {
    const body = await act(() =>
      backend(`projects/${projectId}/halt`, {
        method: "POST",
        body: { reason: haltReason || null },
      }),
    );
    if (body) {
      setNotice("Halted — nothing new will dispatch; in-flight work concludes.");
      setHaltReason("");
    }
  }

  async function resume() {
    const body = (await act(() =>
      backend<StartResult>(`projects/${projectId}/resume`, { method: "POST", body: {} }),
    )) as StartResult | null;
    if (body) {
      setNotice(
        body.tasks.length === 0
          ? "Resumed — nothing was waiting."
          : `Resumed — ${body.tasks.length} task(s) picked back up.`,
      );
    }
  }

  async function close() {
    const body = await act(() =>
      backend(`projects/${projectId}/close`, { method: "POST", body: {} }),
    );
    if (body) {
      setNotice("Project closed — acceptance verified and recorded.");
    }
  }

  const halted = Boolean(project?.halted_at);
  const closed = project?.status === "closed";

  return (
    <section
      data-testid="project-controls"
      style={{
        display: "flex",
        gap: 12,
        alignItems: "center",
        flexWrap: "wrap",
        margin: "12px 0 20px",
      }}
    >
      {project && (
        <span data-testid="project-state" style={{ fontSize: 13, opacity: 0.85 }}>
          Status: {project.status}
          {halted ? " · HALTED" : ""}
        </span>
      )}

      {!closed && !halted && (
        <>
          <button
            style={{ ...buttonStyle, borderColor: "#5ad17a" }}
            disabled={busy}
            onClick={() => void start()}
          >
            Start
          </button>
          <input
            aria-label="Halt reason"
            placeholder="Halt reason (optional)"
            value={haltReason}
            onChange={(e) => setHaltReason(e.target.value)}
            style={{ padding: 6, flex: "0 1 220px" }}
          />
          <button
            style={{ ...buttonStyle, borderColor: "#e0883a" }}
            disabled={busy}
            onClick={() => void halt()}
          >
            Halt
          </button>
          <button style={buttonStyle} disabled={busy} onClick={() => void close()}>
            Close project
          </button>
        </>
      )}
      {!closed && halted && (
        <button
          style={{ ...buttonStyle, borderColor: "#5ad17a" }}
          disabled={busy}
          onClick={() => void resume()}
        >
          Resume
        </button>
      )}

      {error && (
        <span role="alert" data-controls-error style={{ color: "#e0883a", fontSize: 13 }}>
          {error}
        </span>
      )}
      {notice && (
        <span
          role="status"
          data-controls-notice
          style={{ color: "#5ad17a", fontSize: 13 }}
        >
          {notice}
        </span>
      )}
    </section>
  );
}
