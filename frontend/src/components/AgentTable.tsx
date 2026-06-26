import type { AgentMetricRow } from "@/lib/api";
import { pct } from "@/lib/metrics";

/** Agent-performance table. */
export function AgentTable({ rows }: { rows: AgentMetricRow[] }) {
  if (rows.length === 0) {
    return <p style={{ color: "#9fb0c0" }}>No agent executions yet.</p>;
  }
  return (
    <table
      aria-label="Agent performance"
      style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}
    >
      <thead>
        <tr style={{ textAlign: "left", color: "#9fb0c0" }}>
          <th style={{ padding: 6 }}>Agent</th>
          <th style={{ padding: 6 }}>Runs</th>
          <th style={{ padding: 6 }}>Success</th>
          <th style={{ padding: 6 }}>Avg score</th>
          <th style={{ padding: 6 }}>Avg tokens</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.agent_id} style={{ borderTop: "1px solid #30363d" }}>
            <td style={{ padding: 6 }}>{r.agent_name}</td>
            <td style={{ padding: 6 }}>{r.metrics.executions}</td>
            <td style={{ padding: 6 }}>{pct(r.metrics.success_rate ?? 0)}</td>
            <td style={{ padding: 6 }}>{(r.metrics.avg_score ?? 0).toFixed(2)}</td>
            <td style={{ padding: 6 }}>{r.metrics.avg_tokens}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
