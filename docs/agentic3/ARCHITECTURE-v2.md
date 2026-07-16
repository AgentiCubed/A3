# Agentic³ Unified Architecture Specification v2 — DRAFT SKELETON

> **Status: draft skeleton.** This document is the consolidation target for
> issue #19. Sections marked **[BLOCKED: #16]** or **[BLOCKED: #17]** cannot be
> finalized until those design workstreams conclude; their headings and scope
> are fixed now so the consolidation has a stable shape. Everything here is
> design and specification — no product code, no database or vendor selection,
> no candidate promotion without evidence, no Constitution v1.0 rewrite
> (issue #19 non-goals).

## 0. Reading this document

This specification must be interpretable without conversational memory
(issue #19 acceptance criterion). Every referenced authority is either linked
to a repository artifact or listed in §0.1 as **not yet landed** — a reader
finding a dangling name should treat that as a defect in this document, not as
missing context they were supposed to have.

### 0.1 Input register

| Input | Repository artifact | State |
|-------|--------------------|-------|
| Constitution v1.0 | [`../governance/constitution/Constitution-v1.0.md`](../governance/constitution/Constitution-v1.0.md) | Ratified ([RR-0001](../governance/ratification/RR-0001.md)) |
| Amendment A-0001 (halt on insufficient/ambiguous authority) | [`../governance/constitution/Amendment-A-0001.md`](../governance/constitution/Amendment-A-0001.md) | Ratified |
| Amendment procedure | [`../governance/decisions/DR-0001-Constitutional-Amendment-Procedure.md`](../governance/decisions/DR-0001-Constitutional-Amendment-Procedure.md) | Adopted |
| Institutional memory system (issue #12) | [`../governance/knowledge/`](../governance/knowledge/) (README, record types, templates, transmission) | Landed; issue closed complete |
| AC-0001 Knowledge Gravity | **none** | **Not landed — exists only in issue text. Must land as an artifact before any §here that cites it can finalize.** |
| AC-0002 Engineering Genome | **none** | **Not landed — same condition as AC-0001.** |
| AC-0003 Architectural Contracts | **none** | Candidate — must land with candidate status explicit |
| AC-0004 Separation of Decision and Execution | **none** | Candidate — note: the *shipped platform* already enforces executor/evaluator separation (ADR-0004); the candidate generalizes it |
| AC-0005 Explicit Relationships | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| AC-0006 Semantic Inheritance | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| TARP-0001 traceability | **none** | **Not landed — the traceability chain (Constitution → Foundational Concepts → Ontology → Principles → Patterns → Implementations) is cited by #16/#17/#19 but exists in no artifact.** |
| Ontology & semantic graph | issue #16 (open) | **[BLOCKED: #16]** |
| Runtime Domain & continuous operation | issue #17 (open) | **[BLOCKED: #17]** |

### 0.2 Relationship to the shipped platform

The AgentiCubed platform (backend/, frontend/ — see
[`../architecture.md`](../architecture.md)) is a working implementation whose
seams (ports/adapters, executor–evaluator separation, append-only audit, the
new live event stream) are *evidence* for several candidate principles. This
specification governs the architecture of Agentic³ as a system-of-record and
engineering institution; it does not retro-specify the platform, and the
platform does not automatically instantiate this spec.

## 1. Mission

*What Agentic³ is for, in one page: a governed engineering system in which AI
and human contributors execute projects under explicit, revocable human
authority, with every material action evidenced, verifiable, and reversible in
effect or halted.*

Draws only on the Constitution's Preamble and Article I. **[DRAFT — needs
prose, no blockers]**

## 2. Authority hierarchy

*Principal → Executor → Evaluator roles (Constitution Art. II–V); delegation,
revocation, and accountability; explicit authority and execution boundaries
(issue #19 acceptance criterion: no conflicting engine definitions, explicit
authority boundaries).*

- 2.1 Roles and definitions (Art. II)
- 2.2 Sovereignty and delegation (Art. III)
- 2.3 Rights of Principals (Art. IV)
- 2.4 Separation of authority (Art. V) — and its relation to candidate AC-0004
- 2.5 Halt semantics incl. Amendment A-0001 (Art. VII §4, Art. IX, Art. X)

**[DRAFT — constitutional inputs complete; candidate AC-0004 not landed]**

## 3. Ontology **[BLOCKED: #16]**

*The canonical entity taxonomy, controlled relationship vocabulary, identity/
versioning/provenance semantics, lifecycle states, graph integrity rules, and
query semantics shared by every engine.*

Fixed subsection shape (mirrors issue #16 required outputs):

- 3.1 Root entity model
- 3.2 Entity families (actor, system, knowledge, artifact, evidence,
  governance, temporal)
- 3.3 Relationship vocabulary (source/target constraints)
- 3.4 Identity, versioning, provenance, authority semantics
- 3.5 Lifecycle states and transition constraints
- 3.6 Graph integrity rules
- 3.7 Knowledge Gravity metadata and update rules *(also blocked on AC-0001
  landing)*
- 3.8 Engineering Genome membership and evolution *(also blocked on AC-0002
  landing)*
- 3.9 Query semantics (provenance, impact, contradiction, authority, reuse)
- 3.10 AC-0005 / AC-0006 adopt–modify–reject decisions

## 4. Domains

*The domain map: Executive Domain (approved), Runtime Domain (#17), and any
domains the #16/#17 outcomes introduce. Each domain states its authority
boundary and its constitutional basis.*

- 4.1 Executive Domain **[DRAFT — cite the approving artifact; if approval
  exists only conversationally, it must land first (same rule as §0.1)]**
- 4.2 Runtime Domain **[BLOCKED: #17]** — observe, schedule, queue,
  synchronize, learn, report continuously without an active chat session,
  preserving human authority over irreversible actions
- 4.3 Domain interaction contracts **[BLOCKED: #16 relationships, #17]**

## 5. Engines

*One definition per engine — Memory, Knowledge, Governance, Verification,
Assurance, Evolution — with non-overlapping responsibilities (issue #19
acceptance criterion: no conflicting engine definitions). Each engine section
states: purpose, inputs, outputs, authority limits, ontology dependencies.*

- 5.1 Memory engine — grounded in the issue #12 system (working / project /
  institutional / evolution memory) **[DRAFT — memory records landed]**
- 5.2 Knowledge engine — record taxonomy (FR, RM, IER, RL, TET, DR, Pattern,
  Anti-pattern, Risk, Assumption, Experiment, Unexpected Success) per
  [`../governance/knowledge/README.md`](../governance/knowledge/README.md)
  **[DRAFT]**
- 5.3 Governance engine — Constitution, amendments (DR-0001), ratification,
  gate workflow (POL-0001) **[DRAFT]**
- 5.4 Verification engine — evidence and verification duties (Art. VI);
  relation to the platform's evaluation subsystem is evidence, not identity
  **[DRAFT]**
- 5.5 Assurance engine **[BLOCKED: #17 — continuous-operation assurance model]**
- 5.6 Evolution engine — candidate lifecycle owner (§7) **[DRAFT]**

## 6. Runtime **[BLOCKED: #17]**

*Continuous operation model: schedulers, queues, synchronization, learning
loops, reporting; what may run unattended; what always requires a Principal.
Constitutional constraints: Bounded Autonomy (Art. VII), Halt/Escalation
(Art. IX incl. A-0001), Emergency (Art. X).*

## 7. Candidate lifecycle

*How an Architectural Candidate (AC-XXXX) is proposed, evidenced across
repeated evaluation, and adopted / modified / rejected — never promoted by
default or by document existence (issue #16: "authority is conferred through
governance relationships, not document existence").*

**[DRAFT — the procedure can be specified now; the current candidate registry
(AC-0003…AC-0006) cannot be evaluated until the artifacts land]**

## 8. Traceability

*The TARP-0001 chain: Constitution → Foundational Concepts → Ontology →
Architectural Principles → Patterns → Implementations. Every durable
architectural statement must be traceable along explicit relationships
(issue #16 acceptance criterion).*

**[BLOCKED: TARP-0001 has no repository artifact — see §0.1. Landing it is a
prerequisite of issue #19's own acceptance criteria.]**

## 9. Safety

*Consolidated safety posture: human authority over irreversible actions,
halt-first defaults (A-0001), evidence-before-action (Art. VI), bounded
autonomy (Art. VII), emergency powers and their limits (Art. X). Cross-reference
the platform security model
([`../security-model.md`](../security-model.md)) as implementation evidence.*

**[DRAFT — constitutional inputs complete]**

## 10. Roadmap

*Sequencing to v2-final:*

1. Land the missing foundational artifacts (AC-0001, AC-0002, TARP-0001,
   candidate texts AC-0003…AC-0006) — unblocks §3.7, §3.8, §7, §8
2. Close issue #16 (ontology) — unblocks §3, §4.3
3. Close issue #17 (Runtime Domain) — unblocks §4.2, §5.5, §6
4. Fill §1, §2, §5.1–5.4, §5.6, §9 (no blockers — can proceed now)
5. Consolidation review under STD-0001 (context-complete review), then
   ratify per the gate workflow (POL-0001)

## 11. Open risks and reopening conditions

- **R1 — Concept drift before landing:** Knowledge Gravity / Engineering
  Genome are cited across issues but defined nowhere durable; every citation
  is currently unverifiable. *Reopen §3/§7/§8 if the landed definitions differ
  from issue-text usage.*
- **R2 — Platform/spec conflation:** the shipped platform's seams look like
  the candidate principles; treating shipped code as proof of adoption would
  promote candidates without governance. *Reopen §0.2 if any engine section
  starts citing code as authority.*
- **R3 — Engine overlap:** Verification vs. Assurance boundaries are
  undefined until #17 lands. *Reopen §5 on #17 closure.*
- **R4 — Amendment interactions:** future amendments (post A-0001) may alter
  halt semantics assumed in §6/§9. *Reopen on any Article VII/IX/X amendment.*
