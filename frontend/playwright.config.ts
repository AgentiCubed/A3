import { defineConfig, devices } from "@playwright/test";

/**
 * E2E config: full-stack. Boots the hermetic backend (SQLite + mock provider,
 * see backend/tools/run_e2e_backend.py) and the Next dev server, then drives
 * the governed loop through the real browser. Run with: npm run test:e2e
 * (requires `npm install`, `npx playwright install`, and the backend's Python
 * environment — override the interpreter with E2E_BACKEND_CMD).
 *
 * Set E2E_BASE_URL to target an already-running stack instead.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  // Specs share one backend and one dev server; serial execution keeps the
  // dev server's lazy page compilation from stampeding under parallel load.
  workers: 1,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : [
        {
          command: process.env.E2E_BACKEND_CMD ?? "python3 tools/run_e2e_backend.py",
          cwd: "../backend",
          url: "http://localhost:8000/healthz",
          reuseExistingServer: true,
          timeout: 120_000,
        },
        {
          command: "npm run dev",
          url: "http://localhost:3000",
          reuseExistingServer: true,
          timeout: 60_000,
          env: {
            INTERNAL_API_BASE_URL: "http://localhost:8000",
            NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000",
          },
        },
      ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
