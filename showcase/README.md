# AgentiCubed

**An agentic operating layer for work that spans systems you do not control.**

AgentiCubed (also written **Agentic³** or **A³**) is a platform-neutral operating
layer that sits *above* fragmented networks and services. Instead of one more
integration that logs into one more account, it treats identity, content,
monitoring, agent workflows, approvals, memory, and cross-platform intelligence
as first-class primitives — coordinated once, then projected onto whichever
services happen to exist that year: X, Threads, Bluesky, Mastodon, LinkedIn,
Reddit, YouTube, and whatever replaces them.

> **Status, before anything else.** AgentiCubed is building a governed
> social-operations layer. This public repository presents the architecture and
> reasoning behind its governed execution model; **it does not currently connect
> to social platforms.** The long-term thesis is an agentic social operating
> system spanning fragmented networks. The present capability is the governed
> orchestration substrate needed to plan, approve, execute, evaluate, remediate,
> and close agentic work safely — and that substrate lives in a private
> repository, not this one.

This repository is a **public architecture showcase**. It explains the problem,
the thesis, the architecture, and the governance model. It contains prose,
diagrams, and fabricated sample data — there is nothing here to run, and no
result on this page was produced by code in this repository.

---

## Contents

- [The problem](#the-problem)
- [Product thesis](#product-thesis)
- [What this repository is](#what-this-repository-is)
- [What this repository is not](#what-this-repository-is-not)
- [Architecture overview](#architecture-overview)
- [Example use cases](#example-use-cases)
- [Current status](#current-status)
- [Roadmap](#roadmap)
- [Security and privacy posture](#security-and-privacy-posture)
- [Documentation map](#documentation-map)
- [Connect at AI4](#connect-at-ai4)

---

## The problem

Every social and publishing network is a silo with its own identity model, its own
content shape, its own rate limits, its own moderation regime, and its own idea of
what "you" are. The practical consequences are boring and expensive:

1. **Identity is per-account, not per-person.** There is no durable subject that
   persists across platforms, so context, reputation, and history fragment.
2. **Automation is per-platform.** Every integration is rebuilt from scratch, and
   dies when the platform changes its terms, its API, or its mind.
3. **Agents have no substrate.** Dropping an LLM into a posting queue produces
   fluent, ungoverned output with no evaluation, no approval boundary, and no
   audit trail. That is a liability, not a product.
4. **Memory does not accumulate.** What was learned on one network in March is
   unavailable on another in June, because nothing owns the memory.
5. **Platform risk is total.** When a provider retires an API, everything built
   directly against it stops. (This is not hypothetical — see
   [`docs/provenance.md`](docs/provenance.md) for a documented instance that
   reshaped this project's adapter layer.)

The pattern underneath all five is the same: **the coordination layer is missing.**
Each platform assumes it is the top of the stack. None of them is.

---

## Product thesis

> Platforms are peripherals. The operating layer belongs above them.

AgentiCubed's bet is that the durable value is not in any one network integration
but in the layer that makes networks interchangeable:

| Primitive | What the operating layer owns |
|-----------|-------------------------------|
| **Identity** | A subject that persists across platforms; per-platform accounts are projections of it, not the source of truth. |
| **Policy** | What may be done, by whom, on which surface, under what conditions — declared once, enforced everywhere. |
| **Orchestration** | Objectives decomposed into a governed task graph, assigned to agents or humans by capability. |
| **Approvals** | Irreversible and sensitive actions are blocked pending a human decision. Default-deny, not default-send. |
| **Evaluation** | Output is graded against explicit acceptance criteria by an actor that did not produce it. |
| **Memory** | Durable, queryable context that outlives any single platform, campaign, or model. |
| **Audit** | An append-only record of what was decided, by whom, on what evidence. |
| **Adapters** | Platforms are pluggable at the edge. Adding one is configuration; losing one is survivable. |

The second bet is more specific and more contrarian:

> **Governance is the feature, not the friction.**

Anyone can wire a model to an API. What is hard — and what determines whether an
agentic system can be trusted with an account, a brand, or a budget — is the
substrate underneath: approval gates that actually block, evaluators that cannot
grade their own work, credentials that are never in a prompt, and a history that
cannot be quietly rewritten. AgentiCubed is built governance-first and grows
outward to surfaces, not the other way around.

---

## What this repository is

An **architecture showcase** — a public artifact describing how the system is
designed and why.

It contains:

- Architecture and boundary documentation with diagrams
- The security model expressed as boundaries and invariants
- A public roadmap with honest status labels
- Provenance notes: real decisions, including ones that were wrong first
- Sanitized, non-functional mock data illustrating the shapes involved
- Positioning material for conversations at AI4

### What you can and cannot do with this repository

Stated plainly, because "showcase" is a word people read optimistically:

| You can | You cannot |
|---------|------------|
| Read the architecture and judge whether the boundaries are sound | Run anything — there is no executable code here |
| Inspect the fabricated sample data and see the shapes involved | Reproduce any claimed behaviour from this repository |
| Evaluate the security model as a set of stated invariants | Verify those invariants yourself — the enforcing code is private |
| Argue with the reasoning, and tell me where it is wrong | Audit the implementation |

Every `Working` label in the [status table](#current-status) refers to the
**private** implementation and is backed by evidence held privately. Those labels
are claims made on my own authority, not results you can check here. Treating
them as independently verified would be a mistake, so I would rather say so than
let the word "showcase" do quiet work.

---

## What this repository is not

This is deliberately **not** a product dump. It does not contain, and will not
contain:

- Source code of the working implementation
- API keys, tokens, credentials, or secrets of any kind
- OAuth flows, session handling, or authentication implementation details
- Production prompts or agent routing logic
- Real platform adapters or working service integrations
- Deployment configuration, infrastructure definitions, or host details
- Customer, client, or user data — real, derived, or reconstructed
- Non-public business strategy or commercial terms
- Security architecture at a level of specificity that would assist an attacker
- Private repository history

Everything in `demo/` is **fabricated illustrative data**. It does not execute, it
does not correspond to any real run, and it references no real account, person, or
organization.

> **Disclaimer.** This is a public conceptual showcase of AgentiCubed. The core
> implementation is private and is not published here. Documentation describes
> design intent and architecture; it is not an operational specification, a
> security disclosure, or a commitment to ship any particular capability on any
> particular date.

---

## Architecture overview

Four layers. Dependencies point **inward** — the operating layer never imports a
platform SDK, and the domain never knows which vendor is on the other end of a
call.

```mermaid
flowchart TB
    subgraph S["Surfaces"]
        direction LR
        s1["Operator console"]
        s2["Approval queue"]
        s3["Analytics & audit views"]
    end

    subgraph OL["Operating layer — platform-neutral"]
        direction TB
        id["Identity & subject graph"]
        pol["Policy & permissions<br/><small>default-deny</small>"]
        orch["Orchestration<br/><small>governed task graph</small>"]
        appr["Approval gates"]
        evalr["Evaluation & remediation"]
        mem["Memory & retrieval"]
        aud["Append-only audit"]
    end

    subgraph PA["Adapter boundary — ports"]
        direction LR
        pa1["Platform adapters"]
        pa2["Model provider adapters"]
        pa3["Tool adapters"]
    end

    subgraph N["External services"]
        direction LR
        n1["Social & publishing networks"]
        n2["Model providers"]
        n3["Third-party tools"]
    end

    S --> OL --> PA --> N
```

### The governed loop

Every unit of work runs the same closed loop. Nothing reaches an external service
without passing through it.

```mermaid
flowchart LR
    Intake["Intake<br/><small>objective + constraints</small>"]
    Plan["Plan<br/><small>decompose to a DAG</small>"]
    Approve{"Human<br/>approval"}
    Assign["Assign<br/><small>capability matching</small>"]
    Execute["Execute<br/><small>via adapter</small>"]
    Evaluate["Evaluate<br/><small>independent grader</small>"]
    Gate{"Criteria<br/>met?"}
    Remediate["Remediate<br/><small>policy engine</small>"]
    Close(["Close + retrospective"])

    Intake --> Plan --> Approve
    Approve -->|rejected| Plan
    Approve -->|approved| Assign --> Execute --> Evaluate --> Gate
    Gate -->|yes| Close
    Gate -->|no| Remediate --> Execute
```

Four properties make the loop meaningful rather than decorative:

1. **The plan is a contract.** It is validated against a strict, versioned schema
   before a human is ever asked to approve it. A malformed plan fails loudly at
   the boundary instead of half-executing.
2. **The approver is a human.** Approval is a recorded decision by an identified
   person, not a confidence threshold.
3. **The evaluator is never the executor.** Self-grading is structurally
   prevented, not discouraged by prompt.
4. **Remediation is bounded.** The loop retries under an explicit policy with a
   budget; when it exhausts that budget it escalates to a person rather than
   spinning.

### Platforms are adapters, never architecture

```mermaid
flowchart LR
    subgraph Core["Domain — knows only ports"]
        svc["Orchestration services"]
    end

    port["PlatformAdapter port<br/><small>publish · read · observe</small>"]

    subgraph Edge["Interchangeable at the edge"]
        direction TB
        a1["Adapter: microblog"]
        a2["Adapter: federated"]
        a3["Adapter: professional"]
        a4["Adapter: video"]
        a5["Adapter: retired<br/><small>tombstone</small>"]
    end

    svc --> port --> a1 & a2 & a3 & a4 & a5
```

The tombstone is not decoration. When a provider is withdrawn, its adapter stays
registered as an explicit gravestone that fails with a typed, readable error and
migration guidance — rather than being deleted, which would make every record
still referencing it fail with an opaque crash. This pattern exists because a
provider really was retired mid-build; see
[`docs/provenance.md`](docs/provenance.md).

Full detail: [`docs/architecture.md`](docs/architecture.md).

---

## Example use cases

Illustrative, and deliberately unglamorous — these are the shapes the operating
layer is designed for.

**These are design contexts, not current capability.** Cases 1, 2, 4, and 5
involve social and publishing platforms, and no platform adapter exists today.
They describe what the substrate is being built to carry, and they are the reason
its boundaries sit where they do. Case 3 is the shape that runs now.

**1. Cross-platform publication with a human gate.**
An objective ("publish the launch note") decomposes into per-surface drafting
tasks with per-surface constraints. Each draft is evaluated against explicit
criteria. Publication is an irreversible external action, so it stops at an
approval gate. A person approves once; the layer fans out across surfaces and
records what went where.

**2. Signal monitoring with a durable subject.**
Mentions, replies, and references are observed across networks and resolved
against a persistent subject rather than a per-platform handle. The result is one
timeline of what was said about a person or topic, not seven disconnected inboxes.

**3. Governed research and synthesis.**
An analyst agent gathers, a writer agent drafts, an evaluator agent grades against
a rubric it did not write. Failing outputs are remediated under a bounded policy.
The artifact ships with its own evidence trail attached.

**4. Platform migration without rewrite.**
A network changes terms or shuts an API. The adapter is replaced or tombstoned.
Plans, memory, policies, approvals, and history are unaffected, because none of
them ever referenced the vendor.

**5. Delegated operation with a bounded blast radius.**
An agent is granted a narrow, expiring, scoped permission for a specific surface.
It cannot widen its own permissions, cannot disable its evaluator, and cannot take
a high-sensitivity action without a human decision — and every attempt is recorded
whether it succeeded or not.

---

## Current status

Honest labels. Nothing below is aspirational unless it says so.

Read the **Evidence** column first. `Working` means it runs in the private
implementation and is covered by tests I have run — it does **not** mean you can
verify it from this repository, because the enforcing code is not here. `Design`
means specified and not built, and no evidence is claimed for it.

| Area | Status | Evidence |
|------|--------|----------|
| Governed loop — plan → approve → execute → evaluate → remediate → close | **Working** | Private end-to-end lifecycle test; run against live model providers |
| Strict plan contract with schema validation at the boundary | **Working** | Private schema and contract tests |
| Human approval gates on irreversible and high-sensitivity actions | **Working** | Private approval-gate integration tests |
| Executor / evaluator separation | **Working** | Private dispatch and evaluation-write tests |
| Append-only audit with database-level immutability guards | **Working** | Private audit tests + a database-level trigger |
| Default-deny, scoped, expiring tool permissions | **Working** | Private tool-runtime tests |
| Credential-by-reference with redaction on logs and audit records | **Working** | Private redaction and provider tests |
| Provider adapter layer (model providers interchangeable, retirement-tolerant) | **Working** | Private provider adapter tests |
| Governance corpus — constitution, decision records, ontology, traceability | **Working** | Private decision records; Phase 0 accepted after independent review |
| Operator console — projects, plans, approvals, live execution feed | **Working** | Private end-to-end browser tests |
| Cross-platform identity / subject graph | **Design** | None claimed |
| Social platform adapters | **Design** | None claimed — deliberately last; the substrate comes first |
| Durable cross-platform memory | **Design** | None claimed |
| Multi-tenant hosted offering | **Not started** | None claimed |

Every piece of evidence above is private. That is an honest limitation of a
showcase repository, not a technicality: if independent verification matters to
you, the right response is to ask me for a walkthrough, not to take the table on
faith.

---

## Roadmap

Four horizons. Detail and sequencing rationale in
[`docs/roadmap.md`](docs/roadmap.md).

```mermaid
flowchart LR
    H0["<b>H0 — Substrate</b><br/><small>governed loop · approval gates<br/>audit · provider adapters</small>"]
    H1["<b>H1 — Surfaces</b><br/><small>console depth · transcripts<br/>intake refinement</small>"]
    H2["<b>H2 — Networks</b><br/><small>platform adapter port<br/>read-only adapters · subject graph</small>"]
    H3["<b>H3 — Layer</b><br/><small>durable memory · policy authoring<br/>multi-tenant</small>"]

    H0 --> H1 --> H2 --> H3
```

| Horizon | Status |
|---------|--------|
| H0 — Substrate | Largely complete as of 2026 H2 |
| H1 — Surfaces | In progress, 2026 H2 |
| H2 — Networks | Design — no date committed |
| H3 — Layer | Design — no date committed |

Horizons are an **ordering**, not a schedule. H0 and H1 carry dates because they
describe work that has happened or is happening. H2 and H3 carry none, because
committing a date to unstarted work would be the same overclaiming the status
table exists to prevent.

The ordering is the point. Adapters are last because an ungoverned adapter is a
liability with an API key attached.

---

## Security and privacy posture

Stated as boundaries, not as an implementation guide. Full version:
[`docs/security-boundaries.md`](docs/security-boundaries.md).

- **Secrets are referenced, never stored.** Credentials are held by reference and
  resolved at the moment of an outbound call. They are never written to prompts,
  logs, task inputs, outputs, artifacts, or audit records.
- **Default-deny permissions.** An agent may use a capability only if an explicit,
  scoped, optionally expiring grant exists. Absence is denial.
- **Agents cannot escalate themselves.** Enforced at multiple independent layers,
  and every attempt is audited whether or not it succeeded.
- **Irreversible actions require a human.** Sends, deletes, payments, publications,
  and sign-offs stop at an approval gate.
- **Self-grading is structurally impossible.** The evaluator of a result is never
  the actor that produced it.
- **History is append-only.** Execution records, evaluations, and audit events
  cannot be updated or deleted from the application — and the database enforces it
  independently.
- **Tenancy is scoped at the data layer.** Isolation is enforced where queries are
  issued, not by remembering to add a filter.
- **Errors are redacted by construction.** Public error objects carry a bounded
  category and status, never a provider message, URL, or exception chain that
  could leak a credential reference.

This repository does not describe key management, deployment topology, network
boundaries, or any control at a level of detail that would help someone attack a
running instance.

---

## Documentation map

| Document | What it covers |
|----------|----------------|
| [`docs/architecture.md`](docs/architecture.md) | Layers, ports, the governed loop, data shapes, why the boundaries sit where they do |
| [`docs/security-boundaries.md`](docs/security-boundaries.md) | Invariants and trust boundaries, stated without operational detail |
| [`docs/roadmap.md`](docs/roadmap.md) | Horizons, sequencing rationale, explicit non-goals |
| [`docs/provenance.md`](docs/provenance.md) | Where the design came from, including decisions that were wrong first |
| [`docs/ai4-positioning.md`](docs/ai4-positioning.md) | The short version, for conversations |
| [`demo/`](demo/) | Sanitized mock payloads showing the shapes involved |
| [`assets/diagrams/`](assets/diagrams/) | Mermaid sources for the diagrams above |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | What is welcome here, and what will be closed |

---

## Connect at AI4

I am **James Richmond**, and I build AgentiCubed.

If you work on agent governance, evaluation, multi-platform identity, or the
unglamorous substrate that makes autonomous systems safe to point at production —
I would like to talk.

- **GitHub:** [@JamesTRichmond](https://github.com/JamesTRichmond) · organization
  [@AgentiCubed](https://github.com/AgentiCubed)
- **LinkedIn:** [linkedin.com/in/jamestrichmond](https://www.linkedin.com/in/jamestrichmond)
- **X:** [@jamestrichmond](https://x.com/jamestrichmond)

Good conversations to have: where approval gates belong in an agentic pipeline;
whether evaluation should be structural or statistical; what a durable
cross-platform identity actually requires; and what breaks first when you give an
agent a real account.

---

## License

GitHub's license detector reads a single root `LICENSE` file, so the repository
header will not show the split. This table is the authoritative map:

| Paths | License |
|-------|---------|
| `demo/`, `assets/` | MIT — see [`LICENSE`](LICENSE) |
| `README.md`, `CONTRIBUTING.md`, `docs/` | CC BY 4.0 — see [`LICENSE-DOCS.md`](LICENSE-DOCS.md) |
| The AgentiCubed implementation | Not published here; no license granted |

The AgentiCubed name and logo are not covered by these licenses and may not be
used without permission. Copyright licenses and trademark rights are separate
things.

Note that CC BY 4.0 is a broad grant, not merely a credit requirement: it permits
adaptation and commercial reuse, subject to attribution. That is intentional for a
document whose value is being read.

## Contributions

Corrections and clarifications are welcome via issues. This is a documentation
showcase, not an active codebase, so feature pull requests will be closed — with
thanks. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
