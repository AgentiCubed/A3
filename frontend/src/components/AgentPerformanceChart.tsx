"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AgentMetricRow } from "@/lib/api";

/**
 * Recharts bar chart showing agent success-rate and average evaluation score
 * side-by-side. Uses the same AgentMetricRow data as AgentTable.
 */
export function AgentPerformanceChart({ rows }: { rows: AgentMetricRow[] }) {
  if (rows.length === 0) {
    return <p style={{ color: "#9fb0c0" }}>No agent executions yet.</p>;
  }

  const data = rows.map((r) => ({
    name: r.agent_name.length > 12 ? r.agent_name.slice(0, 12) + "…" : r.agent_name,
    "Success %": Math.round((r.metrics.success_rate ?? 0) * 100),
    "Avg score": r.metrics.avg_score ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
        <XAxis dataKey="name" tick={{ fill: "#9fb0c0", fontSize: 11 }} />
        <YAxis
          yAxisId="success"
          domain={[0, 100]}
          tick={{ fill: "#9fb0c0", fontSize: 11 }}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          yAxisId="score"
          orientation="right"
          domain={[0, 1]}
          tick={{ fill: "#9fb0c0", fontSize: 11 }}
          tickFormatter={(v: number) => v.toFixed(2)}
        />
        <Tooltip
          contentStyle={{
            background: "#161b22",
            border: "1px solid #30363d",
            color: "#e6edf3",
          }}
          formatter={(value: unknown, name: string | number | undefined) =>
            name === "Success %"
              ? `${value}%`
              : typeof value === "number"
                ? value.toFixed(2)
                : String(value)
          }
        />
        <Bar yAxisId="success" dataKey="Success %" fill="#2f6fed" radius={[3, 3, 0, 0]} />
        <Bar yAxisId="score" dataKey="Avg score" fill="#5ad17a" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
