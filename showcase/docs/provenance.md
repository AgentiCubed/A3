# Provenance

Where the design came from — including the parts that were wrong first.

Most architecture documents present a system as if it were reasoned out in advance.
It wasn't. Several of the load-bearing decisions in AgentiCubed exist because
something failed in a specific, instructive way. Those episodes are worth more
than the tidy version, so they are recorded here.

> Sanitization note: this describes *decisions and their reasoning*. It contains
> no code, no configuration, no infrastructure detail, and no private repository
> history. Third parties are named only where the fact is already public.

---

## How decisions are recorded

AgentiCubed maintains a governance corpus alongside the implementation:

| Artifact | Purpose |
|----------|---------|
| Architecture decision records | A structural choice, its alternatives, and its consequences |
| Decision records | Directional and governance decisions with explicit authority |
| Constitution | The rules the project itself operates under |
| Ontology | Controlled vocabulary, so terms mean one thing |
| Traceability protocol | Every artifact traces to the decision that authorized it |
| Reconciliation records | What was found wrong during review, and what was done about it |

Phase 0 of this corpus was formally accepted after independent review by a
reviewer who was not its author — including review findings that were blocking and
had to be repaired before acceptance.

That is more governance ceremony than a solo project needs. It exists on purpose:
a system whose product claim is *governed agentic work* has to be able to account
for its own decisions, or the claim is decoration.

---

## Episode 1 — The governance was right; the environment was broken

**What happened.** A demonstration project stalled short of completion. The
scheduler had approved a plan, dispatched work, and then the run escalated to a
human approval gate instead of finishing.

**First diagnosis.** A concurrency race in the worker layer. Plausible, and there
*was* a real race — it was found and fixed.

**Actual cause.** A dependency needed by an analysis step was missing from the
container image. The step failed. Evaluation correctly marked the output
unacceptable. Remediation correctly attempted recovery, exhausted its budget, and
correctly escalated to a human.

**What it changed.** Nothing in the governance model, which is exactly the point.
Every layer did what it was designed to do. A broken environment produced a
*halt and ask a human*, not a plausible-looking wrong answer shipped as success.

**The lesson kept:** when a governed system stops, read the stop as a signal
before reading it as a defect. The failure mode you should fear is the one where
it *doesn't* stop.

---

## Episode 2 — A vendor retired the platform underneath the build

**GitHub's public facts.** GitHub announced on 2026-07-01 that GitHub Models
would be fully retired, and retired it — playground, catalog, and inference API —
on 2026-07-30. Both statements are GitHub's own, in its changelog:

- [GitHub Models is being fully retired on July 30, 2026](https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/) (2026-07-01)
- [GitHub Models is now retired](https://github.blog/changelog/2026-07-30-github-models-is-now-retired/) (2026-07-30)

**What that meant here.** The endpoint began returning `410 Gone`. Work that had
run green through 28 July failed from 31 July with no code change on this side.
Everything below is AgentiCubed's own response, not GitHub's; nothing here rests
on non-public information, and none of it is a criticism of GitHub's decision,
which was announced with notice.

**What made it expensive.** Not the retirement itself. The retirement was
announced, and vendors are allowed to make decisions. What cost days was that the
failure was diagnosed *twice, wrongly*, because the error reaching the operator
said only that plan generation had failed. Two real bugs were found and fixed
during those days — a wrong model identifier and a starved token budget — and
neither was the cause. Both fixes were announced as "the permanent fix". Both
announcements were false.

**What it changed — three things, all structural:**

1. **One adapter, parameterized.** The vendor-specific module was replaced with a
   single adapter parameterized by endpoint and credential reference. Most
   providers speak the same protocol; adding one is now a registry entry rather
   than a new module. The cost of losing a vendor dropped to roughly zero.

2. **Retirement became a first-class state.** The dead provider is not deleted. It
   remains registered as a tombstone that fails with the correct status and
   exposes migration guidance naming the retirement date and the replacement.
   Deleting it would have converted every stored record referencing it into an
   opaque "unknown provider" crash.

3. **Diagnostic sufficiency became an invariant.** The failure was fully described
   in storage the entire time. The operator's screen showed a generic label
   because the code assembling the displayed message extracted three fields and
   silently discarded the two that carried the cause. That single omission was
   the most expensive defect in the project's history — more expensive than any
   logic bug — and it produced the standing rule that a safe error must also be a
   *sufficient* one, and must actually reach the person operating the system.

**The lesson kept:** vendor dependency is not a risk you mitigate by choosing a
better vendor. It is a risk you mitigate by making vendors interchangeable — and
by making failure legible fast enough that you diagnose the real cause on the
first attempt rather than the third.

---

## Episode 3 — Redaction that redacts too well

**What happened.** While tightening error handling, a change suppressed an
exception's declared cause but left its implicit context chain intact. The public
error object still transitively referenced an internal exception whose message
could name a credential reference.

**How it was caught.** By a pre-existing test asserting that public provider
errors carry no chained context at all. Not by review — review had already passed
it.

**What it changed.** The construction pattern. Errors that must not carry context
are now raised *outside* the handler that detected the condition, so no chain can
be attached in the first place. The property is now structural rather than
dependent on remembering a particular idiom.

**The lesson kept:** the invariants that matter are the ones you can write a test
for. "Be careful with exception chaining" is a reminder, not a control. "This
error object carries no chain, asserted in CI on every commit" is a control.

---

## Episode 4 — Show the contract, do not describe it

**What happened.** A planning step produced structurally invalid output —
repeatedly, and in the same way each time. The instructions listed every *allowed
value* for a field, and the surrounding text explained what the field meant. It
never showed the *shape*. The model produced plans that omitted required keys and
were rejected at validation.

**Why that is the system's fault, not the model's.** The model was asked to
conform to a contract it had never been shown. There was no way for it to
anticipate the rejection. Blaming the model here would have been blaming a
correctly-behaving component for a specification defect.

**What it changed.** The instruction now embeds a complete, worked example that is
itself run through the real validator by a test. If the contract and the example
drift apart, the build fails. The specification and its example cannot disagree
silently.

**The lesson kept:** when integrating a model against a strict contract, show the
contract. Descriptions of a schema are not a schema. And whatever you show it
should be verified against the same validator that will judge the output —
otherwise you have two specifications, and they will diverge.

---

## Cross-cutting principles these produced

1. **Structural beats behavioural.** If correctness depends on an instruction
   being followed, it is not a control. Executor/evaluator separation, default-deny
   grants, and append-only history are enforced by shape, not by prompt.

2. **Legibility is a safety property.** A system that fails safely but
   incomprehensibly drives its operators toward guessing, and guessing produces
   unsafe workarounds. Diagnostic sufficiency is a first-class invariant, not
   polish.

3. **Vendors are peripherals.** Every external dependency is assumed to be
   temporary. This assumption has already been vindicated once, mid-build.

4. **Halting is success.** A governed system that stops and asks a human when it
   is uncertain is working. The failure to fear is the confident wrong answer that
   sails through.

5. **Record the wrong turns.** Three of the four episodes above involve a
   confident diagnosis that was incorrect. A project that only records its
   successful reasoning is not maintaining a decision record; it is maintaining a
   press release.

---

## Attribution

AgentiCubed is designed and built by **James Richmond**. AI-assisted tools
contributed to drafting and implementation throughout. James Richmond reviewed
the published material, verified the claims and evidence identified in this
repository, and accepts responsibility for the final artifact.

Two process claims, stated narrowly because they are the supportable ones:
architectural and directional decisions are captured as written decision records
with named authority, and the Phase 0 governance review was performed by a
reviewer who was not the drafter. That is a document-and-review discipline
borrowed from the product's thinking. It is *not* the product's runtime
governance — no approval gate or automated evaluator sits between an assistant
and this repository, and it would be an overclaim to imply otherwise.
