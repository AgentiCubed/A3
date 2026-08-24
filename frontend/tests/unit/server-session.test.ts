import { afterEach, describe, expect, it, vi } from "vitest";

import { readCookie, refreshTokens } from "@/lib/server-session";

describe("readCookie", () => {
  it("extracts a named cookie from a header with several", () => {
    const header = "theme=dark; ac_token=abc.def.ghi; ac_refresh=jkl.mno";
    expect(readCookie(header, "ac_token")).toBe("abc.def.ghi");
    expect(readCookie(header, "ac_refresh")).toBe("jkl.mno");
  });

  it("returns undefined when absent, and does not prefix-match other names", () => {
    // `ac_token` must not match `ac_token_old` or a name that merely starts
    // the same way; startsWith on "name=" guarantees that.
    const header = "ac_token_old=stale; other=1";
    expect(readCookie(header, "ac_token")).toBeUndefined();
    expect(readCookie("", "ac_token")).toBeUndefined();
  });
});

describe("refreshTokens", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the new pair on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({ access_token: "new-access", refresh_token: "new-refresh" }),
          { status: 200 },
        ),
      ),
    );
    const pair = await refreshTokens("old-refresh");
    expect(pair).toEqual({ access_token: "new-access", refresh_token: "new-refresh" });
  });

  it("returns null on 401 — a dead refresh token means signed out, not a crash", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 401 })));
    expect(await refreshTokens("dead")).toBeNull();
  });

  it("returns null on a malformed body or network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ access_token: "only-half" }), {
        status: 200,
      })),
    );
    expect(await refreshTokens("r")).toBeNull();

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("connection refused");
      }),
    );
    expect(await refreshTokens("r")).toBeNull();
  });
});
