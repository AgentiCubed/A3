import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskMatrix } from "./RiskMatrix";

describe("RiskMatrix", () => {
  it("renders a 5x5 grid and shows counts", () => {
    render(<RiskMatrix matrix={{ L4I5: 2 }} />);
    const table = screen.getByRole("table", { name: "Risk matrix" });
    expect(table).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    // Likelihood/impact axis labels present.
    expect(screen.getByText("L5")).toBeInTheDocument();
    expect(screen.getByText("I5")).toBeInTheDocument();
  });
});
