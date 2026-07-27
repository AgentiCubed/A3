# Agentic³ Source Precedence and Retention Policy Record

- **Status:** Phase 0 record (IMPLEMENTATION-BLUEPRINT §10 Phase 0 "record
  … source precedence, retention policy"); makes explicit the precedence
  policy RT-SPEC §17 lists as an open risk ("must be explicit per RT-107")
- **Date:** 2026-07-27
- **Sources:** [`IMPLEMENTATION-BLUEPRINT.md`](./IMPLEMENTATION-BLUEPRINT.md)
  §5.2, §7.2, §8.1 ("BP"); the
  [Runtime Domain Specification v1.0](../governance/runtime/Runtime-Domain-Specification-v1.0.md)
  RT-107 and §10 ("RT-SPEC")
- **Authority:** This record states policy for *recording and reconciling*
  state. It authorizes no purge, no deletion, and no implementation. The one
  decision it defers is explicitly reserved: **approving a purge-enabling
  retention policy is a Principal ratification act** (see §3.4).

---

## 1. Source precedence (RT-107)

### 1.1 Precedence order

When authoritative sources disagree, the Synchronizer ranks them:

1. **Ratified governance records in the repository** — the Constitution,
   DR-/RR- records, and adopted specifications at their pinned commits and
   digests. Nothing outranks a ratified record within its scope and validity.
2. **The repository at large** (files at commits) — the human-reviewable
   canonical representation for all governance and knowledge documents
   (§2 below).
3. **The hosted forge's API state** (GitHub: PR/issue/branch/protection
   state) — authoritative for forge-native facts that have no file
   representation, such as whether a PR is merged.
4. **CI and build systems** — authoritative for run outcomes; a CI claim
   about repository content defers to the repository itself.
5. **Agentic³ database projections** (`runtime_events`, work items, ledger
   state) — authoritative for Runtime's *own* history (what was observed,
   decided, dispatched, recorded), never for the state of an external
   source.
6. **Conversational or session memory** — never repository truth (RT-SPEC
   §1 out-of-scope list). It may only propose captures that become durable
   records through the Memory Engine.

A rank applies **within the source's own domain of fact**. Precedence
resolves *which source is believed about a given fact class*; it never
licenses rewriting the lower-ranked source.

### 1.2 Conflict handling

- A detected divergence produces an appended **reconciliation record** (the
  sources agreed after re-read, or the lower-ranked projection was
  corrected by appending, never editing) or a **contradiction record**
  (they genuinely disagree).
- Contradictions between ranks 1–4 are never auto-resolved: they are
  recorded, quarantine or `BLOCKED` state is applied to dependent work, and
  a human resolution is requested through RT-110 (BP §12: "Approved
  precedence policy; contradiction record; human resolution").
- Silent overwrite is prohibited in both directions. Corrections preserve
  prior state and link it (`corrects` / `supersedes`).
- Every synchronization record names the precedence rank it applied, the
  before/after references, and digests.

## 2. Repository-canonical rule (BP §7.2)

The repository remains the human-reviewable **canonical representation**
for governance and knowledge documents. Database records *index and link*
those artifacts — by path, commit, digest, and canonical ID — and do not
silently rewrite files. A database row about a governance document is a
pointer plus verification metadata, not a second authority; if row and file
diverge, the file at the recorded commit wins and the row is corrected by
an appended revision.

This is why ratification records (RR-0002) pin SHA-256 digests: any
consumer — including the Phase 2 dispatcher's read-only policy adapter —
verifies bytes against the ratified digest rather than trusting a
projection.

## 3. Retention (BP §5.2)

### 3.1 Class-specific rules

Retention is class-specific, not uniform:

| Record class | Mutability | Retention rule |
|---|---|---|
| Evidence, events, decisions, relationships, transitions, revisions, gravity events | **Reject update/delete at both application and database layers** | Retained indefinitely pending an approved retention policy |
| Audit/evidence **metadata and digests** | Append-only | Outlive their payload bodies; never purged with them |
| Payload **bodies** (ArtifactStore blobs behind `payload_reference`) | Immutable content, disposable container | The only class eligible for future archival/expiry — and only under an approved policy, with digests retained |
| Operational projections (queues, current-state views) | Rebuildable | May be dropped and rebuilt from append-only history at any time |
| Quarantined raw events | Append-only | Retained until human resolution; secret material is never persisted in the first place (reference only) |

### 3.2 Append-only enforcement

The no-update/no-delete rule for durable history is enforced twice: in the
service layer (repositories expose no update/delete for these classes) and
at the database (constraints/triggers/permissions where practical), per
BP §5.2. Correction, contradiction, revocation, and supersession add linked
records (BP §1 invariant 6).

### 3.3 No purge job before an approved policy

**No purge, archival-with-deletion, or expiry job may exist before a
retention policy is approved** (BP §5.2). Until then the only sanctioned
volume controls are the non-destructive ones: payload separation (digest in
the ledger, body in ArtifactStore) and rebuildable projections. The risk
register's cost mitigation ("class retention, digest-only archival, payload
separation") is available **only after** such a policy exists; "no evidence
purge without policy" binds regardless.

### 3.4 Reserved decision

Approving a retention policy that enables any purge is a **Principal
ratification act** (a versioned, digest-pinned governance decision under
`docs/governance/decisions/`, registered like DR-0003), because purging is
an enumerated irreversible action (destructive cleanup) and evidence
deletion touches the constitutional append-only guarantee. No such policy
exists today; accordingly, no purge job is authorized.

## 4. Reopening conditions

Reopen this record when: measured event volume or storage cost exceeds the
budget a phase defines; a new source class (rank) is integrated; a
contradiction class recurs that §1.2 handles poorly; or a ratified
retention policy lands (which then governs and this record is amended by
appended revision to cite it).
