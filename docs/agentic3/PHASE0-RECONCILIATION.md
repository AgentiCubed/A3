# Agentic³ Phase 0 — Reconciliation Record

- **Status:** Proposed — Executor-drafted working record; rulings marked
  *(mechanical)* are correction proposals, rulings marked *(Principal)* are
  reserved decisions awaiting the Principal
- **Date:** 2026-07-26
- **Scope:** the Phase 0 "merge or explicitly reconcile v2, ontology, memory,
  and Runtime sources" deliverable (`IMPLEMENTATION-BLUEPRINT.md` §10);
  produced by a full-text comparison of `docs/agentic3/ARCHITECTURE-v2.md`
  ("**A**"), `docs/governance/architecture/Unified-Agentic3-Architecture-
  Specification-v2.md` ("**B**"), `docs/governance/ontology/ONTO-0001..0006`,
  `docs/agentic3/concepts/AC-0001..0002`, `docs/governance/runtime/Runtime-
  Domain-Specification-v1.0.md` ("**RT-SPEC**"), and
  `docs/agentic3/IMPLEMENTATION-BLUEPRINT.md` ("**BP**")
- **Phase 0 acceptance this record serves:** "No conflicting engine
  definition; all candidate/adopted statuses are explicit; every contract has
  an owner and version; TARP review complete; links and glossary are
  context-complete."

Nothing in this record adopts, promotes, or ratifies anything. Authority is
conferred through governance relationships, not document existence — this
document included.

---

## 1. The two v2 architecture specifications are a fork

**Finding.** A and B share **zero prose**. B (103 lines) is the older
integration skeleton (PR #23); A (566 lines) is the deep draft that PR #25
was supposed to unify with B twenty-six minutes later — but the merge kept
A's body, harvested only B's §17–§19, and left B orphaned and unmodified
since. Consequences:

- **Section-number collision.** The same section numbers denote different
  topics in each file (A §7 = candidate lifecycle; B §7 = engine contract
  schema). Every downstream citation ("ARCHITECTURE-v2 §7" in AC-0001,
  AC-0002, TARP-0001) resolves correctly only against A. `README.md`
  meanwhile links **only B** as "canonical".
- **A's numbering is broken** by the harvest: §11 jumps to §17 (no §12–§16),
  and A §11 (risks) duplicates the harvested §17/§18 with different content.
- **Direct contradiction:** A leaves the Verification/Assurance boundary
  undefined pending #17; B §10 defines it ("Verification evaluates evidence;
  Assurance evaluates readiness and unresolved risk").
- **A is stale on the Runtime Domain:** A still marks §4.2/§5.5/§6
  `[BLOCKED: #17]`, but the Runtime Domain Specification v1.0 exists and is
  headed "Adopted architecture baseline". B correctly links it.
- **Unique content in each:** A alone has the input register, authority
  hierarchy, six-engine roster (incl. Evolution), candidate lifecycle +
  open decision GD-P1, safety section, platform-separation rule. B alone has
  the Intelligence domain, engine-contract field schema, Gravity review
  protocol, Genome lifecycle, candidate-register schema, glossary section,
  and the Runtime-cannot-self-promote rules.

**Ruling (mechanical, proposed):** **A is the canonical consolidation
target** — every substantive citation in the repository already points at
it, and it is the declared target of issue #19. B is demoted to a harvested
source: its unique sections (§11–§16 material, Intelligence domain, engine
contract schema, runtime-authority rules) are to be merged into A under A's
numbering, after which B is superseded with a pointer header, and README's
link is corrected to A. A's stale `[BLOCKED: #17]` markers are replaced with
references to the adopted RT-SPEC. A's §11 and harvested §17/§18 risk lists
are merged.

**Reserved (Principal):** whether B's §10 Verification/Assurance boundary
sentence is *adopted* as the boundary (A treats this as open risk R3). It is
consistent with RT-SPEC §6 and BP §3; recommendation: adopt B's sentence.

## 2. Candidate/adopted statuses are not explicit — they are contradictory

**Finding (highest severity in the corpus).** AC-0001 (Knowledge Gravity)
and AC-0002 (Engineering Genome) are recorded as **Adopted Foundational
Concepts** by the ontology README, ONTO-0004, ONTO-0006 §3, and ACR-0001 —
while the AC-0001/AC-0002 documents themselves declare **"Proposed —
awaiting Principal review and an explicit adoption decision"** and contain
an explicit statement that *no adoption record exists in the repository*.
Everything below the Foundational-Concept layer currently hangs from this
contradiction. Worse, **two of AC-0001's reopening conditions are already
met and unactioned**:

1. AC-0001 reopening #1 — "Issue #16 lands a metadata model inconsistent
   with the four-source rule": ONTO-0004's `GravityEvent` defines **seven**
   event types against AC-0001's bounded **four**.
2. AC-0001 Rule 2 ("Gravity is not authority") — the ontology README and
   ONTO-0004 repeatedly describe gravity as "authority".

Related conflicts: ONTO-0004 answers open questions AC-0001/AC-0002
explicitly reserved for the adoption decision (five-tier gravity ladder;
8-kind genome element list vs AC-0002's 3-kind definition); two competing
genome-entry procedures exist (AC-0002 Rule 4 via ARCHITECTURE-v2 §7,
gated on undecided GD-P1, vs ONTO-0004 §2.4's own lifecycle); and TARP-0001
exists under three names and three statuses (Proposed protocol in
`docs/agentic3/`, "Traceable Architecture Review Process" per ONTO-0006,
and **Active** STD-0002 in the playbook).

**Reserved (Principal) — this is the core Phase 0 decision queue:**

| # | Decision | Recommendation |
|---|---|---|
| P-1 | Adopt, modify, or reject **AC-0001** — and in the same decision resolve the two met reopening conditions (four-source rule vs ONTO-0004's seven event types; "gravity is not authority" wording) | Adopt with ONTO-0004's representation *amended* to conform (7→4 sources by folding review/demotion/promotion into the four; strike "authority" wording) |
| P-2 | Adopt, modify, or reject **AC-0002** — resolving genome element granularity (3 kinds vs 8) and the genome-entry procedure (GD-P1) | Adopt with ONTO-0004 §2.2's 8 kinds as the *representation* and A §7 as the *procedure* (decides GD-P1: yes, the lifecycle governs) |
| P-3 | Decide **GD-P1**: does the A §7 candidate lifecycle govern layer-2 Foundational Concepts? | Yes — one lifecycle for all candidate layers |
| P-4 | Name the single canonical review instrument: TARP-0001 (proposed) vs STD-0002 (active) | STD-0002 remains the *active standard*; TARP-0001 is adopted as the *protocol* it implements; ONTO references corrected to cite both by their real names |
| P-5 | Adopt B §10's Verification/Assurance boundary sentence (closes A risk R3) | Adopt |
| P-6 | AC-0003..AC-0006 have register rows but **no concept documents** | Keep status Proposed/Validating; commission the four missing concept docs before any promotion review (no status change now) |

**Ruling (mechanical, proposed):** whatever P-1/P-2 decide, the *register*
is single-sourced: **ACR-0001 is the only candidate register**; ONTO-0006
§3's duplicate table is replaced by a pointer; ONTO-0006's stale "once the
PR establishing it is merged" text is corrected (ACR-0001 exists); AC-0003
is added to ACR-0001 (it is currently in ONTO-0006's table but absent from
the register entirely).

## 3. Status vocabularies: seven, unreconciled

**Finding.** Seven overlapping status/lifecycle vocabularies exist
(`governance_status`, ONTO-0003 lifecycle, candidate lifecycle, genome
maturity, genome membership status, gravity levels, ACR-0001 lifecycle),
reusing tokens (`validated`, `adopted`, `proposed`, `foundational`,
`retired`) with different meanings and no mapping. ONTO-0001's
`governance_status` contains `adopted` — a state with no defined transition
anywhere. `REQUEST_MORE_EVIDENCE` / `NEEDS_EVIDENCE` /
`request_more_evidence` are three spellings across three documents. Two
non-identical outcome enumerations exist for the same gravity review
(ONTO-0004 §1.8 vs ONTO-0005 Q-011).

**Ruling (mechanical, proposed):** one mapping table is added to ONTO-0003
(the lifecycle owner) declaring, for each vocabulary: its scope, its owner
document, and its token-level mapping to the ONTO-0003 lifecycle. The
duplicated review-outcome enumerations are unified in ONTO-0004 with
ONTO-0005 referencing it. `adopted` is either given transitions or removed
from `governance_status` (recommendation: remove; adoption is a candidate-
lifecycle concept, not an instance state).

## 4. RT-SPEC vs Implementation Blueprint: eighteen divergences

**Finding.** The two Runtime sources agree on the deep structure (same
component roster RT-101..RT-110, same engine API surface, same event
families and classification enum) but diverge on eighteen points. The ones
that materially affect Phase 1 code:

| # | Topic | RT-SPEC | BP | Ruling (proposed) |
|---|---|---|---|---|
| R-1 | Governance placement | authorization from "Governance **Domain**" | Governance is an engine **inside Executive Domain** | *(mechanical)* BP wording adopted — its own text guarantees the authority boundary is placement-invariant |
| R-2 | Tenancy | absent from all models; open risk | mandatory field in every contract, quarantine trigger, query bound | *(mechanical)* BP adopted — Phase 1 acceptance requires a test tenant; RT-SPEC risk noted as resolved by BP |
| R-3 | `actor_id` null rule | null only for passive observation/schedule tick; else **quarantine** | null "when source cannot supply"; no consequence | *(mechanical)* RT-SPEC adopted — stricter test *and* stricter consequence; BP's wording is the defect |
| R-4 | Where events become canonical | ambiguous (RT-101 vs RT-102) | RT-101 emits raw, RT-102 produces `RuntimeEventV1` | *(mechanical)* BP adopted — resolves RT-SPEC's internal ambiguity |
| R-5 | Checkpoint mutability | "immutable **or append-only**" | immutable only | *(mechanical)* BP adopted (narrower); checkpoint contract to be named `RuntimeCheckpointV1` for parity |
| R-6 | Lease/decision revocation | expiry only | revocation state + immediate-revocation acceptance | *(mechanical)* BP adopted; revocation fields added to the `GovernanceDecisionV1` example too (gap in both docs) |
| R-7 | Executor-forbidden transitions | not "directly" to `VERIFIED_PASS`/`READY_FOR_PROMOTION` | adds `PROMOTED`, drops "directly" | *(mechanical)* union adopted: all three states, no "directly" qualifier (fail closed) |
| R-8 | Non-authorizers of irreversible promotion | schedule, timeout, silence, inferred intent | timeout, schedule, urgency, silence, model confidence | *(mechanical)* union adopted: all six |
| R-9 | Quarantine triggers | 9 incl. missing-required-actor | 9 incl. tenant mismatch, missing missing-actor | *(mechanical)* union adopted: 10 triggers |
| R-10 | Work-item temporal rules | four explicit rules | compressed away | *(mechanical)* RT-SPEC's four rules restored into the contract notes |
| R-11 | Transition laws 4–6 | present | absent | *(mechanical)* RT-SPEC laws restored |
| R-12 | Irreversible retry | "fresh authorization" | "fresh **human** authorization" | *(mechanical)* BP adopted (stricter) |
| R-13 | Degraded mode | stop promotion + irreversible | also stop **dispatch** | *(mechanical)* BP adopted (stricter) |
| R-14 | Priority tuple | 9 dims incl. "constitutional" | 9 dims incl. "security"; approved queue-policy version | *(mechanical)* union: 10 dims; queue-policy-version requirement adopted |
| R-15 | AC-0003 used normatively | "each component follows AC-0003" | "does not silently promote" | *(mechanical)* RT-SPEC §2 reworded to "is structured in the manner AC-0003 proposes (candidate, not adopted)" |
| R-16 | Contract owners/versions | none | none (V1 names only) | *(mechanical)* every contract gets `owner: Runtime workstream (Executor: delegated agents; accountable: Principal)` + semver, recorded with the contract examples deliverable |
| R-17 | `assurance_id` / `work_id`+`version` fields | present | dropped | *(mechanical)* restored — identity fields are load-bearing |
| R-18 | Issue-number metadata | #17 | #21/#19; ledger says #23/#24/#25 | *(mechanical)* header metadata corrected to name both design issue and landing PR |

Union rulings are proposed wherever both documents state safety rules and
neither is a superset — fail closed by taking both.

## 5. Dangling references and undefined terms (context-completeness)

**Findings** *(all mechanical unless noted)*:

- **Missing documents cited as existing:** AC-0003, AC-0004, AC-0005,
  AC-0006 concept docs; any ARC-NNNN principle; any CON-NNNN contract; any
  PAT-/AP- record (ONTO-0004 §2.2 names four genome examples with no records
  behind them); GD-P1 as a recorded decision. Resolution: register each as
  an explicit gap in ACR-0001 / the risk register — citations must say
  "(not yet landed)" until they land.
- **`KnowledgeEngine`** used as a relationship source type but never defined
  → replace with `Engine` + `engine_role` qualifier or define the type.
- **"Engineering Genome (AC-0002 entity)" vs `EngineeringGenome`** — one
  name chosen (`EngineeringGenome`).
- **Undefined load-bearing terms:** "independent" (the ≥3-independent-
  workstreams promotion gate), "architectural workstream", "Material Action"
  criterion, "Halt" (defined only in A §2.5, uncited by ONTO docs),
  `PromotionThreshold`/`DemotionTrigger` schemas. Resolution: definitions
  added to the glossary section during the A/B merge; "independence" is
  **reserved (Principal, P-7)** since it gates promotions —
  recommendation: *different initiating issue, different primary Executor
  session, and no shared draft lineage*.
- **Namespace table gaps:** `ACR-`, `RR-`, `GD-`, `TARP-`, `ONTO-` exist in
  the repo; ONTO-0003 §4.1 admits only `ONTO-` of these → table extended.
- **Duplicate/near-duplicate entity types** (`Observation` vs
  `ObservationRecord`, `VerificationRecord` vs `VerificationResult`,
  `Decision`×3, `RuntimeEvent`/`Event`/`LogRecord`): disambiguation notes
  added; unused types (`VerificationResult`, knowledge-`Decision`) marked
  *candidate-for-removal* pending ontology review.
- **Four mutually inconsistent statements** of which entity types require
  `knowledge_gravity` (ONTO-0001 §2.3 prose vs §2.3 rows vs §3 table vs
  ONTO-0004 §1.2) → single authoritative list adopted in ONTO-0001 §3,
  others reference it.
- **A/B/ontology cross-blindness:** the ONTO family never cites
  ARCHITECTURE-v2 (either copy); B never cites the ontology files.
  Resolution: the merged A gains explicit links; ONTO README gains the
  reverse link.

## 6. What this record does *not* do

- It does not change any status. §2's decision queue (P-1..P-7) is the
  Principal's; the register stays as ACR-0001 records it until then.
- It does not touch code. Phase 1 starts only after this record and DR-0003
  are accepted and the mechanical corrections above have landed.
- It does not complete Phase 0 by itself. Remaining Phase 0 deliverables
  after this record: the corrected/merged ARCHITECTURE-v2 (per §1), the
  ONTO/AC correction PRs (per §2–§5), worked contract examples with owners
  and versions (per R-16), the authority matrix (extracted from BP §3 +
  RT-SPEC §2 — drafted alongside DR-0003), source-precedence and retention
  policy records, implementation ADRs, and the STD-0002 review of the lot.

## 7. Companion artifact

`docs/governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md`
(Proposed) — the Principal-ratified reversible-work standing policy Phase 0
requires and Phase 2's dispatcher will verify by stable ID, version,
digest, scope, and expiry. Drafted from the reconciled action
classification in §4 (R-8, R-9, R-12) and RT-SPEC's irreversible-action
enumeration.
