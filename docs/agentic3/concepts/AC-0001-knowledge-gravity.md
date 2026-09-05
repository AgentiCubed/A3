# AC-0001 — Knowledge Gravity

**Type:** Foundational Concept (Architectural Candidate)
**Status:** **Adopted, as amended** — by explicit Principal decision
[DR-0004](../../governance/decisions/DR-0004-Phase-0-Reconciliation-Decisions.md)
P-1 (2026-07-26, recorded in RR-0002). The amendments conform the ontology
representation to this concept (four-source rule; gravity is justified
weight, never authority) and thereby action and close both previously met
reopening conditions. GD-P1 is decided (DR-0004 P-3): the ARCHITECTURE-v2
§7 lifecycle governs Foundational Concepts.
**Drafted by:** delegated agent (Executor); per Constitution Art. XII §2 by
analogy and STD-0001, the drafter must not be the sole reviewer

## Provenance and status discrepancy

*Historical record, preserved as drafting context — see Status above for
the current, decided state.* This concept had been cited across the
Agentic³ design workstream (issues #16, #17, #19) without a defining
repository artifact. Issue #17 listed AC-0001 under "existing approved
architecture," but no adoption or ratification record existed in the
repository at drafting time. Per the rule that authority is conferred
through governance relationships, not document existence (ARCHITECTURE-v2
§7), this document landed as a **proposal**. The Principal has since
recorded the adoption decision explicitly — [DR-0004](../../governance/decisions/DR-0004-Phase-0-Reconciliation-Decisions.md)
P-1 — which, not this file, confers the status.

Every definitional claim below is reconstructed from the following evidence:

- Issue #16 (scope item 7): "Knowledge Gravity metadata and update rules."
- Issue #16 (acceptance criteria): "Knowledge Gravity can be updated from
  evidence, reuse, contradiction, and supersession without becoming
  arbitrary scoring theater."
- Issue #19 (acceptance criteria): "Knowledge Gravity and Engineering Genome
  apply across every subsystem."

Every rule and definitional claim below carries one of three labels:

- **[supported: …]** — restates the cited issue text; no new decision.
- **[reconstructed]** — inferred from constitutional principles or issue
  context; holds only if the inference is right, and the review may correct
  it.
- **[proposed]** — a **new decision this document introduces**; it has no
  force until the Principal explicitly adopts it.

## Definition

**Knowledge Gravity** is metadata carried by knowledge entities (records,
patterns, decisions, principles) expressing how much justified weight the
institution currently assigns them **[reconstructed]** (issue #16 uses the
term without defining it; this sentence is the reconstruction under
review). Weight is earned and lost through four named update sources
**[supported: #16 acceptance criteria]**:

1. **Evidence** — verified outcomes that support or contradict the knowledge;
2. **Reuse** — the knowledge being applied again, with its outcome recorded;
3. **Contradiction** — new records that conflict with it;
4. **Supersession** — newer knowledge explicitly replacing it.

**[interpretation]** The gravitational metaphor: heavier knowledge attracts
more reuse, more scrutiny, and more linkage — and therefore accumulates
evidence faster in both directions. Gravity makes influence *visible and
auditable* instead of implicit in who remembers what.

## Rules

1. **Bounded update vocabulary** **[proposed, adopted by DR-0004 P-1,
   2026-07-26]**. Gravity changes *only* through the four sources above —
   no update from popularity, recency alone, author identity, citation
   count without outcomes, or manual adjustment without evidence. Issue #16
   names the four sources and warns against "arbitrary scoring theater";
   the **exclusivity** ("only these four") was a new rule this document
   proposed as the enforceable form of that warning, and is now in force by
   the Principal's decision, not merely a fact of #16.
2. **Gravity is not authority** **[reconstructed]**. High-gravity knowledge
   informs decisions; it never makes them, and it never outranks a
   Delegation, an acceptance condition, or a Principal decision. Inferred
   from Constitution Art. VIII §1 precedence applied to gravity — the
   application, not the precedence, is the inference. A heavily-reused
   pattern is still not a policy (ARCHITECTURE-v2 §5.2).
3. **Traceable updates** **[reconstructed]**. Every gravity change records
   its source event (which evidence, which reuse, which contradiction,
   which supersession) so a reviewer can reconstruct why the weight is what
   it is. Inferred by analogy to the Reasoning Ledger's traceability of
   confidence changes; #16 does not state it.
4. **Universal scope** **[supported: #19 acceptance criteria]**. Gravity
   metadata applies to knowledge entities in every subsystem, not only to
   the knowledge engine's records.
5. **Ontology owns the representation** **[supported: #16 scope item 7]**.
   The concrete metadata schema and update semantics belong to the ontology
   workstream. This document defines what gravity *means*; #16 defines how
   it is *stored and computed*.

## What this is NOT

- Not a reputation system for contributors — gravity attaches to knowledge,
  never to people or agents.
- Not a ranking algorithm to be optimized — it is an audit trail of earned
  weight.
- Not a substitute for verification — high gravity does not verify anything
  (Art. VI §5).

## Open questions (deferred past adoption — implementation-level, owned by #16)

1. Scale and representation: scalar, vector by context, or qualitative
   tiers? (Owned by #16.)
2. Decay: does unused knowledge lose gravity passively, or only through the
   four active sources? Passive decay is attractive but risks penalizing
   rarely-needed-but-critical knowledge.
3. Bootstrapping: what gravity does newly-landed knowledge start with?

## Reopening conditions

- Issue #16 lands a metadata model inconsistent with the four-source rule.
- Gravity updates are observed being used as authority (rule 2 violation).
- The Principal's review of this document contradicts the reconstruction.

## Traceability

Constitution (Art. VI evidence, Art. VIII precedence) → this concept →
ontology representation (#16) → knowledge-engine practice
(ARCHITECTURE-v2 §5.2) → future implementations. See TARP-0001.
