# Diagram sources

Mermaid sources for the diagrams embedded throughout this repository. Each `.mmd`
file is the canonical source; the fenced `mermaid` blocks in the documents are
copies, and a header comment in each file records where it is rendered.

GitHub renders Mermaid natively in Markdown, so no build step or image export is
required. These files exist so the diagrams can be edited, diffed, and reused
without hunting through prose.

| File | Rendered in | Shows |
|------|-------------|-------|
| [`01-operating-layer.mmd`](01-operating-layer.mmd) | `README.md` | Four layers: surfaces, operating layer, adapter boundary, external services |
| [`02-governed-loop.mmd`](02-governed-loop.mmd) | `docs/architecture.md` §3 | The full loop, including contract validation and budget-exhaustion escalation |
| [`03-approval-gate.mmd`](03-approval-gate.mmd) | `docs/architecture.md` §4 | An irreversible action stopping at a human gate despite a valid standing permission |
| [`04-adapter-boundary.mmd`](04-adapter-boundary.mmd) | `docs/architecture.md` §5 | Ports and interchangeable adapters, including a retirement tombstone |
| [`05-trust-boundaries.mmd`](05-trust-boundaries.mmd) | `docs/security-boundaries.md` §2 | Who may authorize what — and the dotted edge that may not |
| [`06-horizons.mmd`](06-horizons.mmd) | `README.md`, `docs/roadmap.md` | Roadmap horizons; the ordering is the argument |

## Editing

Paste a file into any Mermaid renderer, or edit it in place and copy the result
back into the document that embeds it. If you change a diagram, change both — the
header comment in each file names its render site so the pair stays findable.

## No screenshots

This directory contains no screenshots of the running system, and that is
deliberate. Console screenshots leak more than people expect: internal
identifiers, route shapes, account names, project titles, and environment detail
all end up legible in a supposedly-illustrative image. Diagrams communicate the
design without any of that.
