import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApprovalsPanel } from "./ApprovalsPanel";

const PENDING = {
  id: "ap-1",
  project_id: "p1",
  task_execution_id: "ex-1",
  requested_action:
    "Evaluation failed for task 'Deliver'. Recommended remediation: escalate.",
  risk_level: "medium",
  status: "pending",
  comment: null,
  decided_at: null,
};

type FetchArgs = { url: string; init?: RequestInit };

function mockBackend(
  approvalPages: unknown[][],
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
      const body = approvalPages[Math.min(reads, approvalPages.length - 1)];
      reads += 1;
      return Response.json(body);
    }
    return Response.json({ ...PENDING, status: "approved" });
  });
  return calls;
}

describe("ApprovalsPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the empty state when nothing is pending", async () => {
    mockBackend([[]]);
    render(<ApprovalsPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("no-pending-approvals")).toBeInTheDocument();
    });
  });

  it("renders a pending gate and approves it with a justification", async () => {
    const calls = mockBackend([
      [PENDING],
      [{ ...PENDING, status: "approved", comment: "verified by hand" }],
    ]);
    render(<ApprovalsPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("pending-approval")).toBeInTheDocument();
    });
    expect(screen.getByText(/Evaluation failed for task 'Deliver'/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Justification"), {
      target: { value: "verified by hand" },
    });
    fireEvent.click(screen.getByText("Approve"));

    await waitFor(() => {
      expect(screen.getByTestId("no-pending-approvals")).toBeInTheDocument();
    });
    const decideCall = calls.find(
      (c) => c.url.includes("/approvals/ap-1/decide") && c.init?.method === "POST",
    );
    expect(JSON.parse(String(decideCall?.init?.body))).toEqual({
      approve: true,
      comment: "verified by hand",
    });
    expect(screen.getByText(/Decided: approved/)).toBeInTheDocument();
  });

  it("rejects with approve=false", async () => {
    const calls = mockBackend([[PENDING], [{ ...PENDING, status: "rejected" }]]);
    render(<ApprovalsPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("pending-approval")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Reject"));
    await waitFor(() => {
      expect(screen.getByText(/Decided: rejected/)).toBeInTheDocument();
    });
    const decideCall = calls.find((c) => c.url.includes("/decide"));
    expect(JSON.parse(String(decideCall?.init?.body))).toEqual({
      approve: false,
      comment: null,
    });
  });

  it("surfaces an already-decided refusal", async () => {
    mockBackend([[PENDING]], ({ url }) => {
      if (url.includes("/decide")) {
        return Response.json({ detail: "approval already decided" }, { status: 409 });
      }
      return undefined;
    });
    render(<ApprovalsPanel projectId="p1" />);
    await waitFor(() => {
      expect(screen.getByTestId("pending-approval")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Approve"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/already decided/);
    });
  });
});
