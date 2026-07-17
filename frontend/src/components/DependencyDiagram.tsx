import type { ProjectGraph } from "@/lib/api";
import { mermaidFromGraph } from "@/lib/metrics";
import { MermaidDiagram } from "./MermaidDiagram";

/**
 * Dependency view. Renders the Mermaid flowchart live via the MermaidDiagram
 * client component (dynamic import — browser only) plus an at-a-glance edge
 * list with critical nodes highlighted. See ADR-0005 for history.
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
      <div style={{ marginTop: 12 }}>
        <MermaidDiagram source={mermaid} />
      </div>
    </div>
  );
}
