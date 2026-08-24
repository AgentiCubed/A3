/**
 * Server-side session plumbing shared by the session route and the backend
 * proxy: httpOnly cookie names, TTLs, and the silent-refresh call.
 *
 * Two cookies, both httpOnly (the browser never scripts against either):
 *  - `ac_token`  — the short-lived access token; expires with the backend TTL.
 *  - `ac_refresh` — the refresh token; lets the proxy renew a session
 *    transparently instead of hard-logging users out every 15 minutes.
 */
import type { NextResponse } from "next/server";

export const ACCESS_COOKIE = "ac_token";
export const REFRESH_COOKIE = "ac_refresh";

export function apiBase(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  );
}

export function accessTtlSeconds(): number {
  return Number(process.env.ACCESS_TOKEN_TTL_SECONDS ?? 60 * 15);
}

export function refreshTtlSeconds(): number {
  return Number(process.env.REFRESH_TOKEN_TTL_SECONDS ?? 60 * 60 * 24 * 14);
}

export function readCookie(cookieHeader: string, name: string): string | undefined {
  return cookieHeader
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

/** Exchange a refresh token for a fresh pair; null on any failure. */
export async function refreshTokens(refreshToken: string): Promise<TokenPair | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const tokens = (await res.json()) as Partial<TokenPair>;
    if (!tokens.access_token || !tokens.refresh_token) return null;
    return tokens as TokenPair;
  } catch {
    return null;
  }
}

/** Set both session cookies on an outgoing response. */
export function applySessionCookies(response: NextResponse, tokens: TokenPair): void {
  const common = {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
  };
  response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    ...common,
    maxAge: accessTtlSeconds(),
  });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    ...common,
    maxAge: refreshTtlSeconds(),
  });
}

export function clearSessionCookies(response: NextResponse): void {
  response.cookies.delete(ACCESS_COOKIE);
  response.cookies.delete(REFRESH_COOKIE);
}
