import { riskGrid, severityClass } from "@/lib/metrics";

const HEAT: Record<"low" | "medium" | "high", string> = {
  low: "#1f7a3d",
  medium: "#9a6b00",
  high: "#9a1f1f",
};

/** 5x5 likelihood (x) × impact (y) risk heat-matrix. */
export function RiskMatrix({ matrix }: { matrix: Record<string, number> }) {
  const grid = riskGrid(matrix);
  return (
    <table role="table" aria-label="Risk matrix" style={{ borderCollapse: "collapse" }}>
      <tbody>
        {grid.map((row, r) => {
          const impact = 5 - r;
          return (
            <tr key={impact}>
              <th style={{ color: "#9fb0c0", fontSize: 11, padding: 4 }}>I{impact}</th>
              {row.map((count, c) => {
                const likelihood = c + 1;
                return (
                  <td
                    key={likelihood}
                    title={`Likelihood ${likelihood}, Impact ${impact}: ${count}`}
                    style={{
                      width: 34,
                      height: 34,
                      textAlign: "center",
                      color: "white",
                      fontSize: 13,
                      background: count
                        ? HEAT[severityClass(likelihood, impact)]
                        : "#0d1117",
                      border: "1px solid #30363d",
                    }}
                  >
                    {count || ""}
                  </td>
                );
              })}
            </tr>
          );
        })}
        <tr>
          <th />
          {[1, 2, 3, 4, 5].map((l) => (
            <th key={l} style={{ color: "#9fb0c0", fontSize: 11, padding: 4 }}>
              L{l}
            </th>
          ))}
        </tr>
      </tbody>
    </table>
  );
}
