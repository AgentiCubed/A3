# AC-0001 — Knowledge Gravity

**Type:** Foundational Concept (Architectural Candidate)
**Status:** Proposed — reconstructed from issue-text usage; awaiting Principal
review and an explicit adoption decision under the candidate lifecycle
(ARCHITECTURE-v2 §7)
**Drafted by:** delegated agent (Executor); per Constitution Art. XII §2 by
analogy and STD-0001, the drafter must not be the sole reviewer

## Provenance and status discrepancy

This concept has been cited across the Agentic³ design workstream (issues
#16, #17, #19) without a defining repository artifact. Issue #17 lists
AC-0001 under "existing approved architecture," but no adoption or
ratification record exists in the repository. Per the rule that authority is
conferred through governance relationships, not document existence
(ARCHITECTURE-v2 §7), this document lands as a **proposal**. If the Principal
has in fact already adopted the concept, the adoption decision should be
recorded explicitly when this document is reviewed — that record, not this
file, confers the status.

Every definitional claim below is reconstructed from the following evidence:

- Issue #16 (scope item 7): "Knowledge Gravity metadata and update rules."
- Issue #16 (acceptance criteria): "Knowledge Gravity can be updated from
  evidence, reuse, contradiction, and supersession without becoming
  arbitrary scoring theater."
- Issue #19 (acceptance criteria): "Knowledge Gravity and Engineering Genome
  apply across every subsystem."

Anything beyond those sources is marked **[interpretation]**.

## Definition

**Knowledge Gravity** is metadata carried by knowledge entities (records,
patterns, decisions, principles) expressing how much justified weight the
institution currently assigns them. Weight is earned and lost through four —
and only four — update sources:

1. **Evidence** — verified outcomes that support or contradict the knowledge;
2. **Reuse** — the knowledge being applied again, with its outcome recorded;
3. **Contradiction** — new records that conflict with it;
4. **Supersession** — newer knowledge explicitly replacing it.

**[interpretation]** The gravitational metaphor: heavier knowledge attracts
more reuse, more scrutiny, and more linkage — and therefore accumulates
evidence faster in both directions. Gravity makes influence *visible and
auditable* instead of implicit in who remembers what.

## Rules

1. **Bounded update vocabulary.** Gravity changes only through the four
   sources above. No update from popularity, recency alone, author identity,
   citation count without outcomes, or manual adjustment without evidence —
   the "arbitrary scoring theater" failure mode issue #16 names.
2. **Gravity is not authority.** High-gravity knowledge informs decisions;
   it never makes them, and it never outranks a Delegation, an acceptance
   condition, or a Principal decision (Constitution Art. VIII §1).
   A heavily-reused pattern is still not a policy (ARCHITECTURE-v2 §5.2).
3. **Traceable updates.** Every gravity change records its source event
   (which evidence, which reuse, which contradiction, which supersession),
   so a reviewer can reconstruct why the weight is what it is — the same
   traceability the Reasoning Ledger demands of confidence changes.
4. **Universal scope.** Gravity metadata applies to knowledge entities in
   every subsystem (issue #19), not only to the knowledge engine's records.
5. **Ontology owns the representation.** The concrete metadata schema and
   update semantics belong to the ontology workstream (issue #16, scope
   item 7). This document defines what gravity *means*; #16 defines how it
   is *stored and computed*.

## What this is NOT

- Not a reputation system for contributors — gravity attaches to knowledge,
  never to people or agents.
- Not a ranking algorithm to be optimized — it is an audit trail of earned
  weight.
- Not a substitute for verification — high gravity does not verify anything
  (Art. VI §5).

## Open questions (for the adoption decision)

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
