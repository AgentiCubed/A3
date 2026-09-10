import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProviderReadiness } from "./ProviderReadiness";

describe("ProviderReadiness", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("runs a preflight check and shows a human failure message", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/backend/providers") && (!init || init.method === "GET")) {
        return Response.json({ providers: ["mock", "gemini"] });
      }
      if (url.endsWith("/api/backend/providers/preflight")) {
        return Response.json({
          provider: "gemini",
          ok: false,
          message:
            "Credential missing or malformed — set the provider API key in the runtime environment (provider_http_status=none provider_error_category=authentication)",
          category: "authentication",
          http_status: null,
          diagnostic: "provider_http_status=none provider_error_category=authentication",
          model: null,
        });
      }
      return Response.json({ error: "unexpected" }, { status: 500 });
    });

    render(<ProviderReadiness defaultProvider="gemini" />);
    await waitFor(() => expect(screen.getByLabelText("Provider")).toBeTruthy());
    fireEvent.click(screen.getByText("Verify provider"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/Credential missing or malformed/);
      expect(screen.getByRole("status")).toHaveAttribute("data-preflight-ok", "false");
    });
  });

  it("shows ready state on a successful mock preflight", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/backend/providers")) {
        return Response.json({ providers: ["mock"] });
      }
      if (url.endsWith("/api/backend/providers/preflight")) {
        return Response.json({
          provider: "mock",
          ok: true,
          message: "Mock provider is ready (deterministic, no network).",
          category: null,
          http_status: null,
          diagnostic: null,
          model: "mock",
        });
      }
      return Response.json({}, { status: 500 });
    });

    render(<ProviderReadiness defaultProvider="mock" />);
    await waitFor(() => expect(screen.getByLabelText("Provider")).toBeTruthy());
    fireEvent.click(screen.getByText("Verify provider"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/Ready/);
      expect(screen.getByRole("status")).toHaveAttribute("data-preflight-ok", "true");
    });
  });
});
