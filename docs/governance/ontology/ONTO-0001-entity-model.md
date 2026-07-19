# ONTO-0001 — Entity Model

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Root Entity

Every addressable object in the Agentic³ system is an `Entity`. All entity families defined below
inherit these fields. Fields marked *Conditional* are required only for the entity types noted.

| Field | Type | Required | Immutable | Description |
|---|---|---|---|---|
| `entity_id` | StableIdentifier | Yes | Yes | Globally unique within Agentic³; format determined by namespace (e.g. `AC-0001`, `FR-0001`). Never reused. |
| `canonical_name` | String | Yes | No | Human-readable name. Changes are versioned and preserved in `version_history`. |
| `aliases` | []String | Yes | No (append-only) | Preserved prior and alternate names. |
| `namespace` | String | Yes | Yes | Project, repository, organization, or institutional identity scope. |
| `entity_type` | EntityType | Yes | Yes within a version | One of the defined types in this model. Reclassification requires a governed new version. |
| `lifecycle_state` | LifecycleState | Yes | No | Current lifecycle state. Transitions governed by ONTO-0003. |
| `provenance` | ProvenanceRecord | Yes | Yes | Origin: creator, authority, source, and creation context. Immutable. |
| `current_version_id` | VersionIdentifier | Conditional | No | References the current version record for versioned types (documents, specifications, governance records, software artifacts). |
| `version_history` | []VersionRef | Conditional | No (append-only) | Ordered list of prior versions. Append-only; entries never removed. |
| `verification_status` | VerificationStatus | Yes | No | Whether the entity's claims have been verified, by whom, and under which criteria. |
| `governance_status` | GovernanceStatus | Yes | No | Current governance standing: `draft`, `active`, `adopted`, `superseded`, `retired`. |
| `relationships` | []Relationship | Yes | No (append-only) | All explicit relationships to other entities. See ONTO-0002. |
| `created_at` | Timestamp | Yes | Yes | Creation timestamp. Immutable. |
| `created_by` | ActorReference | Yes | Yes | Actor that created the entity. |
| `updated_at` | Timestamp | Yes | No | Last-modification timestamp. |
| `authority_refs` | []GovernanceRelationship | Conditional | No (append-only) | Required when authority is claimed; identifies delegation, ratification, or decision conferring standing. |
| `superseded_by` | EntityReference | Conditional | No | If superseded, references the superseding entity. Prior content preserved. |
| `knowledge_gravity` | KnowledgeGravityMetadata | Conditional | No | Required for knowledge entities. See ONTO-0004. |
| `genome_membership` | GenomeMembershipRecord | Conditional | No | Required for entities explicitly in the Engineering Genome. See ONTO-0004. |

### Root entity constraints

- Every entity must have a stable identifier before it can be referenced by another entity.
- An entity's `authority_refs` must trace to a Principal through a chain of governance
  relationships. Authority is not inferred from document existence.
- `created_at` and `provenance` are immutable after creation. Corrections to provenance are
  added as versioned annotations, not overwrites.
- `superseded_by` never erases the prior entity. Both the prior and new entity coexist and
  remain navigable.
- Reclassification, including candidate promotion, requires a governance decision and a new
  immutable version. The stable `entity_id` is retained, and the prior type remains visible in
  `version_history`.

---

## 2. Entity Families

### 2.1 Actor Entities

Actor entities represent participants who take actions within the system. All actors receive
their authority through explicit governance relationships.

| Type | Description | Additional required fields |
|---|---|---|
| `Principal` | An entity holding ultimate authority and accountability in a defined scope. | `scope_boundary`, `delegations_granted[]` |
| `Executor` | An entity performing work under Delegation from a Principal. | `delegating_authority` (ref to Delegation), `boundary` |
| `Evaluator` | An entity determining whether work satisfies acceptance conditions. | `evaluation_scope`, `independence_basis` |
| `Agent` | An autonomous executor with a defined capability profile, tool permissions, and provider. | `capabilities[]`, `tool_permissions[]`, `provider`, `max_autonomy_boundary` |
| `AIAgent` | An Agent identity implemented by an AI system. | `agent_ref`, `model_or_provider_ref` |
| `Human` | A natural-person identity; roles are conferred separately. | `role_refs[]` |
| `HumanContributor` | A human participant with defined system and project roles. | `system_role`, `project_roles[]`, `org_membership` |
| `Organization` | A collective actor that owns scopes and may designate Principals. | `scope`, `principal_refs[]` |
| `ServiceIdentity` | A non-human identity used by a system or integration. | `service_ref`, `credential_reference` |

**Actor constraints:**
- An Actor's authority is conferred through explicit governance relationships, not inferred from
  role labels.
- An Actor serving as Executor on a Material Action shall not serve as the sole Evaluator of
  that action (Constitution Art. V).
- An Actor may not expand its own authority, alter its Boundary, or create Delegations for
  itself (Constitution Art. VII §2).
- `Agent` actors record a `max_autonomy_boundary`; actions beyond it require an explicit
  Delegation extension.

### 2.2 System Entities

System entities represent technical components acting as execution environments, infrastructure,
or integration points. They do not hold governance authority.

| Type | Description | Additional required fields |
|---|---|---|
| `ServiceComponent` | A discrete deployable unit (API, worker, database, cache). | `interface_contract`, `dependencies[]`, `health_indicator` |
| `Domain` | A bounded functional area with declared responsibilities. | `scope`, `owned_entity_types[]` |
| `Engine` | A system responsible for a defined reasoning or operational capability. | `responsibilities[]`, `forbidden_authority[]` |
| `RuntimeComponent` | A component that observes, schedules, dispatches, or monitors runtime work. | `runtime_role`, `inputs[]`, `outputs[]` |
| `Tool` | A bounded capability callable by an Actor or Engine. | `capabilities[]`, `permission_requirements[]` |
| `Workflow` | A versioned orchestration definition. | `steps[]`, `gate_refs[]`, `authority_ref` |
| `WorkflowEngine` | An execution environment managing task dispatch, retries, and state. | `engine_type`, `capabilities[]`, `port_interface` |
| `ProviderAdapter` | A provider-neutral interface to an external AI or tooling provider. | `provider_name`, `capability_mapping`, `credential_reference` |
| `ArtifactStore` | A content-addressed storage backend for execution artifacts. | `addressing_scheme`, `persistence_policy` |
| `Repository` | A version-controlled source code or documentation store. | `vcs_type`, `org_scope`, `default_branch` |

**System constraints:**
- System entities do not hold governance authority independently.
- Interactions with system entities are governed by the authority of the Principal or Actor
  whose Delegation covers that interaction.
- System entities record `dependencies[]` explicitly; implicit dependencies are a graph
  integrity violation (see ONTO-0003).

### 2.3 Knowledge Entities

Knowledge entities represent recorded understanding: facts, interpretations, decisions, patterns,
and their confidence levels. Facts, interpretations, authority decisions, and confidence levels
are always distinct fields and shall never be conflated.

| Type | Identifier | Description | Additional required fields |
|---|---|---|---|
| `FailureRecord` | `FR-NNNN` | An observed failure preserved as fact, not interpretation. | `failure_facts[]`, `recovery_actions[]` |
| `Observation` | (stable namespace ID) | A directly observed fact without interpretation. | `observation_ref`, `scope`, `observed_at` |
| `Claim` | (stable namespace ID) | A proposition whose support, contradiction, and confidence are explicit. | `statement`, `confidence`, `evidence_refs[]` |
| `Finding` | (stable namespace ID) | A reviewed conclusion drawn from stated evidence. | `claim_refs[]`, `evidence_refs[]`, `review_status` |
| `Decision` | (stable namespace ID) | A selected course or interpretation, distinct from its evidence and authority. | `decision`, `rationale`, `authority_refs[]` |
| `Lesson` | (stable namespace ID) | A reusable interpretation derived from experience. | `source_refs[]`, `applicability`, `confidence` |
| `Heuristic` | (stable namespace ID) | A bounded decision aid whose exceptions remain explicit. | `trigger`, `recommended_action`, `exceptions[]` |
| `Rumination` | `RM-NNNN` | Structured interpretation of a failure with competing hypotheses. | `linked_failure_record`, `hypotheses[]`, `counter_evidence[]` |
| `IdeaEvolutionRecord` | `IER-NNNN` | Chronological record of how a concept changed across stages. | `stage_sequence[]`, `evidence_at_each_stage[]` |
| `ReasoningLedger` | `RL-NNNN` | Evidence, counter-evidence, confidence history, and review triggers for a claim. | `evidence[]`, `counter_evidence[]`, `confidence_history[]` |
| `TETCapsule` | `TET-NNNN` | The minimal reusable capsule of a belief change. | `prior_model`, `disturbing_evidence`, `revised_model`, `tested_consequence` |
| `Pattern` | `PAT-NNNN` | A repeated successful practice with sufficient evidence to recommend reuse. | `application_evidence[]`, `known_exceptions[]`, `knowledge_gravity` |
| `AntiPattern` | `AP-NNNN` | A repeated harmful practice that should be recognized and avoided. | `recurrence_evidence[]`, `recognition_signals[]`, `knowledge_gravity` |
| `Risk` | `RSK-NNNN` | A material downside with owner, trigger conditions, mitigation, and review interval. | `owner`, `triggers[]`, `mitigation`, `residual_exposure`, `review_interval` |
| `Assumption` | `ASM-NNNN` | An unverified premise on which active work depends. | `testability_conditions`, `invalidation_triggers[]` |
| `Experiment` | `EXP-NNNN` | An intentional test designed to reduce uncertainty or compare options. | `hypothesis`, `design`, `measured_outcomes[]` |
| `UnexpectedSuccessRecord` | `USR-NNNN` | An outcome materially better than expected, preserving the mechanism. | `expected_outcome`, `actual_outcome`, `mechanism_hypothesis` |
| `FoundationalConcept` | `AC-NNNN` | A project-wide concept with the highest non-constitutional governance weight. | `scope`, `adoption_evidence[]`, `upward_compatibility_impact`, `knowledge_gravity`, `genome_membership` |
| `ArchitecturalCandidate` | `AC-NNNN` | A concept under evaluation for potential adoption as a Foundational Concept. | `lifecycle_state`, `promotion_criteria[]`, `evidence_to_date[]` |
| `ArchitecturalPrinciple` | `ARC-NNNN` | A derived principle governing design decisions; derived from the Ontology layer. | `governing_concept` (ref to FoundationalConcept), `scope`, `exceptions[]`, `knowledge_gravity` |
| `ArchitecturalContract` | `CON-NNNN` | A binding invariant between architectural layers or components. | `parties[]`, `invariants[]`, `violation_consequences` |
| `EngineeringGenome` | (singleton, versioned) | The explicit set of current genome memberships. | `version`, `membership_refs[]`, `revision_history[]` |

**Knowledge entity constraints:**
- Facts, interpretations, authority decisions, and confidence levels are always separate fields.
  A single undifferentiated prose block is a model violation.
- A knowledge entity's authority is conferred by a governance relationship, not by file
  existence.
- `FoundationalConcept` and `ArchitecturalPrinciple` require `knowledge_gravity` metadata. See
  ONTO-0004.
- `Pattern` and `AntiPattern` require at least two independent application or recurrence events
  before they may be created. A single incident may produce a `Risk` or `Assumption` but not a
  `Pattern`.
- `TETCapsule` is the minimal unit. When the surrounding record already makes the epistemic
  transition self-evident, a separate `TETCapsule` is not required.

### 2.4 Artifact Entities

Artifact entities represent produced outputs. Artifacts produced under a Delegation are owned by
the responsible Principal unless ownership is explicitly transferred.

| Type | Description | Additional required fields |
|---|---|---|
| `CodeArtifact` | A source code file, module, or package. | `language`, `module_path`, `test_coverage_ref` |
| `DocumentArtifact` | A documentation or specification file. | `document_type`, `governing_section` |
| `MigrationArtifact` | A database migration script. | `migration_number`, `schema_changes_summary`, `reversible` |
| `TestArtifact` | A test file or test suite. | `test_type`, `target_component`, `latest_result_ref` |
| `DataArtifact` | A data file, seed file, or export. | `format`, `content_hash`, `freshness_policy` |
| `AnalysisArtifact` | Output from an analysis worker (report, chart, computation result). | `worker_type`, `inputs[]`, `content_hash` |
| `ConfigurationArtifact` | A configuration or infrastructure-as-code file. | `config_type`, `environment_scope` |
| `Issue` | A durable issue-tracker record. | `repository_ref`, `issue_number`, `state` |
| `PullRequest` | A proposed repository change and its review history. | `repository_ref`, `number`, `head_ref`, `base_ref` |
| `Commit` | An immutable version-control commit. | `repository_ref`, `sha`, `parent_shas[]` |
| `Branch` | A named version-control reference. | `repository_ref`, `ref_name`, `head_sha` |
| `Tag` | An immutable named reference to a commit. | `repository_ref`, `tag_name`, `target_sha` |
| `Release` | A published, versioned set of artifacts. | `tag_ref`, `artifact_refs[]`, `published_at` |
| `SourceFile` | A source-controlled file at a specific version. | `repository_ref`, `path`, `commit_ref` |
| `ArchitectureDecisionRecord` | A technical architecture decision with alternatives and consequences. | `context`, `decision`, `alternatives[]`, `consequences` |
| `DesignLedger` | A chronological record of design reasoning and changes. | `entries[]`, `decision_refs[]` |
| `Report` | A durable report produced by work or analysis. | `report_type`, `source_refs[]` |
| `TestReport` | An aggregate report over one or more test results. | `test_result_refs[]`, `summary` |
| `Checkpoint` | A durable capture of system or work state. | `scope`, `captured_at`, `state_refs[]` |

**Artifact constraints:**
- Content-addressed artifacts (SHA-identified) are immutable once stored.
- Artifact provenance must trace to the execution that produced it.
- Ownership transfer requires an explicit governance action; implied transfer is not permitted.

### 2.5 Evidence Entities

Evidence entities represent inspectable information that supports or contradicts claims about
work or Material Actions. Evidence entities are append-only.

| Type | Description | Additional required fields |
|---|---|---|
| `CIRunResult` | The outcome of a CI workflow run. | `run_id`, `workflow_name`, `result_status`, `log_reference` |
| `TestResult` | The outcome of a test run. | `test_suite`, `pass_count`, `fail_count`, `artifact_refs[]` |
| `LintResult` | The outcome of a lint or format check. | `tool`, `target`, `findings[]` |
| `ObservationRecord` | A recorded observation: measurement, log excerpt, output, or screenshot. | `observation_type`, `source`, `content_reference` |
| `ExperimentResult` | The measured outcome of a defined Experiment entity. | `linked_experiment`, `measured_outcome`, `conditions` |
| `ReviewRecord` | The outcome of a formal review (code, governance, architecture). | `reviewer`, `reviewed_artifact_ref`, `outcome`, `conditions[]` |
| `VerificationRecord` | The structured record that a Material Action was verified. | `material_action_ref`, `verifier`, `criteria[]`, `evidence_refs[]` |
| `VerificationResult` | The result of applying verification criteria to a claim, artifact, or state. | `target_ref`, `criteria[]`, `result`, `evidence_refs[]` |
| `AssuranceResult` | A determination of whether evidence is sufficient for a proposed action. | `proposed_action_ref`, `result`, `uncertainties[]` |
| `Metric` | A measured value with unit, scope, and collection context. | `name`, `value`, `unit`, `measured_at` |
| `LogRecord` | An immutable runtime or system log observation. | `source`, `occurred_at`, `content_reference` |
| `AuditEvent` | An immutable record of a system state change. | `action_type`, `actor_ref`, `before_state`, `after_state` |

**Evidence constraints:**
- Evidence entities are append-only. Once created, they shall not be modified or deleted.
- No claim of Verification shall exist without a `VerificationRecord` referencing sufficient
  evidence (Constitution Art. VI §1, §5).
- An Executor shall not be the sole source of evidence establishing the success of its own
  Material Action (Constitution Art. VI §3).
- `ReviewRecord` reviewer must not be the same entity as the work's primary Executor.

### 2.6 Governance Entities

Governance entities represent authority instruments, decisions, delegations, and the records
through which work is authorized. Governance entities are append-only: amendments and
supersessions add new content and preserve prior content; they do not overwrite.

| Type | Identifier | Description | Additional required fields |
|---|---|---|---|
| `Constitution` | (singleton) | The supreme governing instrument. | `version`, `articles[]`, `amendment_history[]` |
| `ConstitutionalArticle` | (stable article citation) | An addressable article within a Constitution version. | `constitution_version_ref`, `article_number`, `text_ref` |
| `ConstitutionalAmendment` | `A-NNNN` | A ratified change to the Constitution. | `amended_articles[]`, `ratification_record`, `prior_text` |
| `GovernanceDecision` | `DR-NNNN` | An authority decision ratified within the governance namespace. | `decision_body`, `authority_basis`, `ratification_evidence` |
| `Delegation` | (inline or separate) | A grant of authority from a Principal to an Executor or Evaluator within a Boundary. | `granting_principal`, `receiving_entity`, `boundary`, `expiry` |
| `AuthorityGrant` | (stable namespace ID) | A bounded grant of authority. | `issuer`, `recipient`, `scope`, `expiry_or_revocation` |
| `Permission` | (stable namespace ID) | Permission for a named action within a scope. | `action`, `scope`, `grantee`, `expiry` |
| `Policy` | `POL-NNNN` | A governance rule issued under explicit authority. | `scope`, `requirements[]`, `authority_ref` |
| `Standard` | `STD-NNNN` | A mandatory quality or interoperability specification. | `scope`, `criteria[]`, `authority_ref` |
| `Procedure` | `PROC-NNNN` | An authorized sequence for carrying out governed work. | `steps[]`, `gate_refs[]`, `authority_ref` |
| `Gate` | (stable namespace ID) | A required decision point before a transition or action. | `criteria[]`, `decision_authority`, `outcomes[]` |
| `Approval` | (stable namespace ID) | A recorded authorized approval or rejection. | `target_ref`, `decision`, `decided_by`, `authority_ref` |
| `Boundary` | (inline or separate) | An explicit limit on delegated authority. | `scope`, `duration`, `resources`, `permitted_outcomes[]` |
| `TaskPacket` | (per task) | Authorization document for a specific task. | `objective`, `scope`, `acceptance_conditions[]`, `stop_conditions[]`, `deliverables[]` |
| `ReviewPacket` | (per review) | Authorization document for a specific review. | `review_objective`, `artifacts_under_review[]`, `governing_criteria[]`, `non_goals[]` |
| `PlaybookDocument` | `POL-NNNN`, `PROC-NNNN`, `STD-NNNN`, `TPL-NNNN` | A policy, procedure, standard, or template in the governance namespace. | `document_type`, `governing_scope`, `supersedes` |

**Governance entity constraints:**
- Authority is conferred through explicit Delegation or ratification, not through document
  existence.
- `GovernanceDecision` and `ArchitectureDecisionRecord` are append-only; corrections annotate
  rather than overwrite.
- A Delegation shall not expand itself or create authority beyond what the granting Principal
  possesses (Constitution Art. III §2).
- No governance entity may alter the Constitution except through the amendment process
  (Constitution Art. XII).
- `TaskPacket` and `ReviewPacket` must establish acceptance conditions before execution begins
  (Constitution Art. VI §4).

### 2.7 Work Entities

Work entities represent bounded intent, plans, work, and executions. Assignment identifies an
executor but does not confer approval authority.

| Type | Description | Additional required fields |
|---|---|---|
| `Objective` | A desired outcome with explicit success conditions. | `acceptance_criteria[]`, `authority_ref` |
| `Project` | A governed scope coordinating objectives, plans, and work. | `organization_ref`, `objective_refs[]`, `authority_ref` |
| `Plan` | An ordered proposal for satisfying one or more objectives. | `objective_refs[]`, `work_items[]`, `risk_refs[]` |
| `Milestone` | A reviewable intermediate outcome in a plan. | `plan_ref`, `acceptance_criteria[]` |
| `Task` | A bounded unit of planned work. | `plan_ref`, `scope`, `acceptance_criteria[]` |
| `WorkItem` | A schedulable or assignable unit of work. | `task_ref`, `assigned_actor_ref`, `authorization_ref` |
| `MaterialAction` | An action whose impact requires explicit authorization and verification. | `scope`, `authorization_ref`, `verification_criteria[]` |
| `AcceptanceCriterion` | A testable condition defining acceptable work. | `statement`, `verification_method`, `authority_ref` |
| `RuntimeEvent` | An observed runtime occurrence relevant to work state. | `source`, `occurred_at`, `observed_by` |
| `Execution` | One attempt to perform an authorized work item. | `work_item_ref`, `executor_ref`, `delegation_ref`, `attempt` |

**Work entity constraints:**
- Plans and assignments do not authorize themselves; authorization must resolve through
  `authority_refs`.
- Each execution is a distinct historical attempt and must preserve its produced artifacts and
  evidence.
- Objectives, plans, and work items must remain traceable to their originating intent and
  acceptance criteria.

### 2.8 Temporal Entities

Temporal entities represent events, sequences, and histories where ordering and timing are
material to interpretation. They are immutable records of what happened.

| Type | Description | Additional required fields |
|---|---|---|
| `Event` | A timestamped occurrence that changes system or governance state. | `event_type`, `actor_ref`, `affected_entity_refs[]` |
| `ExecutionSequence` | The ordered set of states through which a task passes. | `task_id`, `state_transitions[]`, `durations[]` |
| `LifecycleTransition` | A single state change for an entity, with cause and timestamp. | `entity_ref`, `from_state`, `to_state`, `triggered_by` |
| `LifecycleState` | A named state in an entity lifecycle vocabulary. | `state_name`, `applies_to[]` |
| `Transition` | A permitted movement between lifecycle states. | `from_state`, `to_state`, `constraints[]` |
| `Version` | An immutable revision of a durable entity. | `version_id`, `entity_id`, `parent_version_ids[]`, `effective_date` |
| `ValidityInterval` | The bounded interval in which an entity or relationship applies. | `valid_from`, `valid_to` |
| `ReviewTrigger` | A temporal or evidentiary condition requiring review. | `condition`, `reviewer_ref`, `due_at` |
| `ReuseEvent` | A timestamped independent application of knowledge. | `knowledge_ref`, `context_ref`, `outcome`, `evidence_refs[]` |
| `Timeline` | A projection of scheduled events, milestones, or deadlines. | `project_id`, `milestones[]`, `critical_path_nodes[]` |
| `VersionHistory` | The ordered sequence of versions for a versioned entity. | `entity_ref`, `versions[]`, `supersession_events[]` |

**Temporal entity constraints:**
- Temporal entities are immutable records of what occurred. They may be annotated but not
  retroactively modified.
- `LifecycleTransition` records both the prior and new state; the prior state shall never be
  discarded.
- `VersionHistory` preserves all prior versions, including superseded ones.
- An `ExecutionSequence` covers a single task execution attempt; distinct attempts produce
  distinct sequences.

---

## 3. Entity Family Summary

| Family | Authority source | Append-only | Knowledge Gravity required | Genome Membership required |
|---|---|---|---|---|
| Actor | Governance relationship | No — changes create new delegation | No | No |
| System | Deployed configuration | No — changes audited via AuditEvent | No | No |
| Knowledge | Authority decision | Supersessions add, never overwrite | Pattern, AntiPattern, FoundationalConcept, ArchitecturalPrinciple, ArchitecturalContract | Pattern, AntiPattern, FoundationalConcept (if in genome) |
| Artifact | Execution provenance | Content-addressed artifacts immutable | No | No |
| Evidence | System or human observation | Yes | No | No |
| Governance | Ratification or delegation | Yes (amendments preserve prior text) | No | No |
| Work | Governance authorization | Executions and runtime events are append-only | No | No |
| Temporal | Events and state changes | Yes | No | No |

---

## 4. Type Completeness Requirement

The entity types in this model cover the Agentic³ engines as of Issue #16. As additional
engines are specified (Memory, Verification, Assurance, Evolution), entity types must be
evaluated for fit. If an entity cannot be cleanly mapped to an existing family, the Ontology
must be extended through an authorized revision rather than forcing a misfit.

This is an open risk. See ONTO-0006 §4.
