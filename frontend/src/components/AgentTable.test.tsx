import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AgentTable } from "./AgentTable";

describe("AgentTable", () => {
  it("shows an empty state with no rows", () => {
    render(<AgentTable rows={[]} />);
    expect(screen.getByText(/no agent executions/i)).toBeInTheDocument();
  });

  it("renders agent rows with formatted success rate", () => {
    render(
      <AgentTable
        rows={[
          {
            agent_id: "a",
            agent_name: "Alpha",
            metrics: { executions: 2, success_rate: 0.5, avg_score: 0.8, avg_tokens: 75 },
          },
        ]}
      />,
    );
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("0.80")).toBeInTheDocument();
  });
});
