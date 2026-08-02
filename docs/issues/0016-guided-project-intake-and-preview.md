# Issue 0016 — Guided project intake, controls board, and live preview

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` D1, D2, D3, D4  
**Suggested labels:** `type:enhancement`, `type:epic`, `area:backend`, `area:frontend`, `track:intake`

## Summary
Redesign project intake so the system first restates its understanding, lets the
user correct that understanding, and then offers a configurable controls board
with a live preview before project creation.

## Problem
A single objective textbox does not confirm shared understanding or give the
operator enough control over deliverable shape, evaluation strictness, and work
sizing before execution begins.

## Desired outcome
Project creation should become a guided flow that confirms intent, captures
operator preferences explicitly, and previews how those choices will shape the
plan.

## Acceptance criteria
- [ ] Before project creation, the system presents its understanding of the
      objective, deliverables, assumptions, and out-of-scope items.
- [ ] The operator can correct or comment on that understanding and iterate
      until explicitly confirming it.
- [ ] The intake flow includes a configurable controls board that captures the
      agreed product settings needed for plan quality, evaluation, and routing.
- [ ] A live preview updates before creation to show predicted plan shape,
      estimated task count, estimated model-call intensity, and a sample output
      snippet shaped by the selected options.
- [ ] The confirmed understanding and chosen controls are stored as auditable
      project inputs and feed downstream planning behavior.

## Dependencies
- Planning and routing improvements from issues 0009 and 0011.
- Frontend intake flow redesign.

## Security and risk notes
- Only authenticated, authorized users may create or revise intake state.
- Stored intake data must be auditable and redact any sensitive example text.
