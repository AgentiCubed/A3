import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/backend/[...path]/route";

const context = {
  params: Promise.resolve({ path: ["projects"] }),
};

function requestWithCookies(cookie: string): Request {
  return new Request("http://frontend.test/api/backend/projects", {
    headers: { cookie },
  });
}

function expectSessionCookiesCleared(response: Response): void {
  const setCookie = response.headers.get("set-cookie") ?? "";
  expect(setCookie).toContain("ac_token=;");
  expect(setCookie).toContain("ac_refresh=;");
}

describe("backend proxy refresh failure", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("clears both cookies when refreshing a missing access token fails", async () => {
    const fetchMock = vi.fn(async () => new Response("{}", { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(requestWithCookies("ac_refresh=dead-refresh"), context);

    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectSessionCookiesCleared(response);
  });

  it("clears both cookies when refresh fails after a backend 401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response('{"detail":"expired"}', { status: 401 }))
      .mockResolvedValueOnce(new Response("{}", { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      requestWithCookies("ac_token=expired-access; ac_refresh=dead-refresh"),
      context,
    );

    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expectSessionCookiesCleared(response);
  });
});
