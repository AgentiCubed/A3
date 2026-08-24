/**
 * Authenticated JSON proxy: browser -> Next -> backend `/api/v1/*`.
 *
 * Client components cannot read the httpOnly session cookies (by design —
 * issue 0005), so governed actions go through this handler, which attaches
 * the token server-side. The proxy grants nothing the caller's own
 * token does not already grant; it is plumbing, not privilege.
 *
 * Silent refresh: when the access token is missing or the backend answers
 * 401 and a refresh token is present, the proxy renews the pair via
 * `/auth/refresh`, retries the original request exactly once, and rotates
 * both cookies on the response. Users stop being hard-logged-out every
 * 15 minutes; a genuinely dead session still falls through to 401.
 *
 * Only `/api/v1/...` paths are reachable, and only JSON travels either way.
 */
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  apiBase,
  applySessionCookies,
  clearSessionCookies,
  readCookie,
  refreshTokens,
  type TokenPair,
} from "@/lib/server-session";

async function callBackend(
  url: string,
  method: "GET" | "POST",
  token: string,
  body: string | undefined,
): Promise<Response> {
  const headers: Record<string, string> = {
    accept: "application/json",
    authorization: ["Bearer", token].join(" "),
  };
  const init: RequestInit = { method, headers, cache: "no-store" };
  if (method === "POST") {
    headers["content-type"] = "application/json";
    init.body = body ?? "";
  }
  return fetch(url, init);
}

async function forward(
  request: Request,
  params: Promise<{ path: string[] }>,
  method: "GET" | "POST",
): Promise<NextResponse> {
  const { path } = await params;
  const cookieHeader = request.headers.get("cookie") ?? "";
  let token = readCookie(cookieHeader, ACCESS_COOKIE);
  const refreshToken = readCookie(cookieHeader, REFRESH_COOKIE);

  // The request body is read once up front: a retry after refresh needs it a
  // second time, and Request bodies are single-use streams.
  const body = method === "POST" ? await request.text() : undefined;

  let renewed: TokenPair | null = null;
  let refreshFailed = false;
  if (!token && refreshToken) {
    renewed = await refreshTokens(refreshToken);
    refreshFailed = !renewed;
    token = renewed?.access_token;
  }
  if (!token) {
    const response = NextResponse.json({ error: "not signed in" }, { status: 401 });
    if (refreshFailed) {
      clearSessionCookies(response);
    }
    return response;
  }

  const segments = path.map((segment) => encodeURIComponent(segment)).join("/");
  const search = new URL(request.url).search;
  const url = `${apiBase()}/api/v1/${segments}${search}`;

  let res = await callBackend(url, method, token, body);
  if (res.status === 401 && refreshToken && !renewed) {
    renewed = await refreshTokens(refreshToken);
    refreshFailed = !renewed;
    if (renewed) {
      res = await callBackend(url, method, renewed.access_token, body);
    }
  }

  const text = await res.text();
  const response = new NextResponse(text || "{}", {
    status: res.status,
    headers: { "content-type": "application/json" },
  });
  if (renewed) {
    applySessionCookies(response, renewed);
  } else if (refreshFailed) {
    clearSessionCookies(response);
  }
  return response;
}

export async function GET(
  request: Request,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  return forward(request, ctx.params, "GET");
}

export async function POST(
  request: Request,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  return forward(request, ctx.params, "POST");
}
