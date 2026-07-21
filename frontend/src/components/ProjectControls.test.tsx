import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProjectControls } from "./ProjectControls";

const RUNNING_PROJECT = {
  id: "p1",
  name: "P",
  objective: "o",
  status: "active",
  halted_at: null,
};

const HALTED_PROJECT = { ...RUNNING_PROJECT, halted_at: "2026-07-19T12:00:00Z" };

type FetchArgs = { url: string; init?: RequestInit };

function mockBackend(
  projects: unknown[],
  onPost?: (call: FetchArgs) => Response | undefined,
): FetchArgs[] {
  const calls: FetchArgs[] = [];
  let reads = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    calls.push({ url, init });
    if (init?.method === "POST" && onPost) {
      const custom = onPost({ url, init });
      if (custom) return custom;
    }
    if (!init?.method || init.method === "GET") {
      const body = projects[Math.min(reads, projects.length - 1)];
      reads += 1;
      return Response.json(body);
    }
    return Response.json({ engine: "inline", tasks: [] });
  });
  return calls;
}

describe("ProjectControls", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts the project and reports the outcome", async () => {
    const calls = mockBackend([RUNNING_PROJECT], ({ url }) => {
      if (url.includes("/start")) {
        return Response.json({
          engine: "inline",
          tasks: [
            { task_id: "t1", status: "completed" },
            { task_id: "t2", status: "completed" },
          ],
        });
      }
      return undefined;
    });
    render(<ProjectControls projectId="p1" />);
    await waitFor(() => expect(screen.getByText("Start")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Start"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        /2 task\(s\) ran to completion/,
      );
    });
    expect(
      calls.some(
        (c) =>
          c.url.endsWith("/api/backend/projects/p1/start") && c.init?.method === "POST",
      ),
    ).toBe(true);
  });

  it("surfaces a start refusal (plan approval required) as an outcome", async () => {
    mockBackend([RUNNING_PROJECT], ({ url }) => {
      if (url.includes("/start")) {
        return Response.json(
          { detail: { error: "plan_approval_required" } },
          { status: 409 },
        );
      }
      return undefined;
    });
    render(<ProjectControls projectId="p1" />);
    await waitFor(() => expect(screen.getByText("Start")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Start"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/plan_approval_required/);
    });
  });

  it("halts with the operator's reason and flips to a Resume control", async () => {
    const calls = mockBackend([RUNNING_PROJECT, HALTED_PROJECT], ({ url }) => {
      if (url.includes("/halt")) {
        return Response.json({ project_id: "p1", status: "active", halted_at: "now" });
      }
      return undefined;
    });
    render(<ProjectControls projectId="p1" />);
    await waitFor(() => expect(screen.getByText("Halt")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Halt reason"), {
      target: { value: "pausing for review" },
    });
    fireEvent.click(screen.getByText("Halt"));

    await waitFor(() => expect(screen.getByText("Resume")).toBeInTheDocument());
    expect(screen.queryByText("Start")).not.toBeInTheDocument();
    expect(screen.getByTestId("project-state")).toHaveTextContent(/HALTED/);

    const haltCall = calls.find((c) => c.url.includes("/halt"));
    expect(JSON.parse(String(haltCall?.init?.body))).toEqual({
      reason: "pausing for review",
    });
  });

  it("resumes a halted project and reports what picked back up", async () => {
    mockBackend([HALTED_PROJECT, RUNNING_PROJECT], ({ url }) => {
      if (url.includes("/resume")) {
        return Response.json({
          engine: "celery",
          tasks: [{ task_id: "t2", status: "queued" }],
        });
      }
      return undefined;
    });
    render(<ProjectControls projectId="p1" />);
    await waitFor(() => expect(screen.getByText("Resume")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Resume"));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/1 task\(s\) picked back up/);
    });
    await waitFor(() => expect(screen.getByText("Start")).toBeInTheDocument());
  });
});
