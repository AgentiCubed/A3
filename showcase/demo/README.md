# Demo — sanitized mock data

> **Nothing here runs.** These are static JSON documents written by hand to
> illustrate the *shapes* described in [`../docs/architecture.md`](../docs/architecture.md).
> There is no code, no client, no adapter, and nothing to execute.

## What these files are

| File | Illustrates |
|------|-------------|
| [`mock-agent-workflow.json`](mock-agent-workflow.json) | One governed run end to end: intake restatement, a rejected plan, an approved plan, capability-based assignment, a failed attempt, independent evaluation, bounded remediation, an approval gate, and closeout |
| [`mock-platform-events.json`](mock-platform-events.json) | Cross-platform observations normalized into one stream and resolved to a durable subject — including the ones that *don't* resolve |

## What these files are not

- **Not real.** Every identifier, handle, name, timestamp, score, and piece of
  content is invented. No real account, person, organization, run, or post is
  represented.
- **Not the production contract.** Field names are chosen for readability. The
  real schemas are private, are versioned, and differ. Do not build against these.
- **Not executable.** No credentials, no endpoints, no client code, no adapters.
- **Not evidence of shipped features.** `mock-platform-events.json` illustrates
  the subject graph and platform adapters, which are **design, not built**. See
  [`../docs/roadmap.md`](../docs/roadmap.md) — H2.

## Reading them

Both files carry inline `_note` and `_meta` keys — commentary embedded in the data
rather than kept in a separate document, so the explanation stays next to the
thing it explains. Underscore-prefixed keys are annotations, not fields.

Three things are worth looking for specifically:

1. **In `mock-agent-workflow.json`** — the first execution attempt is retained
   *unchanged* after the retry. History is append-only; a retry appends, it never
   overwrites. The record of a task is everything that was tried, not the last
   thing that happened.

2. **Also in `mock-agent-workflow.json`** — the publication approval fires even
   though the acting agent held a valid, scoped, unexpired grant for that
   capability. Permission answers *may this actor do this kind of thing*. The gate
   answers *should this specific thing happen now*. They are different questions
   and both must be answered.

3. **In `mock-platform-events.json`** — one event resolves to no subject and stays
   that way, and one resolves at medium confidence and is flagged for human
   confirmation rather than merged. An unattributed observation is more useful
   than a wrongly-attributed one, and confidence is never silently promoted.

## Why mock data at all

Prose describing a data model is easy to write and hard to evaluate. A concrete
document makes the design falsifiable — you can look at it and decide whether the
boundaries are actually where the documentation claims. That is the entire purpose
of these files, and it is why they are annotated rather than minimal.
