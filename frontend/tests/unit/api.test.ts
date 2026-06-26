import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/lib/api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("parses a successful health response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ status: "ok", version: "0.1.0" }), {
          status: 200,
        }),
      ),
    );
    const health = await api.health("http://test");
    expect(health.status).toBe("ok");
    expect(health.version).toBe("0.1.0");
  });

  it("throws ApiError on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("nope", { status: 503 })),
    );
    await expect(api.ready("http://test")).rejects.toBeInstanceOf(ApiError);
  });
});
