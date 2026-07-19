/**
 * Minimal SSE frame parser for fetch-streamed `text/event-stream` bodies.
 *
 * Used instead of EventSource because the backend emits *named* events
 * (`event: task.transition`, `event: approval.requested`, …) with an open
 * vocabulary; EventSource only surfaces names registered up front.
 */

export interface SseFrame {
  event: string;
  data: string;
}

/**
 * Incremental parser: feed it chunks, it returns completed frames.
 * Comment lines (`: keep-alive`) are ignored per the SSE spec.
 */
export class SseParser {
  private buffer = "";

  push(chunk: string): SseFrame[] {
    this.buffer += chunk;
    const frames: SseFrame[] = [];
    let sep: number;
    while ((sep = this.buffer.indexOf("\n\n")) !== -1) {
      const raw = this.buffer.slice(0, sep);
      this.buffer = this.buffer.slice(sep + 2);
      const frame = parseFrame(raw);
      if (frame) frames.push(frame);
    }
    return frames;
  }
}

function parseFrame(raw: string): SseFrame | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith(":")) continue; // comment / heartbeat
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}
