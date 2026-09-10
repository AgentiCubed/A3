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

/** Allowlisted human copy for provider_error_category values (mirrors backend). */
const PROVIDER_HUMAN: Record<string, string> = {
  authentication:
    "Credential missing or malformed — set the provider API key in the runtime environment",
  authorization: "Provider refused access — check the credential's permissions",
  invalid_request:
    "Provider rejected the request — check the model ID and parameters",
  not_found:
    "Model or endpoint not found — the model ID may be unknown or the provider endpoint was retired",
  rate_limited:
    "Rate limited — wait and retry; the provider quota may be exhausted",
  provider_unavailable: "Provider unavailable — retry shortly or switch providers",
  timeout: "Provider timed out — retry; the model may be overloaded",
  network_error: "Could not reach the provider — check network connectivity",
};

/**
 * Prefer the human explanation when a machine provider diagnostic is present.
 * Already-humanized operator messages (backend operator_message) pass through.
 */
export function humanizeProviderDiagnostic(text: string): string {
  const match = /provider_error_category=([a-z_]+)/.exec(text);
  if (!match) return text;
  const human = PROVIDER_HUMAN[match[1]];
  if (!human) return text;
  if (text.includes(human)) return text;
  const machine = /provider_http_status=(?:none|[1-5][0-9]{2}) provider_error_category=[a-z_]+/.exec(
    text,
  );
  return machine ? `${human} (${machine[0]})` : `${human} — ${text}`;
}

/** Human-readable message out of a FastAPI error payload. */
export function errorDetail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return humanizeProviderDiagnostic(detail);
    if (detail && typeof detail === "object") {
      const record = detail as Record<string, unknown>;
      // `code` and `detail` carry the cause: plan generation returns
      // {error: "plan_generation_failed", code: "planner_error", detail:
      // "provider_http_status=410 provider_error_category=not_found"}.
      // Dropping them showed operators only the generic label while the
      // actual reason sat in the database — the single most expensive
      // diagnostic failure in this project's history. Every field that
      // explains a failure must reach the screen.
      const parts = [
        record.error,
        record.reason,
        record.hint,
        record.code,
        record.detail,
      ]
        .filter((part): part is string => typeof part === "string")
        .map(humanizeProviderDiagnostic);
      if (parts.length > 0) return parts.join(" — ");
      return JSON.stringify(detail);
    }
  }
  // The auth proxy returns `{error: "not signed in"}` on a missing session
  // (frontend/src/app/api/backend/[...path]/route.ts); surface it rather than
  // the generic fallback so an expired session reads as a sign-in prompt.
  if (body && typeof body === "object" && "error" in body) {
    const error = (body as { error: unknown }).error;
    if (typeof error === "string") return humanizeProviderDiagnostic(error);
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
