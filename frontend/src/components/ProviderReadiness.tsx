"use client";

/**
 * Operator-facing provider preflight (MVP A3). Runs a cheap credential +
 * endpoint check without starting project work, so a missing or bad API key
 * is caught before a live run fails mid-loop.
 */

import { useCallback, useEffect, useState } from "react";
import { backend, errorDetail } from "@/lib/backend";

interface PreflightResult {
  provider: string;
  ok: boolean;
  message: string;
  category: string | null;
  http_status: number | null;
  diagnostic: string | null;
  model: string | null;
}

const buttonStyle: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: 6,
  border: "1px solid #4a5568",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
};

export function ProviderReadiness({
  defaultProvider = "gemini",
}: {
  defaultProvider?: string;
}) {
  const [providers, setProviders] = useState<string[]>([
    defaultProvider,
    "mock",
    "ollama",
  ]);
  const [provider, setProvider] = useState(defaultProvider);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PreflightResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [signedIn, setSignedIn] = useState(true);

  const loadProviders = useCallback(async () => {
    const res = await backend<{ providers: string[] }>("providers");
    if (res.status === 401) {
      setSignedIn(false);
      return;
    }
    if (res.ok && Array.isArray(res.body.providers) && res.body.providers.length > 0) {
      const names = res.body.providers;
      setProviders(names);
      setProvider((current) => (names.includes(current) ? current : names[0]));
    }
  }, []);

  useEffect(() => {
    void loadProviders();
  }, [loadProviders]);

  async function runCheck() {
    setBusy(true);
    setError(null);
    setResult(null);
    const res = await backend<PreflightResult>("providers/preflight", {
      method: "POST",
      body: { provider },
    });
    setBusy(false);
    if (res.status === 401) {
      setSignedIn(false);
      setError("Sign in to verify provider credentials.");
      return;
    }
    if (!res.ok) {
      setError(errorDetail(res.body));
      return;
    }
    setResult(res.body);
  }

  return (
    <section data-testid="provider-readiness" style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 18 }}>Provider readiness</h2>
      <p style={{ color: "#9fb0c0", fontSize: 14, marginTop: 4 }}>
        Verify the live-model credential and endpoint before starting a project. This does
        not create work or spend a project attempt.
      </p>
      {!signedIn ? (
        <p style={{ color: "#e0883a", fontSize: 13 }}>
          Sign in to run a provider preflight check.
        </p>
      ) : (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <label style={{ fontSize: 13 }}>
            Provider{" "}
            <select
              aria-label="Provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              style={{ marginLeft: 6, padding: 6 }}
            >
              {providers.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => void runCheck()}
            disabled={busy}
            style={buttonStyle}
          >
            {busy ? "Checking…" : "Verify provider"}
          </button>
        </div>
      )}
      {error && (
        <p role="alert" style={{ color: "#e0883a", fontSize: 13 }}>
          {error}
        </p>
      )}
      {result && (
        <p
          role="status"
          data-preflight-ok={result.ok ? "true" : "false"}
          style={{
            color: result.ok ? "#5ad17a" : "#e0883a",
            fontSize: 13,
            marginTop: 10,
          }}
        >
          {result.ok ? "Ready — " : "Not ready — "}
          {result.message}
        </p>
      )}
    </section>
  );
}
