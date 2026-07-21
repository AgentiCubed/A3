import { expect, test, type APIRequestContext } from "@playwright/test";

/**
 * UI write path (c): an escalated approval gate is decided from the browser.
 * A manual task fails its rubric with no remediation budget, escalating to
 * AWAITING_APPROVAL; the operator approves it in the dashboard with a
 * justification and the task completes.
 */

const API = "http://localhost:8000";
const PASSWORD = "supersecret123";

async function apiJson(
  request: APIRequestContext,
  method: "get" | "post" | "patch",
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

test("operator decides an escalated approval gate in the browser", async ({
  page,
  request,
}) => {
  const email = `e2e-${Date.now()}-ap@example.com`;
  await apiJson(request, "post", "/api/v1/auth/register", {
    data: { organization_name: "E2E Approvals", email, password: PASSWORD },
  });
  const login = await apiJson(request, "post", "/api/v1/auth/login", {
    data: { email, password: PASSWORD },
  });
  const token = login.access_token as string;
  const agent = await apiJson(request, "post", "/api/v1/agents", {
    token,
    data: { name: "Worker", kind: "ai", provider: "mock" },
  });
  const project = await apiJson(request, "post", "/api/v1/projects", {
    token,
    data: { name: "E2E approvals project", objective: "Escalate one gate" },
  });
  const task = await apiJson(request, "post", `/api/v1/projects/${project.id}/tasks`, {
    token,
    data: { title: "Deliver the brief" },
  });
  await apiJson(
    request,
    "patch",
    `/api/v1/projects/${project.id}/tasks/${task.id}/assign`,
    { token, data: { agent_id: agent.id } },
  );
  // Failing rubric + zero remediation budget → AWAITING_APPROVAL + gate row.
  const dispatch = await apiJson(
    request,
    "post",
    `/api/v1/projects/${project.id}/tasks/${task.id}/dispatch`,
    {
      token,
      data: {
        rubric: [
          {
            key: "impossible",
            check: "contains_all",
            params: { keywords: ["TOKEN_THAT_NEVER_APPEARS"] },
          },
        ],
        max_remediations: 0,
      },
    },
  );
  expect(dispatch.final_state).toBe("awaiting_approval");

  await page.goto("/login");
  await page.getByPlaceholder("email").fill(email);
  await page.getByPlaceholder("password").fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");

  await page.goto(`/projects/${project.id}`);
  await expect(page.getByTestId("pending-approval")).toBeVisible();
  await expect(page.getByTestId("pending-approval")).toContainText("Deliver the brief");

  await page.getByLabel("Justification").fill("reviewed the output; acceptable");
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.locator("[data-approvals-notice]")).toContainText("Approved");
  await expect(page.getByTestId("no-pending-approvals")).toBeVisible();

  // The decision moved the machine: gate approved with the comment, task completed.
  const approvals = await apiJson(
    request,
    "get",
    `/api/v1/projects/${project.id}/approvals`,
    { token },
  );
  expect(approvals).toHaveLength(1);
  expect(approvals[0].status).toBe("approved");
  expect(approvals[0].comment).toBe("reviewed the output; acceptable");
  const tasks = await apiJson(request, "get", `/api/v1/projects/${project.id}/tasks`, {
    token,
  });
  expect(tasks[0].status).toBe("completed");
});
