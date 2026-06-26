# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-25

## Context
AgentiCubed has firm architectural constraints (provider neutrality, durable
state, immutable history, replaceable worker layer). Decisions that affect these
constraints — including any substitution of the default stack — must be
traceable.

## Decision
We keep Architecture Decision Records as numbered Markdown files in
`docs/decisions/`. Any deviation from the default technical stack, or any
decision materially affecting the constraints above, requires an ADR. ADRs are
immutable once Accepted; a later decision supersedes (it does not edit) an
earlier one.

## Consequences
- A reviewer can reconstruct *why* the system looks the way it does.
- Stack substitutions are never silent; they carry a recorded rationale.
- Lightweight format keeps the cost of recording low.
