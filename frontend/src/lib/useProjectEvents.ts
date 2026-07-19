"use client";

/**
 * Live project events over the same-origin SSE proxy (/api/projects/[id]/events).
 *
 * Streams via fetch + SseParser (see lib/sse.ts for why not EventSource) and
 * keeps a bounded, newest-first list of events. Reconnects with a fixed delay;
 * the stream is advisory, so a dropped connection only pauses the live view —
 * the dashboard's server-rendered data remains the source of truth.
 */

import { useEffect, useRef, useState } from "react";
import { SseParser } from "./sse";

export interface ProjectEvent {
  action: string;
  entity_type: string;
  entity_id: string | null;
  actor_type: string | null;
  occurred_at: string;
  payload: Record<string, unknown>;
}

export type StreamState = "connecting" | "live" | "disconnected";

const MAX_EVENTS = 20;
const RECONNECT_MS = 3000;

export function useProjectEvents(projectId: string): {
  events: ProjectEvent[];
  state: StreamState;
} {
  const [events, setEvents] = useState<ProjectEvent[]>([]);
  const [state, setState] = useState<StreamState>("connecting");
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function connect(): Promise<void> {
      try {
        const res = await fetch(`/api/projects/${projectId}/events`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (!res.ok || res.body === null) throw new Error(`stream ${res.status}`);
        setState("live");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        const parser = new SseParser();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          for (const frame of parser.push(decoder.decode(value, { stream: true }))) {
            try {
              const event = JSON.parse(frame.data) as ProjectEvent;
              setEvents((prev) => [event, ...prev].slice(0, MAX_EVENTS));
            } catch {
              // malformed frame: skip, keep the stream alive
            }
          }
        }
        throw new Error("stream ended");
      } catch {
        if (stopped.current) return;
        setState("disconnected");
        timer = setTimeout(() => {
          setState("connecting");
          void connect();
        }, RECONNECT_MS);
      }
    }

    void connect();
    return () => {
      stopped.current = true;
      controller.abort();
      if (timer !== undefined) clearTimeout(timer);
    };
  }, [projectId]);

  return { events, state };
}
