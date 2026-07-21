/**
 * Authenticated JSON proxy: browser -> Next -> backend `/api/v1/*`.
 *
 * Client components cannot read the httpOnly `ac_token` session cookie (by
 * design — issue 0005), so governed write actions (plan approve/reject, start,
 * halt, approval decisions) go through this handler, which attaches the Bearer
 * token server-side. The proxy grants nothing the caller's own token does not
 * already grant; it is plumbing, not privilege.
 *
 * Only `/api/v1/...` paths are reachable, and only JSON travels either way.
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

async function forward(
  request: Request,
  params: Promise<{ path: string[] }>,
  method: "GET" | "POST",
): Promise<NextResponse> {
  const { path } = await params;
  const cookieHeader = request.headers.get("cookie") ?? "";
  const token = cookieHeader
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${COOKIE}=`))
    ?.slice(COOKIE.length + 1);
  if (!token) {
    return NextResponse.json({ error: "not signed in" }, { status: 401 });
  }
  const segments = path.map((segment) => encodeURIComponent(segment)).join("/");
  const search = new URL(request.url).search;
  const headers: Record<string, string> = {
    accept: "application/json",
    authorization: `Bearer ${token}`,
  };
  const init: RequestInit = { method, headers, cache: "no-store" };
  if (method === "POST") {
    headers["content-type"] = "application/json";
    init.body = await request.text();
  }
  const res = await fetch(`${apiBase()}/api/v1/${segments}${search}`, init);
  const text = await res.text();
  return new NextResponse(text || "{}", {
    status: res.status,
    headers: { "content-type": "application/json" },
  });
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
