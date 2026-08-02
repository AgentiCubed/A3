# AI4 positioning

The short version, for conversations. Written to be spoken, not read aloud.

> **Same facts as the README, stated once here so this document cannot drift into
> a stronger claim.** AgentiCubed is building a governed social-operations layer.
> The governed orchestration substrate works today, in a private repository. It
> **does not currently connect to social platforms** — no platform adapter
> exists. Nothing in this public repository runs.

---

## One sentence

AgentiCubed is an operating layer for agentic work — governance, identity,
approvals, evaluation, memory, and audit — built so that agents can be pointed at
real systems without handing them the keys.

## One paragraph

Every network and service is a silo with its own identity model, its own API, and
its own shutdown date. Building agents directly against them produces integrations
that die on vendor whim and automation nobody can safely approve. AgentiCubed
inverts the stack: a platform-neutral operating layer owns identity, policy,
orchestration, approvals, evaluation, memory, and audit, and platforms become
interchangeable adapters at the edge. The governed loop — plan, human approval,
execute, independently evaluate, bounded remediation, gated closeout — runs today
against live model providers. The social operating layer is what it is being built
toward.

---

## The thirty-second version

> "Everyone's building agents that can act. Almost nobody's building the layer
> that decides whether they *should*. AgentiCubed is that layer — approval gates,
> independent evaluation, default-deny permissions, append-only audit — with
> platforms as swappable adapters on the edge. The governed loop works today. The
> cross-platform layer on top is the direction."

## The two-minute version

**The problem.** Three failure modes kill agentic systems in production, and none
of them is model quality: the agent does something irreversible nobody approved;
the agent grades its own work and reports success; the whole thing dies when a
platform changes its API. Better models do not fix any of the three.

**The bet.** Fix them structurally. The evaluator is never the executor —
enforced at dispatch and again at write, not requested in a prompt. Irreversible
actions block on a recorded human decision, regardless of standing permission.
Permissions are default-deny, scoped, and expiring. History is append-only at both
the application and the storage layer. Credentials are referenced, never stored,
and never reach a prompt or a log.

**The architecture.** Platforms are adapters, never architecture. The domain
defines ports; vendors conform. When a provider is retired, its adapter becomes a
tombstone that fails readably with migration guidance, instead of being deleted
and turning every stored reference into an opaque crash.

**The proof that this is not theory.** A model provider was retired out from under
this build mid-project. The response was not a vendor swap — it was generalizing
the adapter layer so the next retirement costs a configuration change. That
episode, including two confident misdiagnoses along the way, is documented in
[`provenance.md`](provenance.md).

**Where it is going.** The substrate is built. The layer above it — durable
cross-platform identity, memory that outlives any one network, policy authored
once and enforced everywhere — is the product. Platform adapters come last, on
purpose, because an ungoverned adapter is a liability with an API key attached.

---

## Questions worth arguing about

Better than a pitch. These are genuinely open, and I would rather be argued with
than agreed with:

1. **Where does the approval gate belong?** Per action, per plan, or per policy?
   Per action does not scale. Per policy is how you approve something you did not
   read.
2. **Should evaluation be structural or statistical?** AgentiCubed enforces
   executor/evaluator separation structurally. Does that survive contact with
   scale, or does it become a bottleneck that gets quietly relaxed?
3. **What does durable cross-platform identity actually require?** Not "an ID" —
   what does it require in the presence of platforms that actively resist
   correlation, and should it?
4. **What is the right unit of agent memory?** Per project is tractable and wrong.
   Per subject is right and hard. What is the intermediate step that is neither
   useless nor a research programme?
5. **What breaks first when you give an agent a real account?** My money is on
   diagnostic legibility, not autonomy limits. Ask me why.

---

## Who I am looking to meet

- People working on **agent governance, evaluation, or safety substrate** —
  especially anyone who has run governed agentic work against production systems
  and has scar tissue to compare.
- People working on **cross-platform identity** or the federated/decentralized
  protocol stack.
- **Operators** who have tried to deploy agentic automation on real accounts and
  can tell me what actually broke.
- Builders who think **governance-first is the wrong order** — that argument is
  the most useful conversation I could have this week.

---

## What to look at

| If you have | Read |
|-------------|------|
| 30 seconds | The [README](../README.md) opening and the architecture diagram |
| 5 minutes | [`architecture.md`](architecture.md) §2–§5 |
| A skeptical streak | [`provenance.md`](provenance.md) — the wrong turns are the interesting part |
| A security background | [`security-boundaries.md`](security-boundaries.md) — invariants, not marketing |
| An adapter to build | [`../demo/`](../demo/) — the shapes involved |

---

## Contact

**James Richmond**

- GitHub: [@JamesTRichmond](https://github.com/JamesTRichmond) ·
  [@AgentiCubed](https://github.com/AgentiCubed)
- LinkedIn: [linkedin.com/in/jamestrichmond](https://www.linkedin.com/in/jamestrichmond)
- X: [@jamestrichmond](https://x.com/jamestrichmond)

*This repository is the public architecture showcase. The implementation is
private, and nothing here runs. If the conversation warrants it, I am happy to go
deeper than what is written here.*
