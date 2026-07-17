"use client";

import { useEffect, useRef } from "react";

/**
 * Live Mermaid diagram renderer.
 * Dynamically imports the mermaid library so it never SSR-renders
 * (mermaid requires a browser DOM). Falls back to showing the raw
 * source inside a <pre> if rendering fails.
 */
export function MermaidDiagram({ source }: { source: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !source.trim()) return;
    const el = ref.current;
    let cancelled = false;

    async function render() {
      try {
        const { default: mermaid } = await import("mermaid");
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            background: "#0d1117",
            primaryColor: "#2f6fed",
            primaryTextColor: "#e6edf3",
            lineColor: "#8b949e",
            edgeLabelBackground: "#161b22",
          },
        });
        const id = `mermaid-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, source);
        if (!cancelled && el) {
          el.innerHTML = svg;
        }
      } catch {
        // Rendering failed — show raw source as fallback.
        if (!cancelled && el) {
          el.innerHTML = "";
          const pre = document.createElement("pre");
          pre.className = "mermaid";
          pre.style.cssText =
            "background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;font-size:12px;overflow-x:auto;color:#c9d4df;";
          pre.textContent = source;
          el.appendChild(pre);
        }
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [source]);

  return <div ref={ref} aria-label="Dependency diagram" />;
}
