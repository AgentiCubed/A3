import { expect, test, type APIRequestContext } from "@playwright/test";

/**
 * UI write path (a), next-steps Step 1: a human operates the plan gate from
 * the browser — generate a decomposition plan, review exactly what the
 * planner proposed, and approve it — against the real backend (hermetic:
 * SQLite + mock provider), with the real httpOnly-cookie session.
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

test("operator generates and approves a plan entirely in the browser", async ({
  page,
  request,
}) => {
  // Seed through the public API: an org, a planner, an executor, a project.
  const email = `e2e-${Date.now()}@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Org", email, password: PASSWORD },
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
    data: { name: "E2E governed project", objective: "Ship the demo widget" },
  });

  // Sign in through the real login form (sets the httpOnly session cookie).
  await page.goto("/login");
  await page.getByPlaceholder("email").fill(email);
  await page.getByPlaceholder("password").fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");

  // Generate a plan from the dashboard.
  await page.goto(`/projects/${project.id}`);
  await expect(page.getByTestId("plan-panel")).toBeVisible();
  await page.getByLabel("Planner agent").selectOption(planner.id);
  await page.getByRole("button", { name: "Generate plan" }).click();

  // The draft renders exactly what the mock planner proposed.
  await expect(page.getByTestId("plan-draft")).toBeVisible();
  await expect(page.getByText("Research the objective")).toBeVisible();
  await expect(page.getByText("Deliver the objective")).toBeVisible();
  await expect(page.getByText(/research → deliver/)).toBeVisible();

  // Approve with an executor assignment; the request is version+sha bound.
  await page.getByLabel("Executor agent").selectOption(builder.id);
  await page.getByLabel("Decision comment").fill("looks right, ship it");
  await page.getByRole("button", { name: "Approve plan" }).click();
  await expect(page.locator("[data-plan-notice]")).toContainText("approved");

  // The approval materialized real tasks behind the gate.
  const tasks = await apiJson(request, "get", `/api/v1/projects/${project.id}/tasks`, {
    token,
  });
  expect(tasks).toHaveLength(2);
  const plans = await apiJson(request, "get", `/api/v1/projects/${project.id}/plans`, {
    token,
  });
  expect(plans[plans.length - 1].status).toBe("approved");
});

test("operator rejects a plan and the decision is recorded", async ({
  page,
  request,
}) => {
  const email = `e2e-${Date.now()}-r@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Org R", email, password: PASSWORD },
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
    data: { name: "E2E rejected project", objective: "Do something else" },
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

  await page.getByLabel("Decision comment").fill("wrong direction");
  await page.getByRole("button", { name: "Reject plan" }).click();
  await expect(page.locator("[data-plan-notice]")).toContainText("rejected");

  const plans = await apiJson(request, "get", `/api/v1/projects/${project.id}/plans`, {
    token,
  });
  expect(plans[plans.length - 1].status).toBe("rejected");
  expect(plans[plans.length - 1].decision_comment).toBe("wrong direction");
  const tasks = await apiJson(request, "get", `/api/v1/projects/${project.id}/tasks`, {
    token,
  });
  expect(tasks).toHaveLength(0); // rejection leaves no executable residue
});
