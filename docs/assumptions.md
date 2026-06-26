# AgentiCubed — Architectural Assumptions

Reasonable assumptions made to avoid blocking on broad product questions. Each
can be revisited; revisions that change architecture become ADRs.

| # | Assumption | Rationale | Reversible? |
|---|------------|-----------|-------------|
| A1 | Multi-tenant by `Organization`; single deployment serves many orgs. | Standard SaaS shape; matches Organization entity. | Yes |
| A2 | Python 3.11+, Node 20+ targeted in containers regardless of host versions. | Pins a modern, supported baseline; host here has 3.9/Node 26. | Yes |
| A3 | Pydantic v2 and SQLAlchemy 2.0 (typed, async-capable) as the baseline. | Current major versions; long support runway. | Yes |
| A4 | REST + JSON API, versioned under `/api/v1`; SSE for live execution updates (no GraphQL/websocket infra for MVP). | Simpler, testable; SSE covers live needs. | Yes |
| A5 | Auth = email/password + JWT for MVP; SSO/OAuth deferred. | Fastest secure baseline; pluggable later. | Yes |
| A6 | First real provider adapter targets Anthropic (Claude); MockProvider for deterministic tests. | A functional provider is required; Claude is the latest/most capable default. | Yes |
| A7 | Artifact storage uses a local-filesystem adapter for MVP behind `ArtifactStore`; S3 adapter later. | No cloud creds needed to run locally. | Yes |
| A8 | Celery + Redis broker/result backend for MVP workers, behind `WorkflowEngine` port. | Matches stack; Temporal swap is a port re-impl. | Yes (port) |
| A9 | Human contributors are modeled as `Agent` rows with `kind='human'`; their "execution" is a human-completed task record. | Unifies assignment/matching/metrics across humans + AI. | Medium |
| A10 | Methodology recommendation is rule-based for MVP (heuristics over project attributes), upgradable to model-assisted. | Deterministic + testable first. | Yes |
| A11 | Analysis workers (Python/R) run as separate tool invocations producing artifacts, not inline in the API. | Keeps API responsive; matches worker layer. | Yes |
| A12 | Money/cost tracked as decimal estimates in a single org currency for MVP. | Avoids FX scope. | Yes |
| A13 | Time stored in UTC; presentation localizes. | Standard. | No |
| A14 | "Power BI-compatible export" = flat CSV + a JSON schema descriptor + a star-shaped table layout PBI can ingest; no native `.pbix` generation. | PBI ingests CSV/JSON readily; native pbix is out of scope. | Yes |
| A15 | Deterministic tests must never call a live provider; CI uses MockProvider only. | Reproducible CI. | No |
