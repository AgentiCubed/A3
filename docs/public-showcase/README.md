# AgentiCubed Public Showcase Starter

This folder contains sanitized assets you can copy into a separate public GitHub
repository such as `AgentiCubed/agenticubed-public`.

The goal is to let recruiters and other external readers understand what
AgentiCubed is, what has been built, and how it is progressing — without
publishing private source code or sensitive internal material.

## Recommended public repository contents

- `README.md` — public project overview
- `CHANGELOG.md` — high-level public progress log
- `updates/` — dated weekly unclassified updates
- screenshots, diagrams, or mockups that do not reveal sensitive information

## Public README outline

Use the following outline as the starting point for the public repository
`README.md`.

### AgentiCubed

**Agentic project-orchestration platform** that manages projects performed by AI
agents and human contributors.

### Problem statement

Most teams can prompt an agent, but they still lack a governed system that can
turn an objective into planned work, assign the right agents, evaluate outputs,
remediate failures, and keep humans in control.

### What the product does

AgentiCubed converts project objectives into structured plans, recommends a
project-management methodology, decomposes work into tasks, identifies required
capabilities, assigns specialized agents, executes tasks, evaluates outputs,
detects failures, applies remediation, and continues until acceptance criteria
are satisfied.

### Principal control loop

```text
Plan → Assign → Execute → Evaluate → Identify Gaps → Remediate → Re-execute
```

### High-level architecture

- Project intake and requirements
- Methodology recommendation
- Work decomposition
- Capability analysis
- Agent registry
- Task-to-agent matching
- Orchestration and execution
- Output evaluation
- Closed-loop remediation
- Human approval
- Governance and auditing
- Analytics and reporting
- Project closeout and retrospective

### Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, React |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Data | PostgreSQL 16, Redis 7 |
| Workers | Celery behind a `WorkflowEngine` abstraction |
| Infra | Docker, Docker Compose |
| Visualization | Recharts / Plotly, Mermaid |
| Analysis | Python + R analysis workers |
| Testing | Pytest, Vitest, Playwright |

### Current status

- All eight planned phases are complete in the private implementation.
- Core areas include orchestration, evaluation, approvals, remediation,
  analytics, artifacts, and an end-to-end demonstration flow.

### What is implemented

- Multi-phase delivery from scaffolding through security hardening
- Agent registry, capability taxonomy, and provider-neutral integrations
- Durable task execution state machine with retries, escalation, and
  reassignment
- Deterministic and agent-assisted evaluation with enforced separation of roles
- Human approval gates and immutable audit history
- Project and agent analytics, dashboards, and export support
- Real Python and R analysis workers plus seeded end-to-end demonstration

### Screenshots and mockups

Add sanitized screenshots here, for example:

- dashboard overview
- project timeline / dependency view
- risk matrix
- agent assignment or execution history

### Public roadmap / near-term focus

- Continue polishing the product presentation
- Expand recruiter-safe screenshots and diagrams
- Publish weekly progress updates

### Notes for external readers

This public repository is intentionally limited to high-level documentation,
status updates, and presentation material. The working product source remains
private.

## Safe-to-publish guidance

Safe to publish:

- product summary
- high-level architecture
- tech stack
- milestone/status summaries
- sanitized screenshots and diagrams
- unclassified weekly progress updates

Do not publish:

- private source code
- secrets, credentials, or tokens
- internal prompts
- customer or partner data
- security-sensitive operational details
- exact implementation details you consider proprietary

## Suggested publishing workflow

1. Create a separate public repository.
2. Copy the files in this folder into that repository.
3. Add screenshots or diagrams after reviewing them for sensitive content.
4. Post a short update each week in `updates/` and summarize it in
   `CHANGELOG.md`.
5. Pin the public repository on your GitHub profile and link it from your
   profile README.
