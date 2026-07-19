import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PlanPanel } from "./PlanPanel";

const AGENTS = [
  { id: "agent-1", name: "Planner", kind: "ai", provider: "mock" },
  { id: "agent-2", name: "Builder", kind: "ai", provider: "mock" },
  { id: "agent-3", name: "Human Harry", kind: "human", provider: null },
];

const DRAFT_PLAN = {
  id: "plan-1",
  project_id: "p1",
  status: "draft",
  version: 1,
  objective: "ship the widget",
  plan_spec: {
    tasks: [
      {
        key: "t1",
        title: "Research widget",
        description: "collect the numbers",
        estimate_hours: 2,
        required_capabilities: [],
        priority: 3,
        acceptance_criteria: [{ key: "has_numbers", check: "contains_all" }],
      },
      {
        key: "t2",
        title: "Write brief",
        description: "",
        estimate_hours: 1,
        required_capabilities: [],
        priority: 3,
        acceptance_criteria: [{ key: "nonempty", check: "non_empty" }],
      },
    ],
    dependencies: [{ predecessor_key: "t1", successor_key: "t2" }],
    project_acceptance: { deliverables: ["brief"] },
    assumptions: ["mock provider"],
    warnings: [],
  },
  plan_spec_sha256: "a".repeat(64),
  error_code: null,
  diagnostic: null,
  decision_comment: null,
  created_at: "2026-07-19T00:00:00Z",
};

type FetchArgs = { url: string; init?: RequestInit };

function mockBackend(
  plans: unknown[],
  onPost?: (call: FetchArgs) => Response | undefined,
): FetchArgs[] {
  const calls: FetchArgs[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    calls.push({ url, init });
    if (init?.method === "POST" && onPost) {
      const custom = onPost({ url, init });
      if (custom) return custom;
    }
    if (url.endsWith("/agents")) {
      return Response.json(AGENTS);
    }
    if (url.includes("/plans") && (!init?.method || init.method === "GET")) {
      return Response.json(plans);
    }
    return Response.json({});
  });
  return calls;
}

describe("PlanPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the draft plan exactly as proposed", async () => {
    mockBackend([DRAFT_PLAN]);
    render(<PlanPanel projectId="p1" />);

    await waitFor(() => {
      expect(screen.getByTestId("plan-draft")).toBeInTheDocument();
    });
    expect(screen.getByText("Research widget")).toBeInTheDocument();
    expect(screen.getByText("Write brief")).toBeInTheDocument();
    expect(screen.getByText(/t1 → t2/)).toBeInTheDocument();
    expect(screen.getByText(/has_numbers/)).toBeInTheDocument();
    // Only AI agents are offered for assignment.
    const executorSelect = screen.getByLabelText("Executor agent");
    expect(executorSelect).not.toHaveTextContent("Human Harry");
  });

  it("approves with the exact version, sha, and per-task assignments", async () => {
    const calls = mockBackend([DRAFT_PLAN]);
    render(<PlanPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("plan-draft")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Executor agent"), {
      target: { value: "agent-2" },
    });
    fireEvent.click(screen.getByText("Approve plan"));

    await waitFor(() => {
      expect(
        calls.some(
          (c) => c.url.includes("/plans/plan-1/approve") && c.init?.method === "POST",
        ),
      ).toBe(true);
    });
    const approveCall = calls.find((c) => c.url.includes("/plans/plan-1/approve"));
    const payload = JSON.parse(String(approveCall?.init?.body));
    expect(payload.expected_version).toBe(1);
    expect(payload.expected_plan_spec_sha256).toBe("a".repeat(64));
    expect(payload.assignments).toEqual([
      { task_key: "t1", agent_id: "agent-2" },
      { task_key: "t2", agent_id: "agent-2" },
    ]);
  });

  it("cannot approve before choosing an executor", async () => {
    mockBackend([DRAFT_PLAN]);
    render(<PlanPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("plan-draft")).toBeInTheDocument();
    });
    expect(screen.getByText("Approve plan")).toBeDisabled();
  });

  it("surfaces a governance refusal instead of pretending success", async () => {
    mockBackend([DRAFT_PLAN], ({ url }) => {
      if (url.includes("/approve")) {
        return Response.json(
          { detail: { error: "plan_version_conflict", hint: "reload the plan" } },
          { status: 409 },
        );
      }
      return undefined;
    });
    render(<PlanPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("plan-draft")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Executor agent"), {
      target: { value: "agent-2" },
    });
    fireEvent.click(screen.getByText("Approve plan"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/plan_version_conflict/);
    });
  });

  it("offers generation when no draft exists and posts the planner id", async () => {
    const calls = mockBackend([]);
    render(<PlanPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByText("Generate plan")).toBeInTheDocument();
    });
    expect(screen.getByText("Generate plan")).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Planner agent"), {
      target: { value: "agent-1" },
    });
    fireEvent.click(screen.getByText("Generate plan"));

    await waitFor(() => {
      expect(
        calls.some(
          (c) =>
            c.url.endsWith("/api/backend/projects/p1/plans") && c.init?.method === "POST",
        ),
      ).toBe(true);
    });
    const post = calls.find((c) => c.init?.method === "POST");
    expect(JSON.parse(String(post?.init?.body))).toEqual({ planner_agent_id: "agent-1" });
  });
});
