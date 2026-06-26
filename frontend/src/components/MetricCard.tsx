/** A single labelled metric tile. Pure presentational. */
export function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      style={{
        background: "#161b22",
        border: "1px solid #30363d",
        borderRadius: 8,
        padding: "14px 16px",
        minWidth: 140,
      }}
    >
      <div style={{ fontSize: 12, color: "#9fb0c0" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: accent ?? "#e6edf3" }}>
        {value}
      </div>
    </div>
  );
}
