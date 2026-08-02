import { describe, expect, it } from "vitest";
import { errorDetail } from "@/lib/backend";

describe("errorDetail", () => {
  it("surfaces the cause of a failed plan generation, not just the label", () => {
    // The API returns {error, code, detail}; showing only `error` left
    // operators with "plan_generation_failed" and no reason, while the
    // diagnostic sat in the database. Regression guard.
    const message = errorDetail({
      detail: {
        error: "plan_generation_failed",
        plan_id: "abc",
        code: "planner_error",
        detail: "provider_http_status=410 provider_error_category=not_found",
      },
    });
    expect(message).toContain("plan_generation_failed");
    expect(message).toContain("planner_error");
    expect(message).toContain("provider_http_status=410");
    expect(message).toContain("not_found");
  });

  it("surfaces an invalid-plan diagnostic", () => {
    const message = errorDetail({
      detail: {
        error: "plan_generation_failed",
        code: "invalid_plan",
        detail: "planner output is not valid JSON",
      },
    });
    expect(message).toContain("invalid_plan");
    expect(message).toContain("not valid JSON");
  });

  it("still handles a plain string detail", () => {
    expect(errorDetail({ detail: "objective is required" })).toBe(
      "objective is required",
    );
  });

  it("still handles the auth proxy's error shape", () => {
    expect(errorDetail({ error: "not signed in" })).toBe("not signed in");
  });

  it("falls back when nothing is recognisable", () => {
    expect(errorDetail({})).toBe("request failed");
    expect(errorDetail(null)).toBe("request failed");
  });
});
