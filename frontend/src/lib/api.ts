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

async function getJson<T>(path: string, base = apiBaseUrl()): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(`GET ${path} failed`, res.status);
  }
  return (await res.json()) as T;
}

export const api = {
  health: (base?: string) => getJson<HealthStatus>("/healthz", base),
  ready: (base?: string) => getJson<ReadyStatus>("/readyz", base),
  meta: (base?: string) => getJson<ApiMeta>("/api/v1/meta", base),
};
