/**
 * Typed AgentiCubed API client.
 *
 * Thin wrapper over fetch. No provider/vendor specifics leak here — this only
 * knows about the AgentiCubed REST surface. Server components pass an internal
 * base URL; client components use NEXT_PUBLIC_API_BASE_URL.
 */

export interface HealthStatus {
  status: string;
  version: string;
}

export interface ReadyStatus {
  status: string;
  checks: Record<string, string>;
}

export interface ApiMeta {
  api: string;
  version: string;
  modules: string[];
}

export interface TaskSchedule {
  task_id: string;
  earliest_start: number;
  earliest_finish: number;
  slack: number;
  is_critical: boolean;
}

export interface AgentMetricRow {
  agent_id: string;
  agent_name: string;
  metrics: Record<string, number>;
}

export interface Dashboard {
  metrics: Record<string, number>;
  status_breakdown: Record<string, number>;
  agent_metrics: AgentMetricRow[];
  risk_matrix: Record<string, number>;
  timeline: {
    project_duration: number;
    critical_path: string[];
    schedules: TaskSchedule[];
  };
}

export interface GraphNode {
  id: string;
  title: string;
  is_critical: boolean;
}

export interface GraphEdge {
  predecessor_task_id: string;
  successor_task_id: string;
  dependency_type: string;
  lag_hours: number;
}

export interface ProjectGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

async function getJson<T>(path: string, base = apiBaseUrl(), token?: string): Promise<T> {
  const headers: Record<string, string> = { accept: "application/json" };
  if (token) {
    headers.authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${base}${path}`, { headers, cache: "no-store" });
  if (!res.ok) {
    throw new ApiError(`GET ${path} failed`, res.status);
  }
  return (await res.json()) as T;
}

export const api = {
  health: (base?: string) => getJson<HealthStatus>("/healthz", base),
  ready: (base?: string) => getJson<ReadyStatus>("/readyz", base),
  meta: (base?: string) => getJson<ApiMeta>("/api/v1/meta", base),
  dashboard: (projectId: string, token: string, base?: string) =>
    getJson<Dashboard>(`/api/v1/projects/${projectId}/dashboard`, base, token),
  projectGraph: (projectId: string, token: string, base?: string) =>
    getJson<ProjectGraph>(`/api/v1/projects/${projectId}/graph`, base, token),
};
