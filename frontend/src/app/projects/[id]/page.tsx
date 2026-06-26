import { cookies } from "next/headers";
import Link from "next/link";
import { AgentTable } from "@/components/AgentTable";
import { DependencyDiagram } from "@/components/DependencyDiagram";
import { GanttChart } from "@/components/GanttChart";
import { MetricCard } from "@/components/MetricCard";
import { RiskMatrix } from "@/components/RiskMatrix";
import { api, type Dashboard, type ProjectGraph } from "@/lib/api";
import { pct } from "@/lib/metrics";

// Server component. Auth comes from the httpOnly `ac_token` session cookie set by
// /api/session (see /login). A `?token=` query param is still accepted as a
// fallback for scripted/demo access. (Issue 0005.)
export default async function ProjectDashboard({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ token?: string }>;
}) {
  const { id } = await params;
  const { token: queryToken } = await searchParams;
  const cookieToken = (await cookies()).get("ac_token")?.value;
  const token = cookieToken ?? queryToken;

  if (!token) {
    return (
      <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px" }}>
        <h1>Project dashboard</h1>
        <p style={{ color: "#9a6b00" }}>
          You are not signed in. <Link href="/login">Sign in</Link> to view this
          dashboard.
        </p>
      </main>
    );
  }

  const base = process.env.INTERNAL_API_BASE_URL;
  let dash: Dashboard;
  let graph: ProjectGraph;
  try {
    [dash, graph] = await Promise.all([
      api.dashboard(id, token, base),
      api.projectGraph(id, token, base),
    ]);
  } catch {
    return (
      <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px" }}>
        <h1>Project dashboard</h1>
        <p style={{ color: "#9a1f1f" }}>
          Could not load this project (not found, or the token is invalid/expired).
        </p>
      </main>
    );
  }

  const m = dash.metrics;
  const titles = Object.fromEntries(graph.nodes.map((n) => [n.id, n.title]));

  return (
    <main style={{ maxWidth: 1040, margin: "0 auto", padding: "40px 24px" }}>
      <h1 style={{ marginTop: 0 }}>Project dashboard</h1>

      <section style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <MetricCard
          label="Completion"
          value={pct(m.completion_rate ?? 0)}
          accent="#5ad17a"
        />
        <MetricCard
          label="Tasks"
          value={`${m.tasks_completed ?? 0}/${m.tasks_total ?? 0}`}
        />
        <MetricCard label="Exec success" value={pct(m.execution_success_rate ?? 0)} />
        <MetricCard label="Eval pass" value={pct(m.evaluation_pass_rate ?? 0)} />
        <MetricCard label="Avg score" value={(m.avg_evaluation_score ?? 0).toFixed(2)} />
        <MetricCard
          label="Open risks"
          value={m.open_risks ?? 0}
          accent={(m.open_risks ?? 0) > 0 ? "#e0883a" : undefined}
        />
        <MetricCard
          label="Pending approvals"
          value={m.pending_approvals ?? 0}
          accent={(m.pending_approvals ?? 0) > 0 ? "#e0883a" : undefined}
        />
      </section>

      <section style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18 }}>Timeline (critical path)</h2>
        <GanttChart
          schedules={dash.timeline.schedules}
          projectDuration={dash.timeline.project_duration}
          titles={titles}
        />
      </section>

      <div style={{ display: "flex", gap: 32, flexWrap: "wrap", marginTop: 32 }}>
        <section style={{ flex: "1 1 360px" }}>
          <h2 style={{ fontSize: 18 }}>Agent performance</h2>
          <AgentTable rows={dash.agent_metrics} />
        </section>
        <section>
          <h2 style={{ fontSize: 18 }}>Risk matrix</h2>
          <RiskMatrix matrix={dash.risk_matrix} />
        </section>
      </div>

      <section style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18 }}>Dependencies</h2>
        <DependencyDiagram graph={graph} />
      </section>
    </main>
  );
}
