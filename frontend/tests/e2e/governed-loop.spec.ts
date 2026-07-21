import { expect, test, type APIRequestContext } from "@playwright/test";

/**
 * THE Step-1 definition of done (docs/NEXT-STEPS-2026-07.md):
 *
 *   "a Playwright e2e drives objective → plan → approve → start →
 *    (mock) completion → close entirely through the browser"
 *
 * Only the agent registry (a planner with planning.decompose and an executor)
 * is seeded via API — agents have no UI surface yet. Everything the roadmap
 * names happens in the browser: the objective enters through the new-project
 * form, the plan is generated and approved in the dashboard, start runs the
 * governed loop to completion, and close is earned against the generated
 * acceptance criteria.
 */

const API = "http://localhost:8000";
const PASSWORD = "supersecret123";

async function apiJson(
  request: APIRequestContext,
  method: "get" | "post",
  path: string,
  options: { token?: string; data?: unknown } = {},
): Promise<any> {
  const res = await request[method](`${API}${path}`, {
    headers: options.token ? { authorization: `Bearer ${options.token}` } : undefined,
    data: options.data,
  });
  expect(res.ok(), `${method.toUpperCase()} ${path} -> ${res.status()}`).toBeTruthy();
  return res.json();
}

test("objective to close, entirely through the browser", async ({ page, request }) => {
  const email = `e2e-${Date.now()}-loop@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Loop", email, password: PASSWORD },
  });
  const login = await apiJson(request, "post", "/api/v1/auth/login", {
    data: { email, password: PASSWORD },
  });
  const token = login.access_token as string;
  const planner = await apiJson(request, "post", "/api/v1/agents", {
    token,
    data: { name: "Planner", kind: "ai", provider: "mock" },
  });
  await apiJson(request, "post", `/api/v1/agents/${planner.id}/capabilities`, {
    token,
    data: { capability: "planning.decompose" },
  });
  await apiJson(request, "post", "/api/v1/agents", {
    token,
    data: { name: "Builder", kind: "ai", provider: "mock" },
  });

  // Sign in through the login form.
  await page.goto("/login");
  await page.getByPlaceholder("email").fill(email);
  await page.getByPlaceholder("password").fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");

  // Objective in: the project is born in the browser.
  await expect(page.getByTestId("new-project-form")).toBeVisible();
  await page.getByLabel("Project name").fill("Browser-governed project");
  await page.getByLabel("Objective").fill("Deliver the governed demo end to end");
  await page.getByRole("button", { name: "Create project" }).click();
  await page.waitForURL("**/projects/**");

  // Plan: generate and review.
  await page.getByLabel("Planner agent").selectOption({ label: "Planner" });
  await page.getByRole("button", { name: "Generate plan" }).click();
  await expect(page.getByTestId("plan-draft")).toBeVisible();

  // Approve: executor assigned, decision bound to the rendered plan.
  await page.getByLabel("Executor agent").selectOption({ label: "Builder" });
  await page.getByLabel("Decision comment").fill("approved in the browser");
  await page.getByRole("button", { name: "Approve plan" }).click();
  await expect(page.locator("[data-plan-notice]")).toContainText("approved");

  // Start: the loop runs the approved plan (inline engine, mock provider).
  await page.getByRole("button", { name: "Start" }).click();
  await expect(page.locator("[data-controls-notice]")).toContainText(
    /ran to completion/,
    {
      timeout: 30_000,
    },
  );

  // Close: completion is earned against the generated acceptance criteria.
  await page.getByRole("button", { name: "Close project" }).click();
  await expect(page.locator("[data-controls-notice]")).toContainText("closed");
  await expect(page.getByTestId("project-state")).toContainText("closed");

  // The record agrees with the screen: closed project, all tasks completed.
  const url = page.url();
  const projectId = url.substring(url.lastIndexOf("/") + 1);
  const project = await apiJson(request, "get", `/api/v1/projects/${projectId}`, {
    token,
  });
  expect(project.status).toBe("closed");
  const tasks = await apiJson(request, "get", `/api/v1/projects/${projectId}/tasks`, {
    token,
  });
  expect(tasks.length).toBeGreaterThan(0);
  for (const task of tasks) {
    expect(task.status).toBe("completed");
  }
});
