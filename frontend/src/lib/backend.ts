/**
 * Client-side helper for governed backend calls through the authenticated
 * proxy (`/api/backend/...`). Returns status + parsed body instead of
 * throwing, so components can render 409 governance refusals (active draft,
 * version drift, halted project) as first-class outcomes, not crashes.
 */

export interface BackendResult<T> {
  ok: boolean;
  status: number;
  body: T;
}

export async function backend<T = unknown>(
  path: string,
  init?: { method?: "GET" | "POST"; body?: unknown },
): Promise<BackendResult<T>> {
  const res = await fetch(`/api/backend/${path}`, {
    method: init?.method ?? "GET",
    headers:
      init?.body !== undefined ? { "content-type": "application/json" } : undefined,
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
    cache: "no-store",
  });
  let body: T;
  try {
    body = (await res.json()) as T;
  } catch {
    body = {} as T;
  }
  return { ok: res.ok, status: res.status, body };
}

/** Human-readable message out of a FastAPI error payload. */
export function errorDetail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object") {
      const record = detail as Record<string, unknown>;
      const parts = [record.error, record.reason, record.hint].filter(
        (part): part is string => typeof part === "string",
      );
      if (parts.length > 0) return parts.join(" — ");
      return JSON.stringify(detail);
    }
  }
  return "request failed";
}

// ── Types mirroring the backend schemas (fields the UI consumes) ─────────
export interface AgentSummary {
  id: string;
  name: string;
  kind: string;
  provider: string | null;
}

export interface PlanCriterion {
  key?: string;
  check?: string;
  params?: Record<string, unknown>;
}

export interface PlanTask {
  key: string;
  title: string;
  description: string;
  estimate_hours: number;
  required_capabilities: string[];
  priority: number;
  acceptance_criteria: PlanCriterion[];
}

export interface PlanDependency {
  predecessor_key: string;
  successor_key: string;
}

export interface PlanSpec {
  tasks: PlanTask[];
  dependencies: PlanDependency[];
  project_acceptance: Record<string, unknown>;
  assumptions: string[];
  warnings: string[];
}

export interface DecompositionPlan {
  id: string;
  project_id: string;
  status: "draft" | "approved" | "rejected" | "invalid" | string;
  version: number;
  objective: string;
  plan_spec: PlanSpec | null;
  plan_spec_sha256: string | null;
  error_code: string | null;
  diagnostic: string | null;
  decision_comment: string | null;
  created_at: string;
}

export interface ProjectInfo {
  id: string;
  name: string;
  objective: string;
  status: string;
  halted_at: string | null;
}

export interface StartedTask {
  task_id: string;
  status: string;
}

export interface StartResult {
  engine: string;
  tasks: StartedTask[];
}

export interface ApprovalInfo {
  id: string;
  project_id: string;
  task_execution_id: string | null;
  requested_action: string;
  risk_level: string;
  status: string;
  comment: string | null;
  decided_at: string | null;
}
