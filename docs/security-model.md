# AgentiCubed — Security Model

## 1. Tenancy and isolation

Every persisted row is scoped to an `organization_id`. All queries are filtered
by the caller's organization at the repository layer; cross-org access is denied
before a query is issued. There is no "global admin" bypass in application code.

## 2. Authentication

- Password auth with `argon2` (preferred) hashing; never store plaintext.
- Short-lived JWT access tokens + rotating refresh tokens. Tokens carry
  `sub` (user id), `org` (organization id), and `sysrole`; project roles are
  resolved per-request from the DB (not trusted from the token).
- Service/worker calls use a separate internal credential, never a user token.

## 3. Authorization (RBAC)

Two role planes:

| Plane | Roles | Granted at |
|-------|-------|-----------|
| System | `owner`, `admin`, `member` | Organization |
| Project | `manager`, `contributor`, `approver`, `viewer` | Per project (ProjectMember) |

Permissions are checked by a central `authorize(actor, action, resource)` guard
in `app/core/rbac.py`. The API layer calls it; services assume an authorized
actor but still re-scope by org. Representative matrix:

| Action | owner/admin | manager | contributor | approver | viewer |
|--------|:-:|:-:|:-:|:-:|:-:|
| Create project | ✓ | ✓ | – | – | – |
| Edit plan / tasks | ✓ | ✓ | ✓ (assigned) | – | – |
| Assign agents | ✓ | ✓ | – | – | – |
| Grant agent-tool permission | ✓ | ✓ | – | – | – |
| Decide approval gate | ✓ | – | – | ✓ | – |
| View dashboards | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manage users/roles | ✓ | – | – | – | – |

## 4. Least-privilege tool permissions

- An agent may invoke a tool **only** if an `AgentToolPermission` row exists for
  that (agent, tool) pair. Absence = deny (default-deny).
- Permissions carry a `scope` (e.g. allowed domains, read-only flag) and an
  optional `expires_at`. The orchestration layer enforces scope at invocation.
- Tools have a `sensitivity`. `high`-sensitivity tool invocations require a human
  approval gate before execution, regardless of standing permission.

## 5. Agents cannot escalate themselves

Hard rule, enforced at three layers:
1. **RBAC** — the actor performing a permission grant must be a `user` with
   `admin`/`manager`; `actor_type=agent` is rejected for permission mutations.
2. **Service guard** — `grant_tool_permission` refuses when
   `actor_id == target_agent_id` or `actor_type == agent`.
3. **Audit** — every permission change writes an `AuditEvent`; an agent-initiated
   attempt is logged as a security event.

Agents also cannot modify their own `config`, `default_role`, RBAC roles, or
disable evaluators.

## 6. Executor / evaluator separation

The evaluator of a `TaskExecution` is never the executing agent. Enforced at
dispatch and re-validated when an `Evaluation` is written
(`evaluator_agent_id != execution.agent_id`). Prevents self-grading and reward
hacking. (ADR-0004.)

## 7. Secrets handling

Never place secrets in **prompts, logs, source code, or ordinary application
data fields**.

- Provider credentials and tool secrets live only in environment variables /
  a secrets manager, referenced by **key** from `Agent.config` / `Tool.schema`
  (e.g. `{"api_key_ref": "ANTHROPIC_API_KEY"}`), never by value.
- The orchestration layer resolves a credential reference to its value at the
  moment of an outbound call and discards it; the value is never written to
  `TaskExecution.input_context`, `output`, artifacts, or audit rows.
- A redaction filter runs on all structured logs and on `AuditEvent.before/after`
  to strip known secret patterns and any field named like a credential.
- `.env` is git-ignored; `.env.example` ships only placeholder keys.

## 8. Human approval gates

Required before any **irreversible or sensitive** action:
- invoking a `high`-sensitivity tool,
- external side effects flagged irreversible (sends, deletes, payments),
- closing a project / accepting deliverables when policy requires sign-off.

The action is blocked (`AWAITING_APPROVAL`) until an `approver`/`manager`
records an `Approval`. Rejection routes to revision or replan, never silent
proceed.

## 9. Immutability and audit

- `TaskExecution`, `Evaluation`, `EvaluationCriterion`, `AuditEvent` are
  append-only at the application layer; Phase 2 adds DB-level guards
  (revoke UPDATE/DELETE, append triggers).
- Every material state change (status transition, assignment, permission grant,
  approval decision, plan change) emits an `AuditEvent` with redacted
  before/after, the actor, and a timestamp.

## 10. Transport & input safety

- HTTPS terminated at the edge (compose dev uses HTTP on localhost only).
- All input validated by Pydantic schemas; SQLAlchemy parameterizes queries
  (no string-built SQL).
- Prompt-injection mitigation: tool permissions are default-deny and scoped, so a
  hijacked agent still cannot exceed its granted, audited capabilities; sensitive
  actions still hit approval gates.

## 11. Threats explicitly addressed

| Threat | Control |
|--------|---------|
| Self-grading agent | Executor/evaluator separation (§6) |
| Privilege escalation by agent | §5 three-layer block |
| Secret leakage via prompt/log | §7 reference-by-key + redaction |
| Cross-tenant data access | §1 org scoping at repository layer |
| Runaway irreversible action | §8 approval gates + sensitivity tiers |
| Tampered history | §9 append-only + audit |
| Circular dependency lockup | DAG cycle rejection (architecture §7) |
