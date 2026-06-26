import { HealthBadge, type HealthState } from "@/components/HealthBadge";
import { api, type ApiMeta, type ReadyStatus } from "@/lib/api";

// Server component. Runs on the Next server, so it can reach the API over the
// internal compose network. Falls back gracefully if the API is not up yet.
async function loadStatus(): Promise<{
  state: HealthState;
  ready: ReadyStatus | null;
  meta: ApiMeta | null;
}> {
  const base = process.env.INTERNAL_API_BASE_URL ?? undefined;
  try {
    const [ready, meta] = await Promise.all([api.ready(base), api.meta(base)]);
    const state: HealthState = ready.status === "ok" ? "ok" : "degraded";
    return { state, ready, meta };
  } catch {
    return { state: "unknown", ready: null, meta: null };
  }
}

export default async function Home() {
  const { state, ready, meta } = await loadStatus();

  return (
    <main style={{ maxWidth: 920, margin: "0 auto", padding: "48px 24px" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h1 style={{ margin: 0, fontSize: 28 }}>AgentiCubed</h1>
        <HealthBadge state={state} />
      </header>
      <p style={{ color: "#9fb0c0" }}>
        Agentic project-orchestration platform. Plan → Assign → Execute →
        Evaluate → Identify Gaps → Remediate → Re-execute.
      </p>

      <section style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18 }}>API readiness</h2>
        {ready ? (
          <ul>
            {Object.entries(ready.checks).map(([k, v]) => (
              <li key={k}>
                <strong>{k}:</strong> {v}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: "#9a6b00" }}>
            API not reachable yet. Start the stack with <code>make up</code>.
          </p>
        )}
      </section>

      {meta && (
        <section style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18 }}>Modules (v{meta.version})</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {meta.modules.map((m) => (
              <span
                key={m}
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  background: "#161b22",
                  border: "1px solid #30363d",
                  fontSize: 13,
                }}
              >
                {m}
              </span>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
