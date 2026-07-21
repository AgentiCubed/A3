"use client";

/**
 * Minimal governed-project intake: name + objective. The objective is the
 * whole input contract — the planner decomposes it, a human approves the
 * plan, and the loop runs it. This form is where "objective in" begins for
 * the full-loop browser proof (next-steps Step 1 definition of done).
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { backend, errorDetail } from "@/lib/backend";

export function NewProjectForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [objective, setObjective] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const res = await backend<{ id: string }>("projects", {
      method: "POST",
      body: { name, objective },
    });
    setBusy(false);
    if (!res.ok) {
      setError(
        res.status === 401 ? "Sign in to create a project." : errorDetail(res.body),
      );
      return;
    }
    router.push(`/projects/${res.body.id}`);
  }

  return (
    <section data-testid="new-project-form" style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 18 }}>New project</h2>
      <form
        onSubmit={submit}
        style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}
      >
        <input
          aria-label="Project name"
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ padding: 8, flex: "0 1 220px" }}
        />
        <input
          aria-label="Objective"
          placeholder="Objective — what should the loop deliver?"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          required
          style={{ padding: 8, flex: "1 1 320px" }}
        />
        <button
          type="submit"
          disabled={busy || !name || !objective}
          style={{
            padding: "8px 16px",
            borderRadius: 6,
            border: "1px solid #4a5568",
            background: "transparent",
            color: "inherit",
            cursor: "pointer",
          }}
        >
          Create project
        </button>
        {error && (
          <span
            role="alert"
            data-project-form-error
            style={{ color: "#e0883a", fontSize: 13 }}
          >
            {error}
          </span>
        )}
      </form>
    </section>
  );
}
