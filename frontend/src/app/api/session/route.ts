/**
 * Session route handler. Exchanges email/password for an access token via the
 * backend and stores it in an **httpOnly** cookie, so the token never appears in
 * a URL (issue 0005). DELETE clears the session.
 */
import { NextResponse } from "next/server";

const COOKIE = "ac_token";

function apiBase(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  );
}

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
  const tokens = (await res.json()) as { access_token: string };
  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE, tokens.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    // Matches the backend access-token TTL, which is configurable via
    // ACCESS_TOKEN_TTL_SECONDS (server-side env; falls back to 15 minutes).
    maxAge: Number(process.env.ACCESS_TOKEN_TTL_SECONDS ?? 60 * 15),
  });
  return response;
}

export async function DELETE(): Promise<NextResponse> {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(COOKIE);
  return response;
}
