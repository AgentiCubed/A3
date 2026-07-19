/**
 * SSE proxy for the live project event stream.
 *
 * Browsers cannot attach an Authorization header to a streaming request from
 * EventSource/fetch without exposing the token to page script, so this route
 * reads the httpOnly `ac_token` cookie (issue 0005) and relays the backend
 * `text/event-stream` through unchanged.
 */
import { cookies } from "next/headers";

function apiBase(): string {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  );
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  const token = (await cookies()).get("ac_token")?.value;
  if (!token) {
    return new Response("not signed in", { status: 401 });
  }

  const upstream = await fetch(`${apiBase()}/api/v1/projects/${id}/events`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" },
    cache: "no-store",
  });
  if (!upstream.ok || upstream.body === null) {
    return new Response("event stream unavailable", { status: upstream.status || 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
