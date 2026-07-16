import { expect, test } from "@playwright/test";

test("dashboard renders the Agentic³ wordmark and a status badge", async ({ page }) => {
  await page.goto("/");
  // The h1 wraps the Wordmark, whose accessible name is "Agentic cubed".
  await expect(page.getByRole("heading", { name: "Agentic cubed" })).toBeVisible();
  // Scoped by data-state so the Next.js dev-mode indicator (also role=status)
  // does not trip strict mode when the server runs in dev.
  await expect(page.locator('[role="status"][data-state]')).toBeVisible();
});
