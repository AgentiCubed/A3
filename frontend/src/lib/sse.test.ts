import { describe, expect, it } from "vitest";
import { SseParser } from "./sse";

describe("SseParser", () => {
  it("parses a complete named frame", () => {
    const parser = new SseParser();
    const frames = parser.push('event: task.transition\ndata: {"a":1}\n\n');
    expect(frames).toEqual([{ event: "task.transition", data: '{"a":1}' }]);
  });

  it("buffers partial frames across chunks", () => {
    const parser = new SseParser();
    expect(parser.push("event: task.tra")).toEqual([]);
    expect(parser.push('nsition\ndata: {"a":1}\n')).toEqual([]);
    expect(parser.push("\n")).toEqual([{ event: "task.transition", data: '{"a":1}' }]);
  });

  it("ignores heartbeat comments", () => {
    const parser = new SseParser();
    expect(parser.push(": connected\n\n: keep-alive\n\n")).toEqual([]);
  });

  it("parses multiple frames in one chunk and defaults the event name", () => {
    const parser = new SseParser();
    const frames = parser.push("data: one\n\ndata: two\n\n");
    expect(frames).toEqual([
      { event: "message", data: "one" },
      { event: "message", data: "two" },
    ]);
  });

  it("joins multi-line data", () => {
    const parser = new SseParser();
    expect(parser.push("data: line1\ndata: line2\n\n")).toEqual([
      { event: "message", data: "line1\nline2" },
    ]);
  });
});
