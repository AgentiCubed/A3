import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HealthBadge } from "./HealthBadge";

describe("HealthBadge", () => {
  it("renders the operational label for ok state", () => {
    render(<HealthBadge state="ok" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("Operational");
    expect(badge).toHaveAttribute("data-state", "ok");
  });

  it("renders degraded state", () => {
    render(<HealthBadge state="degraded" />);
    expect(screen.getByRole("status")).toHaveTextContent("Degraded");
  });

  it("falls back to unknown styling for unknown state", () => {
    render(<HealthBadge state="unknown" />);
    expect(screen.getByRole("status")).toHaveTextContent("Unknown");
  });
});
