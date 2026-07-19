"use client";

/**
 * Live activity feed for a project: connection indicator + the most recent
 * domain events (task transitions, approvals, remediations) as they happen.
 */

import { useProjectEvents, type StreamState } from "@/lib/useProjectEvents";

const STATE_LABEL: Record<StreamState, string> = {
  connecting: "Connecting…",
  live: "Live",
  disconnected: "Reconnecting…",
};

const STATE_COLOR: Record<StreamState, string> = {
  connecting: "#e0883a",
  live: "#5ad17a",
  disconnected: "#9a1f1f",
};

function describe(action: string, payload: Record<string, unknown>): string {
  if (action === "task.transition" && typeof payload.status === "string") {
    return `task → ${payload.status}`;
  }
  return action;
}

export function LiveActivity({ projectId }: { projectId: string }) {
  const { events, state } = useProjectEvents(projectId);

  return (
    <div data-testid="live-activity">
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          aria-hidden
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: STATE_COLOR[state],
            display: "inline-block",
          }}
        />
        <span
          role="status"
          data-stream-state={state}
          style={{ fontSize: 13, color: "#8b949e" }}
        >
          {STATE_LABEL[state]}
        </span>
      </div>
      {events.length === 0 ? (
        <p style={{ fontSize: 13, color: "#8b949e" }}>
          No activity yet — events appear here as tasks execute.
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0", fontSize: 13 }}>
          {events.map((e, i) => (
            <li
              key={`${e.occurred_at}-${i}`}
              style={{ padding: "4px 0", borderBottom: "1px solid #21262d" }}
            >
              <code style={{ color: "#2f6fed" }}>{e.entity_type}</code>{" "}
              {describe(e.action, e.payload)}
              <span style={{ color: "#8b949e", marginLeft: 8 }}>
                {new Date(e.occurred_at).toLocaleTimeString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
