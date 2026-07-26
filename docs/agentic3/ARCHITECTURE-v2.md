# Agentic³ Unified Architecture Specification v2 — DRAFT

> **Status: draft — the single canonical consolidation target.** Per the
> Phase 0 Reconciliation Record
> ([`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §1), this document
> is the one canonical v2 specification; the former integration skeleton at
> `../governance/architecture/Unified-Agentic3-Architecture-Specification-v2.md`
> is superseded, its unique material harvested into §6 and §12 here with
> statuses preserved. Sections drafted from ratified and adopted sources are
> normative-draft; material marked **candidate** or **[DECISION PENDING:
> P-n]** awaits the Principal decisions queued in the Reconciliation Record.
> Everything here is design and specification — no product code, no database
> or vendor selection, no candidate promotion without evidence, no
> Constitution v1.0 rewrite (issue #19 non-goals).

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
| AC-0001 Knowledge Gravity | [`concepts/AC-0001-knowledge-gravity.md`](concepts/AC-0001-knowledge-gravity.md) | Proposed — landed as a reconstruction from issue-text usage; Principal adoption decision pending (§7 state 1) |
| AC-0002 Engineering Genome | [`concepts/AC-0002-engineering-genome.md`](concepts/AC-0002-engineering-genome.md) | Proposed — same condition as AC-0001 |
| AC-0003 Architectural Contracts | **none** | Candidate — must land with candidate status explicit |
| AC-0004 Separation of Decision and Execution | **none** | Candidate — note: the *shipped platform* already enforces executor/evaluator separation (ADR-0004); the candidate generalizes it |
| AC-0005 Explicit Relationships | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| AC-0006 Semantic Inheritance | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| TARP-0001 traceability | [`TARP-0001-traceability-protocol.md`](TARP-0001-traceability-protocol.md) | Proposed — chain and review rules landed; the **Upward Compatibility Rule** still unlanded; relation to active STD-0002 is decision **P-4** |
| Ontology & semantic graph | [`../governance/ontology/`](../governance/ontology/) ONTO-0001…0006 | Landed as **Drafts** (no owner/version declared); adoption review pending; known conflicts recorded in [`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §2–§5 |
| Runtime Domain & continuous operation | [`../governance/runtime/Runtime-Domain-Specification-v1.0.md`](../governance/runtime/Runtime-Domain-Specification-v1.0.md) | **Adopted architecture baseline** (issue #17 closed) |
| Implementation Blueprint | [`IMPLEMENTATION-BLUEPRINT.md`](IMPLEMENTATION-BLUEPRINT.md) | Landed; divergences from the Runtime spec reconciled as rulings R-1…R-18 in [`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §4 |
| Phase 0 Reconciliation Record | [`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) | Proposed — mechanical rulings applied by this revision; decisions P-1…P-7 reserved for the Principal |
| Reversible-work standing policy | [`../governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md`](../governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md) | Proposed — confers no authority until ratified |

### 0.2 Relationship to the shipped platform

The AgentiCubed platform (backend/, frontend/ — see
[`../architecture.md`](../architecture.md)) is a working implementation whose
seams (ports/adapters, executor–evaluator separation, append-only audit, the
new live event stream) are *evidence* for several candidate principles. This
specification governs the architecture of Agentic³ as a system-of-record and
engineering institution; it does not retro-specify the platform, and the
platform does not automatically instantiate this spec.

## 1. Mission

Agentic³ exists to coordinate human and autonomous contributors through
planned, reviewable, evidence-backed work (Constitution, Preamble). Its
architecture answers one question: how does an engineering institution stay
trustworthy when the capability and diversity of its contributors — human and
AI — grow faster than any individual's ability to supervise them?

The answer the Constitution commits to is structural, not supervisory.
Authority, verification, accountability, and institutional continuity must not
depend on individual judgment or temporary context (Preamble). Instead:

- **Authority is explicit and revocable.** All authority originates with a
  Principal and reaches Executors and Evaluators only through Delegation with
  a defined Boundary (Art. III). Nothing in the system may obstruct
  revocation (Art. IV §3).
- **Claims require evidence.** A claim about a Material Action must be
  supported by inspectable Evidence proportionate to its consequences
  (Art. VI §1), and no Executor may be the sole source of evidence for its
  own success (Art. VI §3).
- **Work that cannot proceed legitimately halts.** When authority is
  insufficient or ambiguous, the required behavior is Halt — never inference
  of broader authority (Art. VII §4, as clarified by Amendment A-0001).
- **The institution remembers.** Failures, reasoning, and idea evolution are
  preserved as context-complete records (§5.1–§5.2) so future contributors
  reuse the search path, not just its conclusion.

Two boundaries keep the mission honest. First, governance exists to improve
the product; the product does not exist to justify governance (Preamble).
Second, the Constitution governs only enduring matters — authority, rights,
evidence, autonomy, precedence, emergency, supremacy, amendment (Art. I §1) —
and everything else, including this specification's subordinate details, must
remain revisable without constitutional change (Art. I §2).

## 2. Authority hierarchy

### 2.1 Roles (Art. II)

Three roles exhaust the authority model. A **Principal** holds ultimate
authority and accountability within a defined scope. An **Executor** performs
work under Delegation. An **Evaluator** determines whether work satisfies
established conditions. Roles are positional, not personal: the same entity
may be Principal in one scope and Executor in another, but never Executor and
sole Evaluator of the same Material Action (Art. V §3).

For current repository work, POL-0001 names the concrete binding: James
Richmond is the Principal for AgentiCubed engineering; delegated agents act as
Executors within gate Boundaries. This binding is a subordinate-instrument
fact and may change without touching this section's model.

### 2.2 Sovereignty and delegation (Art. III)

Every Delegation names its originating Principal, its receiving Executor or
Evaluator, and its Boundary (Art. III §1). Three structural consequences
follow:

1. **No authority is created downstream.** A Principal delegates only what it
   possesses; Delegation cannot enlarge itself; sub-delegation exists only
   when expressly permitted (Art. III §2).
2. **Accountability does not transfer.** The responsible Principal remains
   ultimately accountable for delegated work, while the Executor or Evaluator
   remains responsible for its own actions within the grant (Art. III §3).
3. **Revocation always works.** No Delegation may prevent its own revocation,
   and revocation never erases Evidence or the historical record
   (Art. III §4).

### 2.3 Rights of Principals (Art. IV)

The Principal's rights form the fixed points every engine in §5 must respect:
intent (no Executor or Evaluator may redefine it), evidence (nothing Material
may be withheld; every Material Action must remain traceable to its
Delegation), revocation (unobstructable), and ownership (artifacts, Evidence,
and governance records belong to the Principal absent explicit transfer).
No subordinate instrument — including this specification — may diminish these
rights (Art. IV §5).

### 2.4 Separation of authority (Art. V)

Where any part of a Material Action is delegated, no single Executor or
Evaluator controls execution, verification, *and* acceptance (Art. V §1). An
Executor's account of its own work is Evidence but never Verification
(Art. V §3), and Delegations must preserve enough independence for
Verification to genuinely challenge the Executor (Art. V §4 — the mechanism
lives outside the Constitution, and outside this section).

Relation to candidate **AC-0004 (Separation of Decision and Execution)**: the
constitutional rule separates execution from verification/acceptance of the
*same action*; the candidate proposes a broader separation between deciding
and doing. They are related but not identical, and the shipped platform's
executor/evaluator enforcement (ADR-0004) is evidence for the constitutional
rule — not for the candidate, which remains unlanded and unevaluated (§0.1).

### 2.5 Halt semantics (Art. VII §4, Art. IX, Art. X, A-0001)

The halt model has three tiers:

- **Principal halts** are unrestricted within the Principal's authority
  (Art. IX §1).
- **Executor/Evaluator halts** are restricted to the exhaustive Art. IX §2
  grounds (boundary exceedance, evidence corruption or concealment,
  unauthorized Material Action, constitutional violation, fault propagation).
  Amendment A-0001 closes the seam between this list and Art. VII §4: a halt
  for insufficient or ambiguous authority *is* an Art. IX halt, grounded in
  actual or threatened Boundary exceedance.
- **Emergency actions** (Art. X) activate only narrow protective authority —
  preserve a halt, preserve evidence, prevent immediate Material harm, reach
  a safe condition — and never completion, verification, expansion,
  concealment, or amendment.

Initiating a halt confers no authority over what happens next; correction,
resumption, acceptance, abandonment, and termination each require authority
independently established under Art. III (Art. IX §3). Non-convergence never
justifies indefinite execution or fabricated success (Art. IX §5).

## 3. Ontology **[DRAFTS LANDED — adoption review pending]**

*The canonical entity taxonomy, controlled relationship vocabulary, identity/
versioning/provenance semantics, lifecycle states, graph integrity rules, and
query semantics shared by every engine.*

The representation now exists as six **Draft** documents,
[`ONTO-0001…ONTO-0006`](../governance/ontology/), covering every subsection
below (109 entity types, 64 relationship types, 13 integrity rules, 12
canonical queries). They are not yet adopted, declare no owner or version,
and carry known conflicts with AC-0001/AC-0002 recorded in
[`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §2, §3, and §5 —
resolution of those conflicts is bundled into decisions **P-1…P-3**.

Fixed subsection shape (mirrors issue #16 required outputs):

- 3.1 Root entity model
- 3.2 Entity families (actor, system, knowledge, artifact, evidence,
  governance, temporal)
- 3.3 Relationship vocabulary (source/target constraints)
- 3.4 Identity, versioning, provenance, authority semantics
- 3.5 Lifecycle states and transition constraints
- 3.6 Graph integrity rules
- 3.7 Knowledge Gravity metadata and update rules *(AC-0001 landed as a
  proposal; also awaiting its adoption decision)*
- 3.8 Engineering Genome membership and evolution *(AC-0002 landed as a
  proposal; also awaiting its adoption decision)*
- 3.9 Query semantics (provenance, impact, contradiction, authority, reuse)
- 3.10 AC-0005 / AC-0006 adopt–modify–reject decisions

## 4. Domains

*The domain map: Executive Domain (approved), Runtime Domain (#17), and any
domains the #16/#17 outcomes introduce. Each domain states its authority
boundary and its constitutional basis.*

- 4.1 Executive Domain **[DRAFT — cite the approving artifact; if approval
  exists only conversationally, it must land first (same rule as §0.1)]**
- 4.2 Runtime Domain — **defined by the adopted
  [Runtime Domain Specification v1.0](../governance/runtime/Runtime-Domain-Specification-v1.0.md)**:
  observe, schedule, queue, synchronize, learn, report continuously without
  an active chat session, preserving human authority over irreversible
  actions. See §6.
- 4.3 Domain interaction contracts **[PARTIAL — relationship vocabulary
  landed as Draft (ONTO-0002); adoption pending]**
- 4.4 **Candidate (harvested, unregistered):** the superseded integration
  skeleton asserted an "**Intelligence**" domain (peer of Executive,
  Assurance, Runtime) that appears nowhere else in the repository. It is
  recorded here as an unregistered candidate only — the Implementation
  Blueprint independently uses "Intelligence" as a package grouping for the
  Verification/Memory/Knowledge/Evolution engines, which is implementation
  layout, not domain authority. Registering it as a real domain requires a
  candidate artifact and the §7 lifecycle.

## 5. Engines

An **engine** is a named institutional capability with a bounded
responsibility, defined inputs and outputs, and explicit authority limits.
Engines are roles the institution performs, not services or processes — how
each is realized (by people, agents, tooling, or the platform) is an
implementation choice outside this specification. The definitions below are
deliberately non-overlapping (issue #19 acceptance criterion); §5.5 remains
open, and its eventual definition may narrow — never contradict — the others.

Every engine operates under §2: engines hold no authority of their own, only
authority reaching them through Delegation.

### 5.1 Memory engine

**Purpose:** preserve institutional state across time and contributors, in
four bounded stores (issue #12): *working memory* (the live context of an
active effort — legitimate but disposable), *project memory* (the durable
record of one project), *institutional memory* (cross-project records:
failures, reasoning, patterns), and *evolution memory* (how beliefs and
designs changed, and why).

**Inputs:** capture triggers defined by the knowledge system (failures,
decisions, belief changes, unexpected successes). **Outputs:** durable,
append-only records with stable identifiers. **Authority limits:** memory
records confer no authority (§0.1's rule generalized: existence of a document
is never authority — Art. XI gives that role to the Constitution and
instruments traceable to a Principal). Corrections preserve the prior
statement, the correction, the evidence, and the date; historical claims are
never erased (knowledge README, Maintenance).

**Governing thesis** (issue #12): the durable unit of learning is not a
conclusion but the traceable transition
`prior model → disturbing evidence → revised model → tested consequence`.

### 5.2 Knowledge engine

**Purpose:** turn preserved memory into reusable engineering knowledge by
enforcing the record taxonomy and its quality rules.

**Record taxonomy** (per
[`../governance/knowledge/README.md`](../governance/knowledge/README.md)):
Failure Record (FR — observed vs. expected behavior, evidence, impact,
correction, verification, unresolved facts; no blame, no motive speculation),
Rumination (RM — hypothesis-level analysis linked to an FR, with rejected
explanations and updated mental models), Idea Evolution Record (IER — the
chronology of an idea including discarded branches and reopening conditions),
and Reasoning Ledger (RL — claim, assumptions, evidence, counter-evidence,
alternatives, confidence before/after, the trigger that changed confidence,
remaining uncertainty). Records cross-link by stable identifier
(`FR-NNNN`, `RM-NNNN`, `IER-NNNN`, `RL-NNNN`).

**Quality rules the engine enforces:**

- *Context-complete review*: a record fails review if a future contributor
  must ask what happened, where, on what evidence, which statements are fact
  versus interpretation, or what changed as a result.
- *Fact/interpretation separation*: interpretation must remain visibly
  distinct from verified fact — the epistemics that Art. VI §5 (honest state)
  demands of claims, applied to records.
- *Transmission discipline*: retelling knowledge adds value only when it
  improves discoverability, context, validation, applicability, correction,
  connection, or resilience; otherwise transmission degrades it.

**Authority limits:** knowledge records inform decisions; they never make
them. A Pattern is not a policy.

### 5.3 Governance engine

**Purpose:** maintain the instruments through which authority flows — the
Constitution and its amendments, ratification records, and the subordinate
policy/procedure/standard layer — and operate the gate workflow that turns
authority into authorized work.

**Constitutional layer:** amendments follow Art. XII — complete proposal
(deficiency, change, affected authority, why no subordinate instrument
suffices, interpretive effect), independent context-complete review by a
non-drafter, explicit Principal ratification, durable historical continuity.
DR-0001 operationalizes this procedure; RR-0001 is the ratification record of
the v1.0 baseline.

**Subordinate layer:** policies (POL), procedures (PROC), standards (STD),
and templates (TPL) govern what the Constitution deliberately leaves open
(Art. I §2). They hold authority only while consistent with the Constitution
(Art. XI) and traceable to a Principal (Art. VIII §4).

**Operating model:** the gate workflow (POL-0001). The Principal defines each
gate (objective, scope, acceptance conditions, boundary, expected evidence,
stop conditions); the Executor acts within it and returns complete evidence;
the Principal reviews and decides — next gate, correction gate, or halt. No
work begins without authorization; silence is never authority.

**Authority limits:** the governance engine administers instruments; it never
ratifies. Ratification and gate authorization belong to Principals alone
(Art. XII §3, POL-0001).

### 5.4 Verification engine

**Purpose:** evaluate Evidence against established conditions (Art. II) and
maintain the institution's honest state.

**Duties, all from Art. VI:** demand evidence proportionate to consequences
(§1); keep evidence inspectable by those authorized to review it (§2); refuse
sole self-attestation — no Executor is the only source of evidence for its
own success (§3); insist acceptance conditions exist *before* execution and
that only the responsible Principal changes them, with the change preserved
as evidence (§4); never represent unverified work as verified (§5); preserve
evidence long enough for verification, accountability, and authorized review
(§6).

**Structural position:** verification is independent by construction
(Art. V §4) and cannot be collapsed into execution (Art. V §1, §3).

**Relation to the platform:** the shipped evaluation subsystem — deterministic
rubrics, evaluator agents, enforced executor/evaluator separation (ADR-0004)
— is an *implementation instance* and supporting evidence for this engine's
feasibility. It is not the engine's definition, and platform behavior never
substitutes for constitutional duty (§0.2).

**Authority limits:** verification determines whether conditions are
satisfied; acceptance remains the Principal's (Art. IV §1, Art. IX §3).

### 5.5 Assurance engine **[DECISION PENDING: P-5]**

*Continuous-operation assurance: how the institution stays confident in an
always-on system between explicit verification events.*

Issue #17 has closed; the adopted Runtime Domain Specification and the
Implementation Blueprint both give Assurance a consistent shape: it issues
tri-state readiness decisions (`ready | not_ready | more_evidence_required`)
over an evidence set, unresolved risks, a confidence statement, a validity
window, and reopening conditions — and it **cannot execute, mutate evidence,
grant authority, or replace human acceptance**. The proposed boundary with
§5.4 (harvested from the superseded skeleton, consistent with both Runtime
sources): *Verification evaluates evidence; Assurance evaluates readiness
and unresolved risk; Governance supplies authority.* Adopting that sentence
closes risk R3 and is decision **P-5**.

### 5.6 Evolution engine

**Purpose:** change the institution's own architecture safely — owner of the
candidate lifecycle (§7) and steward of evolution memory (§5.1).

**Inputs:** candidate principles (AC-XXXX), evidence from repeated
application, contradictions surfaced by the knowledge engine, and reopening
conditions attached to prior decisions. **Outputs:** adopt / modify / reject
decisions with their reasoning preserved (RL), updates to the traceability
chain (§8), and amendments proposed — never enacted — when a deficiency is
genuinely constitutional (Art. XII §1).

**Authority limits:** the evolution engine evaluates and recommends;
adoption is a governance act requiring authority traceable to a Principal
(§7). It may not promote a candidate by accumulation of citations, habit, or
document age — the failure mode issue #16 names "scoring theater" and R1/R2
track.

## 6. Runtime

*Continuous operation model: schedulers, queues, synchronization, learning
loops, reporting; what may run unattended; what always requires a Principal.
Constitutional constraints: Bounded Autonomy (Art. VII), Halt/Escalation
(Art. IX incl. A-0001), Emergency (Art. X).*

Defined by the adopted
[Runtime Domain Specification v1.0](../governance/runtime/Runtime-Domain-Specification-v1.0.md)
(issue #17 closed) as elaborated by the
[Implementation Blueprint](IMPLEMENTATION-BLUEPRINT.md); where the two
diverge, the reconciled rulings R-1…R-18 in
[`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §4 control. The
load-bearing facts:

- Ten components (RT-101 Event Observer … RT-110 Notifier/Escalation
  Router), each with explicit authority and "cannot" constraints.
- The Runtime manages work; it holds no product, constitutional, or release
  authority and cannot certify its own success. A Work Item is a proposal,
  not authorization.
- It may initiate only **reversible, pre-authorized work classes** — the
  standing policy instrument is
  [DR-0003](../governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md)
  (Proposed). Irreversible actions require an explicit, current, unexpired,
  unrevoked human authorization artifact.
- Schedule, timeout, urgency, silence, inferred intent, and model confidence
  never authorize anything (reconciled union, R-8).
- Harvested runtime-authority rules (consistent with the adopted spec):
  *Runtime may propose capture but cannot promote its own records to
  institutional truth; Runtime observations are signals, not authority.*

## 7. Candidate lifecycle

An **Architectural Candidate (AC-XXXX)** is a proposed enduring principle of
Agentic³ architecture. Candidates exist so the institution can *try* a
principle repeatedly before committing to it — the opposite of ratifying
ideas at the moment of enthusiasm.

**Lifecycle states:**

1. **Proposed.** The candidate lands as a repository artifact stating: the
   principle, the problem it addresses, its predicted consequences, what
   evidence would support or refute it, and its reopening conditions. Until
   the artifact lands, the candidate does not exist for governance purposes
   (§0.1) — issue text is a proposal to propose.
2. **Under evaluation.** The candidate is applied where it naturally fits and
   each application is recorded with outcome evidence (RL entries linking to
   the candidate). Evaluation is repeated: a single success or failure is an
   anecdote, not a verdict (issue #16 acceptance criterion: decisions "only
   after repeated evaluation").
3. **Decided.** The evolution engine (§5.6) synthesizes the evidence and
   recommends **adopt**, **modify** (returning to state 1 as a revised
   proposal), or **reject**. The decision itself is a governance act under
   authority traceable to a Principal (§5.3), preserved with its full
   reasoning ledger.
4. **Adopted / Rejected — both with reopening conditions.** Adoption adds the
   principle to the traceability chain (§8) and, where issue #16's terms
   apply, to Engineering Genome membership — which is "explicit, versioned,
   and reversible." Rejection preserves the candidate, its evidence, and what
   would justify revisiting it. Neither state erases history (Art. XII §4 by
   analogy; knowledge README, Maintenance).

**Hard rules:**

- Authority is conferred through governance relationships, never through
  document existence, citation frequency, or age (issue #16).
- Shipped code that resembles a candidate is evidence of feasibility, not
  adoption (§0.2, risk R2).
- No candidate becomes constitutional by adoption; if a candidate's substance
  belongs in the Constitution, that is an Art. XII amendment with its own
  procedure.

**Proposed governance decision GD-P1 — applicability to Foundational
Concepts.** This section was written for Architectural Candidates (chain
layer 4). Whether the same lifecycle formally governs **Foundational
Concepts** (chain layer 2 — AC-0001, AC-0002) has never been decided; the
landed concept proposals *assume* it does, and flag that assumption. The
proposal: **the §7 lifecycle governs layer-2 Foundational Concepts and
Engineering Genome membership exactly as it governs layer-4 candidates.**
Alternatives the Principal may prefer: a stricter procedure for layer 2
(closer to Art. XII amendment discipline, since concepts sit directly under
the Constitution), or a distinct lightweight track. Until decided, no
lifecycle claim about a Foundational Concept is enforceable. Decision owner:
the Principal (Art. III).

**Current registry:** AC-0001 and AC-0002 have landed as proposals (state 1;
see §0.1) with every rule labeled supported/reconstructed/proposed;
AC-0003…AC-0006 remain named candidates awaiting artifacts and cannot enter
state 2 until state 1 is satisfied (§10 item 1).

## 8. Traceability

*The TARP-0001 chain: Constitution → Foundational Concepts → Ontology →
Architectural Principles → Patterns → Implementations. Every durable
architectural statement must be traceable along explicit relationships
(issue #16 acceptance criterion).*

**[PARTIALLY UNBLOCKED: TARP-0001 landed as a proposed protocol
([`TARP-0001-traceability-protocol.md`](TARP-0001-traceability-protocol.md))
defining the chain and review rules; the relationship semantics a "trace" is
made of now exist as Draft (ONTO-0002, `TRACES_TO`). This section finalizes
after the Principal's decision **P-4**, which also resolves the instrument
naming: STD-0002 (Active standard) implements the review discipline
TARP-0001 (Proposed protocol) describes, and the superseded skeleton's
eleven-stage chain variant (…candidates, contracts, work, Verification,
Assurance/Governance, Memory, Learning) is recorded as a proposed extension
of the six-stage chain above, not a replacement.]**

## 9. Safety

Agentic³'s safety posture is *structural*: it does not depend on any
contributor — human or AI — choosing well under pressure, because the
architecture removes the authority to choose badly.

**The five load-bearing properties:**

1. **Human authority over what matters.** Every Material Action traces to a
   Delegation from a Principal (Art. III, Art. VII §3); intent belongs to the
   Principal alone (Art. IV §1); revocation is unobstructable (Art. IV §3).
   Autonomy is real but bounded — execution without contemporaneous direction
   is valid *only inside* an existing Delegation (Art. VII §1).
2. **Halt-first defaults.** Insufficient or ambiguous authority means halt,
   never inference (Art. VII §4, A-0001). Objectives, deadlines, and progress
   expectations authorize nothing beyond the Boundary (Art. VII §5), and
   repeated failure never justifies indefinite execution or fabricated
   success (Art. IX §5). Halting is the required behavior, not a failure mode
   (POL-0001).
3. **Evidence before belief.** Claims require proportionate, inspectable
   evidence (Art. VI §1–2); no executor self-attests alone (Art. VI §3);
   unverified work is never represented as verified (Art. VI §5). Acceptance
   conditions predate execution (Art. VI §4), which forecloses success-
   criteria drift after the fact.
4. **No self-expansion, no laundering.** An Executor cannot expand its own
   authority or create a Delegation for itself (Art. VII §2) — and authority
   obtained *through another Executor* stays subject to the original
   Boundary, closing the confused-deputy path. Absence of prohibition is not
   Delegation (Art. VII §5).
5. **Emergencies stay narrow.** Emergency authority covers only halting,
   evidence preservation, harm prevention, and safe states (Art. X §2); it
   can never complete, verify, expand, conceal, or amend (Art. X §3), and it
   expires rather than normalizes (Art. X §5).

**Precedence under conflict:** when interests collide, protection beats
continuation (Art. VIII §2) and ambiguity resolves toward *less* authority
(Art. VIII §3). The full order — Constitution, Principal rights, Principal
decisions, Delegation/Boundary, acceptance conditions, and only then
continuation or efficiency — is Art. VIII §1.

**Implementation evidence (not definition):** the shipped platform exhibits
these properties concretely — RBAC and default-deny tool permissions, agents
barred from changing their own permissions, human approval gates before
irreversible actions, append-only audit/execution/evaluation records, and
secrets referenced by key rather than value
([`../security-model.md`](../security-model.md)). Per §0.2, this is evidence
the posture is buildable, not the posture itself.

## 10. Roadmap

*Sequencing to v2-final:*

1. Land the missing foundational artifacts — **partially done**: AC-0001,
   AC-0002, and TARP-0001 landed as proposals (adoption decisions pending);
   candidate texts AC-0003…AC-0006 and the Upward Compatibility Rule still
   unlanded
2. ~~Close issue #16 (ontology)~~ — **drafts landed** (ONTO-0001…0006);
   adoption review and conflict resolution pending (P-1…P-3)
3. ~~Close issue #17 (Runtime Domain)~~ — **done** (Runtime Domain
   Specification v1.0 adopted); §4.2, §5.5, §6 updated this revision
4. ~~Fill §1, §2, §5.1–5.4, §5.6, §7, §9~~ — **done** (prior revision)
5. ~~Reconcile the parallel v2 specifications~~ — **done** (this revision;
   [`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §1)
6. Principal decisions P-1…P-7, then the remaining Phase 0 deliverables
   (contract examples with owners/versions, authority matrix,
   precedence/retention records)
7. Consolidation review under STD-0001 (context-complete review), then
   ratify per the gate workflow (POL-0001)

## 11. Open risks and reopening conditions

### 11.1 Named risks

- **R1 — Reconstruction risk (updated):** Knowledge Gravity, Engineering
  Genome, and TARP-0001 now exist as landed *reconstructions* from issue-text
  usage, awaiting Principal adoption decisions. The original drift risk is
  narrowed but not closed: the reconstructions may not match the Principal's
  intent; four documents record AC-0001/0002 as "adopted" while the concept
  documents themselves say "proposed"; and **two of AC-0001's reopening
  conditions are already met**
  ([`PHASE0-RECONCILIATION.md`](PHASE0-RECONCILIATION.md) §2). *Resolution is
  decisions P-1…P-3.*
- **R2 — Platform/spec conflation:** the shipped platform's seams look like
  the candidate principles; treating shipped code as proof of adoption would
  promote candidates without governance. *Reopen §0.2 if any engine section
  starts citing code as authority.*
- **R3 — Engine overlap:** the Verification/Assurance boundary has a
  proposed resolution (§5.5). *Closes on decision P-5.*
- **R4 — Amendment interactions:** future amendments (post A-0001) may alter
  halt semantics assumed in §6/§9. *Reopen on any Article VII/IX/X amendment.*

### 11.2 Standing design risks (harvested)

- Relationship vocabulary and metadata may become too broad or costly to curate.
- Engine ownership may become ambiguous for composite artifacts.
- Knowledge Gravity may degrade into false precision or popularity scoring.
- Genome membership may become difficult to reverse in practice.
- Semantic contradiction detection may overstate conflict without scope and
  temporal context.
- Legacy records may be incomplete for historical reconstruction.
- Ontology evolution may require compatibility mappings and migrations.
- Source-of-truth precedence across repositories, CI, Runtime, and memory needs
  an explicit policy *(a Phase 0 deliverable — see the Reconciliation Record §6)*.
- Event volume, retention cost, delayed delivery, and clock skew are unknown
  *(retention policy is likewise a Phase 0 deliverable)*.
- Multi-scope identity and authorization semantics need implementation evidence.
- Physical consolidation of engines may erode logical independence.
- Notifications may create alert fatigue or be mistaken for acknowledged
  authority.
- Continuous coordination may cost more than the value of the work it schedules.
- A vendor-specific implementation may accidentally harden into policy.

These are active design risks, not implied defects in a selected implementation.

### 11.3 Reopening conditions

Reopen this specification when any of the following occurs:

- constitutional amendment or authorized interpretation changes an applicable
  authority boundary;
- a Foundational Concept is superseded or a candidate is promoted;
- two engines require conflicting write or decision authority;
- a material engineering question cannot be expressed by the ontology;
- relationship capture costs exceed demonstrated retrieval and assurance value;
- graph integrity rules block legitimate historical or epistemic representation;
- query explanations are insufficient for independent review;
- gravity becomes opaque scoring or Genome membership becomes irreversible;
- implementation cannot preserve engine separation, historical continuity,
  idempotency, or safe degradation;
- Runtime state is ambiguous, unrecoverable, or enables unsafe autonomy;
- a simpler architecture demonstrates equal traceability and safety at lower
  coordination cost;
- this specification conflicts with the reviewed implementation blueprint or
  repeated implementation evidence.

Revision must preserve the prior version, evidence that triggered reopening,
the authorized decision, compatibility impact, and migration or supersession
path.

## 12. Harvested integration material (candidate status preserved)

Unique material from the superseded integration skeleton, recorded here so
supersession is not silent. Nothing in this section is adopted by virtue of
appearing here.

- **Engine contract schema (proposed):** each engine contract states
  Mission, Inputs, Outputs, Dependencies, Authority, Constraints, Evidence,
  and Learning; cross-engine APIs remain logical contracts until a governed
  technology decision is made. *(§5's engines currently use
  Purpose/Inputs/Outputs/Authority-limits; unifying on the richer schema is
  part of the engine-contract-examples Phase 0 deliverable.)*
- **Knowledge Gravity review protocol (proposed, depends on P-1):** gravity
  changes require evidence-backed reasons, explicit relationships, review
  triggers, and governed promotion when higher architectural layers are
  affected.
- **Engineering Genome lifecycle (proposed, depends on P-2):** membership
  requires demonstrated use, explicit adoption, versioning, evidence, and
  reversal conditions.
- **Candidate register schema (subsumed):** status, supporting and
  contradictory evidence, authority, dependencies, review trigger, and
  supersession history — now realized by
  [`ACR-0001`](../governance/knowledge/ACR-0001-architectural-candidate-register.md),
  the single candidate register (Reconciliation Record §2).
- **Implementation roadmap sentence (superseded):** "implementation proceeds
  in separately authorized, reversible slices" — now fully elaborated by the
  [Implementation Blueprint](IMPLEMENTATION-BLUEPRINT.md) Phases 0–6.
- **Glossary rule (adopted practice):** the glossary references canonical
  definitions rather than duplicating them; conflicts or missing terms are
  recorded for ontology review instead of silently resolved.

## 13. Acceptance tests for this architecture

The architecture is context-complete only if a reviewer can answer:

- Who authorized a Material Action, under what Boundary, and until when?
- Which engine planned, executed, verified, assured, governed, and accepted it?
- Which constitutional and Foundational Concepts constrain an implementation?
- Which evidence supports a claim and what remains unknown or contradictory?
- What failure, success, or experiment produced a lesson?
- Why did knowledge gain or lose gravity?
- Which Genome version contained a member and how can it be reversed?
- What is affected when a principle, contract, or entity is superseded?
- Which candidates remain unpromoted and what evidence would qualify them?
- Can the complete decision be reconstructed from durable links without
  conversational memory?

If any answer requires hidden context, inferred authority, or an opaque model
result, the relevant architecture record is incomplete.
