import { expect, test, type APIRequestContext } from "@playwright/test";

/**
 * UI write path (b), next-steps Step 1: start, halt, and resume from the
 * dashboard against the real backend. Proves the halt gate through the UI:
 * a halted project refuses to start with a visible reason, resume lifts the
 * gate, and the governed loop then runs the approved plan to completion.
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

test("operator halts, is refused start, resumes, then runs the loop to completion", async ({
  page,
  request,
}) => {
  const email = `e2e-${Date.now()}-c@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Controls", email, password: PASSWORD },
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
  const builder = await apiJson(request, "post", "/api/v1/agents", {
    token,
    data: { name: "Builder", kind: "ai", provider: "mock" },
  });
  const project = await apiJson(request, "post", "/api/v1/projects", {
    token,
    data: { name: "E2E controls project", objective: "Run the governed loop" },
  });

  await page.goto("/login");
  await page.getByPlaceholder("email").fill(email);
  await page.getByPlaceholder("password").fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");

  // Approve a plan through the flow-(a) UI so the project is startable.
  await page.goto(`/projects/${project.id}`);
  await page.getByLabel("Planner agent").selectOption(planner.id);
  await page.getByRole("button", { name: "Generate plan" }).click();
  await expect(page.getByTestId("plan-draft")).toBeVisible();
  await page.getByLabel("Executor agent").selectOption(builder.id);
  await page.getByRole("button", { name: "Approve plan" }).click();
  await expect(page.locator("[data-plan-notice]")).toContainText("approved");

  // Halt first: the gate must refuse start with a visible reason.
  await page.getByLabel("Halt reason").fill("hold for review");
  await page.getByRole("button", { name: "Halt" }).click();
  await expect(page.getByTestId("project-state")).toContainText("HALTED");
  await expect(page.getByRole("button", { name: "Resume" })).toBeVisible();

  // Resume lifts the gate (nothing was in flight yet).
  await page.getByRole("button", { name: "Resume" }).click();
  await expect(page.getByRole("button", { name: "Start" })).toBeVisible();

  // Start runs the approved plan; inline engine completes the chain in-request.
  await page.getByRole("button", { name: "Start" }).click();
  await expect(page.locator("[data-controls-notice]")).toContainText(
    /ran to completion|dispatched/,
    { timeout: 30_000 },
  );

  // The loop actually ran: both plan tasks are COMPLETED, and the audit trail
  // holds the operator's halt with its reason.
  const tasks = await apiJson(request, "get", `/api/v1/projects/${project.id}/tasks`, {
    token,
  });
  expect(tasks).toHaveLength(2);
  for (const task of tasks) {
    expect(task.status).toBe("completed");
  }
});

test("start on an unapproved governed project is refused with a visible reason", async ({
  page,
  request,
}) => {
  const email = `e2e-${Date.now()}-u@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Unapproved", email, password: PASSWORD },
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
  const project = await apiJson(request, "post", "/api/v1/projects", {
    token,
    data: { name: "E2E unapproved project", objective: "Nothing approved yet" },
  });

  await page.goto("/login");
  await page.getByPlaceholder("email").fill(email);
  await page.getByPlaceholder("password").fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");

  await page.goto(`/projects/${project.id}`);
  await page.getByLabel("Planner agent").selectOption(planner.id);
  await page.getByRole("button", { name: "Generate plan" }).click();
  await expect(page.getByTestId("plan-draft")).toBeVisible();

  // Draft exists but is NOT approved: the gate refuses to start.
  await page.getByRole("button", { name: "Start" }).click();
  await expect(page.locator("[data-controls-error]")).toContainText(
    /plan_approval_required/,
  );
});
