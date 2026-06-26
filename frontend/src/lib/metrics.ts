/**
 * Pure dashboard helpers. No React/DOM — exhaustively unit-testable.
 */

import type { GraphEdge, GraphNode, TaskSchedule } from "@/lib/api";

export function pct(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export interface GanttRow {
  taskId: string;
  leftPct: number;
  widthPct: number;
  isCritical: boolean;
}

/** Scale CPM schedules into 0–100% horizontal bars over the project duration. */
export function ganttRows(
  schedules: TaskSchedule[],
  projectDuration: number,
): GanttRow[] {
  const span = projectDuration > 0 ? projectDuration : 1;
  return schedules.map((s) => ({
    taskId: s.task_id,
    leftPct: (s.earliest_start / span) * 100,
    widthPct: Math.max(1, ((s.earliest_finish - s.earliest_start) / span) * 100),
    isCritical: s.is_critical,
  }));
}

/** Build a 5x5 risk-matrix grid (impact rows top→bottom 5..1, likelihood cols 1..5). */
export function riskGrid(matrix: Record<string, number>): number[][] {
  const grid: number[][] = [];
  for (let impact = 5; impact >= 1; impact--) {
    const row: number[] = [];
    for (let likelihood = 1; likelihood <= 5; likelihood++) {
      row.push(matrix[`L${likelihood}I${impact}`] ?? 0);
    }
    grid.push(row);
  }
  return grid;
}

/** Severity bucket for a (likelihood, impact) cell — drives the heat color. */
export function severityClass(
  likelihood: number,
  impact: number,
): "low" | "medium" | "high" {
  const s = likelihood * impact;
  if (s >= 15) return "high";
  if (s >= 6) return "medium";
  return "low";
}

/** Emit a Mermaid flowchart for the dependency graph (critical nodes marked). */
export function mermaidFromGraph(nodes: GraphNode[], edges: GraphEdge[]): string {
  const lines = ["graph LR"];
  const short = (id: string) => `T_${id.replace(/-/g, "").slice(0, 8)}`;
  for (const n of nodes) {
    const label = n.title.replace(/"/g, "'");
    lines.push(`  ${short(n.id)}["${label}"]${n.is_critical ? ":::crit" : ""}`);
  }
  for (const e of edges) {
    lines.push(`  ${short(e.predecessor_task_id)} --> ${short(e.successor_task_id)}`);
  }
  lines.push("  classDef crit fill:#7a1f1f,stroke:#ff6b6b,color:#fff;");
  return lines.join("\n");
}
