import { describe, expect, it } from "vitest";
import { ganttRows, mermaidFromGraph, pct, riskGrid, severityClass } from "@/lib/metrics";

describe("pct", () => {
  it("formats a rate as a rounded percentage", () => {
    expect(pct(0.5)).toBe("50%");
    expect(pct(1)).toBe("100%");
    expect(pct(0.666)).toBe("67%");
  });
});

describe("ganttRows", () => {
  it("scales schedules to 0-100% bars", () => {
    const rows = ganttRows(
      [
        {
          task_id: "a",
          earliest_start: 0,
          earliest_finish: 3,
          slack: 0,
          is_critical: true,
        },
        {
          task_id: "b",
          earliest_start: 3,
          earliest_finish: 9,
          slack: 0,
          is_critical: true,
        },
      ],
      9,
    );
    expect(rows[0].leftPct).toBe(0);
    expect(rows[0].widthPct).toBeCloseTo((3 / 9) * 100);
    expect(rows[1].leftPct).toBeCloseTo((3 / 9) * 100);
    expect(rows[1].isCritical).toBe(true);
  });

  it("handles zero duration without dividing by zero", () => {
    const rows = ganttRows(
      [
        {
          task_id: "a",
          earliest_start: 0,
          earliest_finish: 0,
          slack: 0,
          is_critical: false,
        },
      ],
      0,
    );
    expect(Number.isFinite(rows[0].leftPct)).toBe(true);
  });
});

describe("riskGrid", () => {
  it("builds a 5x5 grid with impact descending", () => {
    const grid = riskGrid({ L4I5: 2, L1I1: 1 });
    expect(grid.length).toBe(5);
    expect(grid[0].length).toBe(5);
    // top-left cell is likelihood 1 / impact 5; (4,5) is row 0 col 3.
    expect(grid[0][3]).toBe(2);
    // bottom-left is likelihood 1 / impact 1.
    expect(grid[4][0]).toBe(1);
  });
});

describe("severityClass", () => {
  it("buckets by likelihood*impact", () => {
    expect(severityClass(5, 5)).toBe("high");
    expect(severityClass(2, 3)).toBe("medium");
    expect(severityClass(1, 2)).toBe("low");
  });
});

describe("mermaidFromGraph", () => {
  it("emits a flowchart with edges and a critical class", () => {
    const src = mermaidFromGraph(
      [
        { id: "11111111-aaaa", title: "A", is_critical: true },
        { id: "22222222-bbbb", title: "B", is_critical: false },
      ],
      [
        {
          predecessor_task_id: "11111111-aaaa",
          successor_task_id: "22222222-bbbb",
          dependency_type: "finish_to_start",
          lag_hours: 0,
        },
      ],
    );
    expect(src.startsWith("graph LR")).toBe(true);
    expect(src).toContain("-->");
    expect(src).toContain(":::crit");
  });
});
