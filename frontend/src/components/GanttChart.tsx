import type { TaskSchedule } from "@/lib/api";
import { ganttRows } from "@/lib/metrics";

/** Minimal CPM Gantt: one bar per task, critical path highlighted. */
export function GanttChart({
  schedules,
  projectDuration,
  titles,
}: {
  schedules: TaskSchedule[];
  projectDuration: number;
  titles: Record<string, string>;
}) {
  const rows = ganttRows(schedules, projectDuration);
  if (rows.length === 0) {
    return <p style={{ color: "#9fb0c0" }}>No scheduled tasks.</p>;
  }
  return (
    <div aria-label="Gantt chart" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {rows.map((r) => (
        <div key={r.taskId} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 160, fontSize: 12, color: "#c9d4df" }}>
            {titles[r.taskId] ?? r.taskId.slice(0, 8)}
          </span>
          <div style={{ position: "relative", flex: 1, height: 18, background: "#0d1117" }}>
            <div
              style={{
                position: "absolute",
                left: `${r.leftPct}%`,
                width: `${r.widthPct}%`,
                height: "100%",
                background: r.isCritical ? "#c0392b" : "#2f6fed",
                borderRadius: 3,
              }}
            />
          </div>
        </div>
      ))}
      <div style={{ fontSize: 11, color: "#9fb0c0", marginTop: 4 }}>
        Duration: {projectDuration}h · <span style={{ color: "#c0392b" }}>red = critical path</span>
      </div>
    </div>
  );
}
