# AgentiCubed Engineering Governance Playbook

**Version:** 1.0  
**Authority:** Subordinate to the [AgentiCubed Constitution v1.0](../constitution/Constitution-v1.0.md)  
**Status:** Active

---

## Purpose

This Playbook is the operational layer of AgentiCubed engineering governance. It translates the constitutional principles into durable, reviewable working practice for all human and autonomous contributors.

The Constitution governs enduring authority and obligations. This Playbook governs how work is initiated, executed, reviewed, and verified under that authority. Where the two conflict, the Constitution controls.

---

## Governing Hierarchy

The following instruments govern AgentiCubed engineering in order of precedence:

| Layer | Instrument | Location |
|---|---|---|
| 1 | **Constitution** | `docs/governance/constitution/` |
| 2 | **Governance Decision Records** | `docs/governance/decisions/` |
| 3 | **Policy** (this Playbook) | `docs/governance/playbook/` |
| 4 | **Standards** (this Playbook) | `docs/governance/playbook/` |
| 5 | **Procedures** (this Playbook) | `docs/governance/playbook/` |
| 6 | **Templates** (this Playbook) | `docs/governance/playbook/` |
| 7 | **Architecture Decision Records** | `docs/decisions/` |
| 8 | **Knowledge Records** | `docs/governance/knowledge/` |

A lower layer may interpret and implement a higher layer. It may not contradict it.

---

## Contents

| Document | Type | Purpose |
|---|---|---|
| [POL-0001 — Gate Workflow](POL-0001-gate-workflow.md) | Policy | Authorized gate-based operating model for all repository work |
| [STD-0001 — Context-Complete Reviews](STD-0001-context-complete-reviews.md) | Standard | Minimum requirements for reviewable, reproducible review assignments |
| [STD-0002 — Traceable Architecture Reviews](STD-0002-traceable-architecture-reviews.md) | Standard | Required review packet and reasoning chain for significant architectural proposals |
| [PROC-0001 — Git Workflow](PROC-0001-git-workflow.md) | Procedure | Branch naming, commit, PR, and merge procedures |
| [TPL-0001 — Task Packet](TPL-0001-task-packet.md) | Template | Minimum packet for any delegated task or review assignment |

---

## Scope

This Playbook governs work performed in the `AgentiCubed/agenticubed` repository by all contributors, including autonomous agents acting under Delegation.

It does not govern matters within constitutional jurisdiction (Article I, §1) unless doing so operationalizes an existing constitutional requirement.

---

## Amendment

This Playbook is a subordinate instrument. Its contents may be updated through a PR authorized by the Principal holding ultimate authority for AgentiCubed engineering, without constitutional amendment, provided the change does not alter constitutional authority, obligations, or jurisdiction.

Material changes shall be logged as a Governance Decision Record under `docs/governance/decisions/`.
