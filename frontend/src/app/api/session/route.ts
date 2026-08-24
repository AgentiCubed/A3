/**
 * Session route handler. Exchanges email/password for the backend's token
 * pair and stores BOTH tokens in **httpOnly** cookies, so neither ever
 * appears in a URL or is readable by page script (issue 0005). The refresh
 * token is what lets the backend proxy renew an expiring session silently —
 * previously it was discarded here, which hard-logged users out every
 * ACCESS_TOKEN_TTL_SECONDS (15 minutes by default). DELETE clears both.
 */
import { NextResponse } from "next/server";

import { apiBase, applySessionCookies, clearSessionCookies } from "@/lib/server-session";

export async function POST(request: Request): Promise<NextResponse> {
  const body = (await request.json()) as { email?: string; password?: string };
  const res = await fetch(`${apiBase()}/api/v1/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: body.email, password: body.password }),
    cache: "no-store",
  });
  if (!res.ok) {
    return NextResponse.json({ error: "invalid credentials" }, { status: 401 });
  }
  const tokens = (await res.json()) as { access_token: string; refresh_token: string };
  const response = NextResponse.json({ ok: true });
  applySessionCookies(response, tokens);
  return response;
}

export async function DELETE(): Promise<NextResponse> {
  const response = NextResponse.json({ ok: true });
  clearSessionCookies(response);
  return response;
}
