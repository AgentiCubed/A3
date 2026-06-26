/**
 * Presentational status badge. Pure function of props so it is trivially
 * testable without network or async. Used by the dashboard to render API health.
 */

export type HealthState = "ok" | "degraded" | "unknown";

const STYLES: Record<HealthState, { bg: string; label: string }> = {
  ok: { bg: "#1f7a3d", label: "Operational" },
  degraded: { bg: "#9a6b00", label: "Degraded" },
  unknown: { bg: "#6b7280", label: "Unknown" },
};

export function HealthBadge({ state }: { state: HealthState }) {
  const style = STYLES[state] ?? STYLES.unknown;
  return (
    <span
      role="status"
      data-state={state}
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 999,
        background: style.bg,
        color: "white",
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {style.label}
    </span>
  );
}
