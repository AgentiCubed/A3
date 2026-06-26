import { expect, test } from "@playwright/test";

test("dashboard renders the AgentiCubed heading and a status badge", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "AgentiCubed" })).toBeVisible();
  await expect(page.getByRole("status")).toBeVisible();
});
