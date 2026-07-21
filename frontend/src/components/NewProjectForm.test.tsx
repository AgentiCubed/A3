import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewProjectForm } from "./NewProjectForm";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

describe("NewProjectForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    push.mockClear();
  });

  it("creates a project from name + objective and navigates to it", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      calls.push({ url: String(input), init });
      return Response.json({ id: "proj-9" });
    });

    render(<NewProjectForm />);
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "Widget push" },
    });
    fireEvent.change(screen.getByLabelText("Objective"), {
      target: { value: "Ship the widget brief" },
    });
    fireEvent.click(screen.getByText("Create project"));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/projects/proj-9"));
    const post = calls.find((c) => c.init?.method === "POST");
    expect(post?.url.endsWith("/api/backend/projects")).toBe(true);
    expect(JSON.parse(String(post?.init?.body))).toEqual({
      name: "Widget push",
      objective: "Ship the widget brief",
    });
  });

  it("tells a signed-out visitor to sign in instead of failing silently", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ error: "not signed in" }, { status: 401 }),
    );
    render(<NewProjectForm />);
    fireEvent.change(screen.getByLabelText("Project name"), { target: { value: "X" } });
    fireEvent.change(screen.getByLabelText("Objective"), { target: { value: "Y" } });
    fireEvent.click(screen.getByText("Create project"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/Sign in/);
    });
    expect(push).not.toHaveBeenCalled();
  });
});
