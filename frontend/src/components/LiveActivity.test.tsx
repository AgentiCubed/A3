import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LiveActivity } from "./LiveActivity";

function sseResponse(frames: string): Response {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(frames));
      // stream stays open (no close) so the hook remains in "live" state
    },
  });
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

describe("LiveActivity", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows events streamed from the project feed", async () => {
    const frame =
      "event: task.transition\n" +
      'data: {"action":"task.transition","entity_type":"Task","entity_id":"t1",' +
      '"actor_type":"system","occurred_at":"2026-07-16T20:00:00Z","payload":{"status":"running"}}\n\n';
    vi.spyOn(globalThis, "fetch").mockResolvedValue(sseResponse(frame));

    render(<LiveActivity projectId="p1" />);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveAttribute("data-stream-state", "live");
    });
    await waitFor(() => {
      expect(screen.getByText(/task → running/)).toBeInTheDocument();
    });
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "/api/projects/p1/events",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("reports a disconnected state when the stream cannot start", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("nope", { status: 401 }),
    );

    render(<LiveActivity projectId="p1" />);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveAttribute(
        "data-stream-state",
        "disconnected",
      );
    });
    expect(screen.getByText(/No activity yet/)).toBeInTheDocument();
  });
});
