"use client";

import { useState } from "react";

/** Minimal login form. Posts to /api/session, which sets an httpOnly cookie. */
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const res = await fetch("/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setBusy(false);
    if (res.ok) {
      window.location.href = "/";
    } else {
      setError("Invalid email or password.");
    }
  }

  return (
    <main style={{ maxWidth: 360, margin: "80px auto", padding: "0 24px" }}>
      <h1 style={{ fontSize: 22 }}>Sign in</h1>
      <form
        onSubmit={submit}
        style={{ display: "flex", flexDirection: "column", gap: 12 }}
      >
        <input
          type="email"
          placeholder="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />
        <input
          type="password"
          placeholder="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />
        <button type="submit" disabled={busy} style={buttonStyle}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        {error && <p style={{ color: "#ff6b6b", fontSize: 13 }}>{error}</p>}
      </form>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 6,
  border: "1px solid #30363d",
  background: "#0d1117",
  color: "#e6edf3",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 6,
  border: "none",
  background: "#2f6fed",
  color: "white",
  fontWeight: 600,
  cursor: "pointer",
};
