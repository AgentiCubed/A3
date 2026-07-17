# AC-0002 — Engineering Genome

**Type:** Foundational Concept (Architectural Candidate)
**Status:** Proposed — reconstructed from issue-text usage; awaiting Principal
review and an explicit adoption decision. This document assumes the
ARCHITECTURE-v2 §7 candidate lifecycle governs Foundational Concepts — that
applicability is itself a **proposed governance decision** (GD-P1, recorded
in ARCHITECTURE-v2 §7), not an established rule.
**Drafted by:** delegated agent (Executor); the drafter must not be the sole
reviewer (STD-0001)

## Provenance and status discrepancy

Cited across issues #16, #17, and #19 without a defining repository
artifact; issue #17 lists AC-0002 under "existing approved architecture," but
no adoption record exists. As with AC-0001, this document therefore lands as
a **proposal** — if adoption has already occurred, the review of this
document is the moment to record that decision explicitly.

Evidence base for the reconstruction:

- Issue #16 (scope item 8): "Engineering Genome membership and evolution
  rules."
- Issue #16 (acceptance criteria): "Engineering Genome membership is
  explicit, versioned, and reversible."
- Issue #19 (acceptance criteria): "Knowledge Gravity and Engineering Genome
  apply across every subsystem."

Every rule below carries one of three labels: **[supported: …]** (restates
cited issue text), **[reconstructed]** (inferred; review may correct it), or
**[proposed]** (a new decision this document introduces; no force until the
Principal adopts it). Prose marked **[interpretation]** is explanatory
framing, weaker than a rule.

## Definition

The **Engineering Genome** is the explicit, versioned set of principles,
patterns, and standards that currently define *how Agentic³ engineers* —
the institution's inheritable identity. What is in the genome is expressed
in every subsystem the institution builds; what is not in the genome is
local practice, not institutional identity.

**[interpretation]** The genetic metaphor is about inheritance and
expression, not permanence: new work inherits the genome by default,
the genome is expressed as observable engineering behavior, and mutations
(changes to membership) are deliberate, recorded events — never silent
drift.

## Rules

1. **Membership is explicit** **[supported: #16 acceptance criteria]**, and
   **[reconstructed]** in its elaboration: resemblance, habit, or wide usage
   do not confer membership. #16 states the explicitness; the anti-drift
   elaboration is inferred from it (and parallels AC-0001 rule 1, which is
   itself proposed, not established).
2. **Membership is versioned** **[supported: #16 acceptance criteria]**.
   The genome has identifiable states over time; any element's membership
   history (added, revised, removed, by which decision) is reconstructible.
3. **Membership is reversible** **[supported: #16 acceptance criteria]**;
   the addition that removal **never erases history** is
   **[reconstructed]** by analogy to Constitution Art. XII §4 and the
   knowledge system's append-only maintenance rule.
4. **Adoption is governance** **[proposed]**. Entry to the genome follows
   the candidate lifecycle (ARCHITECTURE-v2 §7): proposed → evaluated
   repeatedly → decided under authority traceable to a Principal, stewarded
   but not decided by the evolution engine (§5.6). This rule depends on the
   proposed governance decision **GD-P1** (does §7 govern Foundational
   Concepts and genome entries?) and has no force until that decision is
   made.
5. **Universal expression** **[supported: #19 acceptance criteria]** in its
   first clause — genome elements apply across every subsystem. The second
   clause — a subsystem that cannot satisfy an element is a finding to
   surface, not an exemption to assume — is **[reconstructed]**.
6. **Ontology owns the representation** **[supported: #16 scope item 8]**.
   How membership, versioning, and evolution are modeled belongs to the
   ontology workstream.

## Relationship to Knowledge Gravity (AC-0001)

**[interpretation]** Gravity measures earned weight; the genome records
adopted identity. High gravity is the natural *evidence trail* that
justifies proposing an element for genome membership, but gravity never
promotes anything automatically — promotion is always a recorded decision
(rule 4). The two concepts are complementary and deliberately not fused.

## What this is NOT

- Not a style guide — genome elements are principles and patterns with
  recorded rationale, not formatting preferences.
- Not immutable doctrine — reversibility is a defining rule, not an edge
  case.
- Not the Constitution — the genome governs engineering practice and is
  subordinate to constitutional authority (Art. XI).

## Open questions (for the adoption decision)

1. Granularity: are genome elements whole principles (AC-scale), patterns,
   or both?
2. Seeding: do the shipped platform's proven seams (ports/adapters,
   executor–evaluator separation, append-only audit) become the first
   membership *proposals*? They are strong candidates precisely because
   their evidence trail already exists — but per §0.2 discipline, shipped
   code is feasibility evidence, not adoption.
3. Expression checking: how is "applies across every subsystem" verified in
   practice — review checklist, tooling, or both? (Likely a #17 runtime
   concern.)

## Reopening conditions

- Issue #16 lands membership/evolution semantics inconsistent with rules
  1–3.
- Genome membership is observed being claimed from resemblance or habit
  (rule 1 violation).
- The Principal's review contradicts the reconstruction.

## Traceability

Constitution (Art. III authority, Art. XI supremacy) → this concept →
ontology representation (#16) → evolution-engine practice
(ARCHITECTURE-v2 §5.6, §7) → future implementations. See TARP-0001.
