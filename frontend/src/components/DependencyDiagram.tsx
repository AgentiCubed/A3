import type { ProjectGraph } from "@/lib/api";
import { mermaidFromGraph } from "@/lib/metrics";

/**
 * Dependency view. Renders the Mermaid flowchart source (paste into any Mermaid
 * renderer) plus an at-a-glance edge list with critical nodes highlighted.
 * Mermaid source generation is pure + unit-tested; see ADR-0005 for why we emit
 * Mermaid text rather than bundling a heavy client renderer in the MVP.
 */
export function DependencyDiagram({ graph }: { graph: ProjectGraph }) {
  if (graph.nodes.length === 0) {
    return <p style={{ color: "#9fb0c0" }}>No tasks to graph.</p>;
  }
  const titleById = new Map(graph.nodes.map((n) => [n.id, n]));
  const mermaid = mermaidFromGraph(graph.nodes, graph.edges);
  return (
    <div>
      <ul aria-label="Dependencies" style={{ fontSize: 13, color: "#c9d4df" }}>
        {graph.edges.length === 0 && <li>No dependencies defined.</li>}
        {graph.edges.map((e, i) => {
          const from = titleById.get(e.predecessor_task_id);
          const to = titleById.get(e.successor_task_id);
          return (
            <li key={i}>
              <strong style={{ color: from?.is_critical ? "#ff6b6b" : undefined }}>
                {from?.title ?? e.predecessor_task_id.slice(0, 8)}
              </strong>{" "}
              → {to?.title ?? e.successor_task_id.slice(0, 8)}
            </li>
          );
        })}
      </ul>
      <details style={{ marginTop: 8 }}>
        <summary style={{ cursor: "pointer", color: "#9fb0c0", fontSize: 12 }}>
          Mermaid source
        </summary>
        <pre
          className="mermaid"
          style={{
            background: "#0d1117",
            border: "1px solid #30363d",
            borderRadius: 6,
            padding: 12,
            fontSize: 12,
            overflowX: "auto",
          }}
        >
          {mermaid}
        </pre>
      </details>
    </div>
  );
}
