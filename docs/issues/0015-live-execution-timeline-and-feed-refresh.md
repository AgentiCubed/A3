# Issue 0015 — Live execution timeline and reliable activity feed refresh

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` C3, C5
**Suggested labels:** `type:enhancement`, `area:backend`, `area:frontend`, `track:transparency`

## Summary
Improve runtime transparency with a per-task live timeline, richer activity
metadata, and reliable refresh behavior for terminal events.

## Problem
The current live feed is too generic and can become stale, which makes it hard
to understand what the system is doing or whether the UI can be trusted.

## Desired outcome
Operators should be able to follow task progress in real time with accurate task
names, deep links, model metadata, timing, and trustworthy refresh behavior.

## Acceptance criteria
- [ ] The live view shows per-task status, task title, model/provider metadata,
      token counts, and durations.
- [ ] Activity entries deep-link to the relevant task or transcript detail.
- [ ] Terminal events refresh stale metric tiles automatically.
- [ ] The reconnect indicator reflects actual stream state rather than getting
      stuck in a misleading state.
- [ ] Automated coverage proves the feed updates correctly on terminal events.

## Dependencies
- Event payloads that carry richer execution metadata.
- Frontend subscription and refresh logic updates.

## Security and risk notes
- Live activity data must remain scoped to the project viewer.
- Token usage visibility must avoid exposing secrets or raw provider payloads.
