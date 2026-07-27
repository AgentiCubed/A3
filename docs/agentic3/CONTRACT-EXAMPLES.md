# Agentic³ Contract Examples — Owners, Versions, and Worked Instances

- **Status:** Phase 0 record (IMPLEMENTATION-BLUEPRINT §10 Phase 0 "record
  contract examples"; satisfies reconciliation ruling R-16 and the Phase 0
  acceptance line "every contract has an owner and version")
- **Date:** 2026-07-27
- **Sources:** [`IMPLEMENTATION-BLUEPRINT.md`](./IMPLEMENTATION-BLUEPRINT.md)
  §4 ("BP") and the
  [Runtime Domain Specification v1.0](../governance/runtime/Runtime-Domain-Specification-v1.0.md)
  §3–§6 ("RT-SPEC"), as reconciled by
  [`PHASE0-RECONCILIATION.md`](./PHASE0-RECONCILIATION.md) §4 rulings
  R-1…R-18, decided under
  [DR-0004](../governance/decisions/DR-0004-Phase-0-Reconciliation-Decisions.md)
- **Authority:** This document records contract shapes and worked instances.
  It authorizes no implementation, dispatch, or irreversible action. Field
  values below are synthetic; digests and UUIDs are illustrative placeholders,
  not real artifacts.

---

## 1. Rules common to every contract

1. **Owner and version (R-16).** Every contract in §2 carries the owner
   `Agentic³ Runtime workstream (Executor: delegated agents; accountable:
   Principal)` and semantic version `1.0.0`. Evolution is additive within a
   major version; a breaking change creates a new version plus an explicit
   translator (BP §4.1).
2. **Tenant scope (R-2).** `tenant_id` is a required field of every contract.
   Tenant mismatch anywhere in a chain is a quarantine trigger, and every
   query is tenant-bounded.
3. **Actor rule (R-3, RT-SPEC wording adopted).** `actor_id` may be null only
   for a passive observation or schedule tick with no attributable actor.
   An event missing an actor its schema requires is **quarantined**, never
   normalized with a null actor.
4. **Secrets by reference.** No contract instance ever carries secret
   material. Payload bytes live in `ArtifactStore` behind
   `payload_reference` + `payload_digest`; secret detection quarantines the
   event without persisting the value.
5. **At-least-once delivery.** `(source_system, idempotency_key,
   schema_version)` is unique; consumers store an `IngestReceiptV1` in the
   same transaction as their effect; ordering is guaranteed only per subject
   via a monotonic `subject_sequence`.
6. **Append-only history (BP §1 invariant 6).** Correction, contradiction,
   revocation, and supersession add linked records; nothing here is ever
   updated in place or erased.
7. **A command is never evidence.** Commands express requests; only events
   record what occurred (BP §4.1).

## 2. Contract register

| Contract | Version | Owner | Persistence owner (BP §5.1) | Controlling rulings |
|---|---|---|---|---|
| `RuntimeEventV1` | 1.0.0 | Agentic³ Runtime workstream (Executor: delegated agents; accountable: Principal) | `runtime_events` | R-2, R-3, R-4 |
| `IngestReceiptV1` | 1.0.0 | same | `runtime_ingest_receipts` | R-2 |
| `QuarantineRecordV1` | 1.0.0 | same | `runtime_events` (quarantined partition) | R-3, R-9 |
| `WorkItemV1` | 1.0.0 | same | `runtime_work_items` + `runtime_work_item_transitions` | R-7, R-10, R-14, R-17 |
| `ExecutionLeaseV1` | 1.0.0 | same | `execution_leases` | R-6, R-12 |
| `GovernanceDecisionV1` | 1.0.0 | same | `governance_authorizations` | R-6, R-8 |
| `VerificationRecordV1` | 1.0.0 | same | `verification_records` | — |
| `AssuranceDecisionV1` | 1.0.0 | same | `assurance_decisions` | R-17 |
| `IntentV1` | 1.0.0 | same | `agentic3_entities` | R-2 |
| `PlanV1` | 1.0.0 | same | `agentic3_entities` + `agentic3_relationships` | R-2 |
| `RuntimeCheckpointV1` | 1.0.0 | same | `runtime_checkpoints` | R-5 |

Contract models live in `backend/app/agentic3/contracts/` when Phase 1+
implementation is authorized; until then this register is the canonical
statement of ownership and versioning.

---

## 3. Worked examples

### 3.1 `RuntimeEventV1`

An approved synthetic source event — a CI workflow-run completion observed
from GitHub Actions. This is the Phase 1 acceptance fixture class.

```json
{
  "contract": "RuntimeEventV1",
  "schema_version": "1.0.0",
  "event_id": "EVT-0001",
  "event_type": "observed.ci.workflow_run_completed",
  "tenant_id": "TEN-0001",
  "source_system": "github_actions",
  "source_entity_id": "workflow_run/16412345678",
  "source_uri": "https://github.com/AgentiCubed/agenticubed/actions/runs/16412345678",
  "source_timestamp": "2026-07-27T06:17:42Z",
  "received_timestamp": "2026-07-27T06:17:44Z",
  "actor_id": "system:github_actions",
  "subject_entity_id": "repository/AgentiCubed/agenticubed",
  "project_id": null,
  "repository_id": "AgentiCubed/agenticubed",
  "subject_sequence": 4187,
  "correlation_id": "corr-7b1e2f7c-3a9d-4c1e-9f42-0d8a51c2e6b4",
  "causation_id": null,
  "payload_digest": "sha256:4be1a2c907d1a51f0e6c3b8d92f47a05c1d9e8b26f3a70415c2d8e9f0a1b3c5d",
  "payload_reference": "artifact://TEN-0001/runtime-events/EVT-0001/payload.json",
  "classification": "fact",
  "sensitivity": "internal",
  "trust_level": "authenticated_source",
  "idempotency_key": "github_actions:workflow_run:16412345678:completed",
  "ontology_relationships": [
    {"type": "OBSERVES", "target": "repository/AgentiCubed/agenticubed"}
  ],
  "provenance": [
    {"step": "observed", "component": "RT-101", "adapter_version": "1.0.0",
     "at": "2026-07-27T06:17:44Z"},
    {"step": "normalized", "component": "RT-102", "schema_version": "1.0.0",
     "at": "2026-07-27T06:17:44Z"}
  ]
}
```

**Notes.**

- RT-101 emits the *raw* observation; only RT-102 produces this canonical
  `RuntimeEventV1` (R-4). Both steps appear in `provenance`.
- `actor_id` here is an attributable system actor. It could be null only if
  this were a passive observation or schedule tick with no attributable
  actor; any other event class missing its required actor is quarantined,
  not defaulted (R-3).
- `classification` is one of `fact | report | proposal | decision |
  authorization | verification | alert`; the `event_type` prefix comes from
  the thirteen event families (`observed.*` … `quarantined.*`).
- Events are immutable. A correction is a new event linked by `corrects` or
  `supersedes`.

### 3.2 `IngestReceiptV1`

Stored in the **same transaction** as the consumer's effect, making
duplicate delivery harmless.

```json
{
  "contract": "IngestReceiptV1",
  "schema_version": "1.0.0",
  "receipt_id": "RCT-0001",
  "tenant_id": "TEN-0001",
  "event_id": "EVT-0001",
  "dedup_key": {
    "source_system": "github_actions",
    "idempotency_key": "github_actions:workflow_run:16412345678:completed",
    "schema_version": "1.0.0"
  },
  "consumer": "runtime.normalizer",
  "outcome": "stored",
  "effect_digest": "sha256:0c2f5e8a1b4d7c9036e5f8a2b4d61c3e9f0a2b5c8d1e4f7a0b3c6d9e2f5a8b1c",
  "recorded_at": "2026-07-27T06:17:44Z"
}
```

**Notes.** `outcome` is `stored | duplicate_ignored`. A second delivery of
`EVT-0001` finds the `dedup_key` and records `duplicate_ignored` with **no
second effect** — the Phase 1 "ingested twice, one stored effect" acceptance
test asserts exactly this pair.

### 3.3 `QuarantineRecordV1`

```json
{
  "contract": "QuarantineRecordV1",
  "schema_version": "1.0.0",
  "quarantine_id": "QRN-0001",
  "tenant_id": "TEN-0001",
  "trigger": "missing_required_actor",
  "raw_event_reference": "artifact://TEN-0001/quarantine/QRN-0001/raw.json",
  "raw_event_digest": "sha256:7d4a1c8e2f5b9036d1e4a7c0b3f6e9d2c5a8b1f4e7d0c3a6b9e2d5f8a1c4b7e0",
  "source_system": "github_actions",
  "received_timestamp": "2026-07-27T06:22:10Z",
  "reason": "Event class reported.* requires an attributable actor; source supplied none.",
  "resolution_state": "open",
  "resolution_requires": "human_review",
  "recorded_at": "2026-07-27T06:22:10Z"
}
```

**Notes.** `trigger` is the **union enumeration of ten** (R-9, fail closed):
`identity_unverifiable`, `schema_invalid`, `tenant_mismatch`,
`repository_mismatch`, `secret_material_detected`, `contradictory_authority`,
`unknown_destructive_action`, `missing_provenance`,
`replay_outside_validity_window`, `missing_required_actor`. Quarantine
preserves the raw bytes by reference (never inline when
`secret_material_detected`) and invents no facts.

### 3.4 `WorkItemV1`

A reversible observation work item inside the sole ratified standing work
class **WC-OBS-1**
([DR-0003 v1.0.0](../governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md)).

```json
{
  "contract": "WorkItemV1",
  "schema_version": "1.0.0",
  "work_id": "WRK-0001",
  "version": 3,
  "tenant_id": "TEN-0001",
  "objective": "Record the outcome of CI workflow run 16412345678 in the runtime ledger and propose a memory capture if it contradicts the last recorded state.",
  "origin_event_id": "EVT-0001",
  "repository_scope": "AgentiCubed/agenticubed",
  "work_class": "WC-OBS-1",
  "allowed_actions": ["read_source", "append_runtime_record", "propose_memory_capture"],
  "prohibited_actions": ["merge", "push", "tag", "release", "delete", "protection_change", "secret_rotation"],
  "allowed_resources": ["runtime_events", "runtime_ingest_receipts", "memory_capture_proposals"],
  "expected_outputs": ["appended ledger record", "optional capture proposal"],
  "acceptance_criteria": ["ledger record present with provenance", "no source mutation"],
  "verification_plan": "VRF-PLAN-0001 (fixed before execution)",
  "authority_required": "standing_policy:WC-OBS-1",
  "current_authorization_artifact": "GOV-0001",
  "risk_class": "reversible_observation",
  "priority": {
    "queue_policy_version": "QP-1.0.0",
    "constitutional_urgency": 0,
    "governance_urgency": 0,
    "safety_security_impact": 0,
    "release_blocking": 0,
    "dependency_criticality": 1,
    "deadline_cost": 0,
    "reversibility": "fully_reversible",
    "evidence_freshness": 2,
    "learning_value": 1,
    "operator_priority": 0
  },
  "dependencies": [],
  "deadline": "2026-07-28T06:17:44Z",
  "review_trigger": "on_referenced_event_or_schedule_tick",
  "eligible_executor_capabilities": ["runtime.recorder"],
  "retry_policy": {"max_attempts": 3, "max_elapsed": "PT1H", "backoff": "exponential"},
  "stop_conditions": ["lease_expired", "authorization_revoked", "quarantine_raised"],
  "state": "QUEUED",
  "state_history": ["OBSERVED", "NORMALIZED", "CLASSIFIED", "PROPOSED", "AUTHORIZED", "QUEUED"],
  "evidence_refs": ["EVT-0001"],
  "learning_refs": []
}
```

**Notes.**

- `work_id` + `version` are load-bearing identity fields (R-17); the worker
  compare-and-swaps on `version`.
- The four **temporal rules** (R-10): a `deadline` is a completion bound
  independent of any authorization validity window; reaching it invokes
  policy and produces a recorded escalation or `EXPIRED` transition; expiry
  never silently cancels and never grants authority; `review_trigger` is
  evaluated on each referenced event and schedule tick.
- The priority tuple is the **ten-dimension union** (R-14) plus the approved
  `queue_policy_version` — Runtime does not invent weights; constitutional
  and governance urgency and safety/security are hard precedence; ties break
  by age then stable `work_id`.
- A Work Item is a proposal, **never** authorization. An executor cannot
  transition it to `VERIFIED_PASS`, `READY_FOR_PROMOTION`, or `PROMOTED`
  (R-7 — all three states, no "directly" qualifier).

### 3.5 `ExecutionLeaseV1`

```json
{
  "contract": "ExecutionLeaseV1",
  "schema_version": "1.0.0",
  "lease_id": "LSE-0001",
  "tenant_id": "TEN-0001",
  "work_id": "WRK-0001",
  "work_version": 3,
  "executor_id": "agent:runtime-recorder-01",
  "task_packet_digest": "sha256:e1f4a7b0c3d6e9f2a5b8c1d4e7f0a3b6c9d2e5f8a1b4c7d0e3f6a9b2c5d8e1f4",
  "authorization_reference": "GOV-0001",
  "allowed_actions": ["read_source", "append_runtime_record", "propose_memory_capture"],
  "allowed_resources": ["runtime_events", "runtime_ingest_receipts", "memory_capture_proposals"],
  "issued_at": "2026-07-27T06:18:00Z",
  "expires_at": "2026-07-27T06:33:00Z",
  "heartbeat_interval": "PT30S",
  "attempt": 1,
  "revocation_state": "active",
  "revoked_at": null,
  "revoked_by": null,
  "revocation_reason": null
}
```

**Notes.** Expiry **or revocation** removes authority to continue, and
revocation takes effect immediately (R-6). Scope cannot self-expand; a
repository or identity mismatch causes STOP. Heartbeat loss yields *unknown*
until timeout — never a fabricated failure or success. A retry of an
**irreversible** action requires fresh **human** authorization (R-12);
retries within WC-OBS-1 are reversible and follow the bounded
`retry_policy`.

### 3.6 `GovernanceDecisionV1`

The registration-shaped decision the Phase 2 dispatcher will verify through
its read-only policy adapter: authorization by the ratified standing policy.

```json
{
  "contract": "GovernanceDecisionV1",
  "schema_version": "1.0.0",
  "decision_id": "GOV-0001",
  "tenant_id": "TEN-0001",
  "work_id": "WRK-0001",
  "action_class": "WC-OBS-1",
  "authority_source": {
    "kind": "standing_policy",
    "stable_id": "DR-0003",
    "version": "1.0.0",
    "digest": "sha256:33d2055028897f149ee52a1cdfe50c5c2c1a870e86ccf066cc751b7c81fc1e35",
    "scope": "WC-OBS-1 only",
    "expiry": "2027-01-22"
  },
  "outcome": "allow",
  "exact_scope": "Append-only observation and recording against tenant TEN-0001, repository AgentiCubed/agenticubed",
  "expiry": "2026-07-28T06:17:44Z",
  "preconditions": ["registered policy digest matches ratified record", "policy unexpired and unrevoked"],
  "prohibited_actions": ["merge", "push", "tag", "release", "delete", "protection_change", "secret_rotation"],
  "required_evidence": ["origin event EVT-0001", "ingest receipt"],
  "revocation_state": "active",
  "revoked_at": null,
  "revoked_by": null,
  "provenance": {"recorded_by": "governance.engine", "basis": "RR-0002 ratification record", "signed_at": "2026-07-27T06:17:50Z"}
}
```

**Notes.** `outcome` is `allow | deny | halt | escalate`. Revocation fields
are present on the decision itself (R-6 — a gap in both source documents,
closed here). Schedule, timeout, silence, inferred intent, urgency, and
model confidence — the **six-way union** of non-authorizers (R-8) — can
never produce this artifact for an irreversible action; those require a
current, exact human authorization. Runtime can neither mint nor broaden
this decision.

### 3.7 `VerificationRecordV1`

```json
{
  "contract": "VerificationRecordV1",
  "schema_version": "1.0.0",
  "verification_id": "VRF-0001",
  "tenant_id": "TEN-0001",
  "target": {"work_id": "WRK-0001", "work_version": 3},
  "criteria_version": "VRF-PLAN-0001@1.0.0",
  "criteria_fixed_at": "2026-07-27T06:17:50Z",
  "verifier_id": "agent:verifier-02",
  "verifier_independence": "verifier is not the executor of WRK-0001 and shares no session lineage with it",
  "outcome": "pass",
  "criterion_results": [
    {"criterion": "ledger record present with provenance", "result": "pass",
     "evidence_refs": ["EVT-0001", "RCT-0001"]},
    {"criterion": "no source mutation", "result": "pass",
     "evidence_refs": ["sync-snapshot sha256:b2c5d8e1f4a7b0c3d6e9f2a5b8c1d4e7f0a3b6c9d2e5f8a1b4c7d0e3f6a9b2c5"]}
  ],
  "environment": "ci-hermetic",
  "tool_versions": {"pytest": "8.x", "adapter": "1.0.0"},
  "recorded_at": "2026-07-27T06:25:00Z"
}
```

**Notes.** `outcome` is the tri-state `pass | fail | unknown`; `unknown` is
a valid gate outcome, never coerced. The criteria version **predates** the
result, and the verifier is independent of the executor (BP §1 invariant 4:
an executor cannot be the sole evaluator of its own material action).

### 3.8 `AssuranceDecisionV1`

```json
{
  "contract": "AssuranceDecisionV1",
  "schema_version": "1.0.0",
  "assurance_id": "ASR-0001",
  "tenant_id": "TEN-0001",
  "target_action": {"work_id": "WRK-0001", "work_version": 3},
  "outcome": "ready",
  "evaluated_evidence": ["VRF-0001", "EVT-0001", "RCT-0001"],
  "unresolved_risks": [],
  "confidence_statement": "All verification criteria pass on inspectable evidence; no unresolved risk in scope.",
  "validity_window": {"from": "2026-07-27T06:26:00Z", "until": "2026-07-28T06:26:00Z"},
  "reopening_conditions": ["any referenced evidence superseded", "new contradiction recorded against EVT-0001"],
  "recorded_at": "2026-07-27T06:26:00Z"
}
```

**Notes.** `assurance_id` is restored as a required identity field (R-17).
`outcome` is `ready | not_ready | more_evidence_required`. **`ready` is not
an authorization** — the adopted boundary (DR-0004 P-5) is: *Verification
evaluates evidence; Assurance evaluates readiness and unresolved risk;
Governance supplies authority.*

### 3.9 `IntentV1`

```json
{
  "contract": "IntentV1",
  "schema_version": "1.0.0",
  "intent_id": "INT-0001",
  "tenant_id": "TEN-0001",
  "actor_id": "human:principal",
  "objective": "Maintain a queryable, append-only ledger of CI outcomes for AgentiCubed/agenticubed.",
  "constraints": ["observation and recording only (WC-OBS-1)", "no source mutation", "no new UI"],
  "acceptance_criteria": ["double-ingest yields one effect", "provenance query answers actor, source, and chain", "quarantine on ambiguity"],
  "non_goals": ["scheduling", "external side effects", "Cockpit changes"],
  "provenance": {"recorded_from": "issue #21 Phase 1 scope", "recorded_by": "executive.intent", "at": "2026-07-27T06:00:00Z"},
  "version": 1
}
```

**Notes.** Intent preserves the Principal's input verbatim; the Intent
engine cannot authorize work or redefine that intent. `IntentV1` implies no
authorization.

### 3.10 `PlanV1`

```json
{
  "contract": "PlanV1",
  "schema_version": "1.0.0",
  "plan_id": "PLN-0001",
  "tenant_id": "TEN-0001",
  "source_intent": {"intent_id": "INT-0001", "version": 1},
  "milestones": [{"id": "M1", "title": "Event ledger vertical slice"}],
  "tasks": [
    {"id": "T1", "milestone": "M1", "title": "Ingest and normalize the approved synthetic source", "depends_on": []},
    {"id": "T2", "milestone": "M1", "title": "Prove double-ingest idempotency", "depends_on": ["T1"]}
  ],
  "dependencies": [{"from": "T2", "to": "T1"}],
  "risks": ["duplicate delivery outside dedup window", "schema drift at source"],
  "acceptance_criteria_preserved_from": {"intent_id": "INT-0001", "version": 1},
  "assumptions": ["single test tenant TEN-0001"],
  "provenance": {"proposed_by": "executive.planning", "at": "2026-07-27T06:05:00Z"},
  "version": 1
}
```

**Notes.** Planning decomposes approved intent into a DAG without redefining
success and cannot approve its own plan; acceptance criteria are preserved
by reference, not restated.

### 3.11 `RuntimeCheckpointV1`

```json
{
  "contract": "RuntimeCheckpointV1",
  "schema_version": "1.0.0",
  "checkpoint_id": "CHK-0001",
  "tenant_id": "TEN-0001",
  "boundary": "phase_gate",
  "captured_at": "2026-07-27T06:30:00Z",
  "verified_facts": ["EVT-0001 stored with receipt RCT-0001", "VRF-0001 outcome pass"],
  "inferences": ["source cadence appears nightly; unconfirmed"],
  "decisions": ["GOV-0001 (standing policy WC-OBS-1)"],
  "unknowns": ["retention cost at production volume"],
  "pending_authority": [],
  "active_work": [{"work_id": "WRK-0001", "version": 3, "state": "VERIFYING"}],
  "source_references": [
    {"path": "docs/governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md",
     "digest": "sha256:33d2055028897f149ee52a1cdfe50c5c2c1a870e86ccf066cc751b7c81fc1e35"}
  ],
  "repository_identifiers": ["AgentiCubed/agenticubed@main"],
  "recorded_by": "RT-108"
}
```

**Notes.** Checkpoints are **immutable, full stop** (R-5 — BP's narrower
rule adopted over RT-SPEC's "immutable or append-only"); a later state is a
*new* checkpoint. The record distinguishes verified facts, inference,
decisions, unknowns, and pending authority, and records supplied state
without certifying it.

---

## 4. Maintenance

This register is append-only in the ACR-0001 sense: a contract's status or
version changes by adding a dated entry and linking the governing decision,
never by silently editing a row. New contracts enter through the same
reconciliation discipline — a recorded ruling or decision, then a row and a
worked example here.
