import { expect, test } from "@playwright/test";
import path from "node:path";

// The game is a self-contained static file at the repo root; no dev server needed.
const gameUrl =
  "file://" + path.resolve(__dirname, "../../../verbal-kombat/index.html");

test.describe("Verbal Kombat", () => {
  // A CPU-vs-CPU match plays out in real time (~1-2s per exchange, best of 3 rounds).
  test.setTimeout(180_000);

  test("spectated match runs to fatality and produces a transcript", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));

    await page.goto(gameUrl);
    await page.click("#btn-start");
    await page.click('.fcard[data-id="einstein"]');
    await page.click('.fcard[data-id="ramsay"]');
    await page.click("#btn-toSetup");
    await page.fill("#topic", "Is a hot dog a sandwich?");
    await page.fill("#stance1", "Topologically, yes.");
    await page.fill("#stance2", "It's RAW is not a sandwich, and neither is this.");
    await page.click("#mode-watch");
    await page.click("#btn-fight");

    await page.waitForSelector("#donewrap:not([hidden])", { timeout: 150_000 });
    await page.click("#btn-transcript");

    const doc = page.locator("#doc");
    await expect(doc.locator("header")).toBeVisible();
    await expect(doc).toContainText("Majority opinion");
    await expect(doc).toContainText("Dissenting opinion");
    expect(errors).toEqual([]);
  });

  test("custom fighter names are escaped, not injected as HTML", async ({
    page,
  }) => {
    await page.goto(gameUrl);
    await page.click("#btn-start");
    await page.fill("#cust-name", '<img src=x onerror="window.xss=1">');
    await page.click("#btn-cust");

    // The name must render as text inside the roster card, not as an element.
    await expect(page.locator(".fcard img")).toHaveCount(0);
    expect(await page.evaluate(() => (window as any).xss)).toBeUndefined();
    await expect(
      page.locator(".fcard .fname").last(),
    ).toContainText("<img src=x");
  });
});
