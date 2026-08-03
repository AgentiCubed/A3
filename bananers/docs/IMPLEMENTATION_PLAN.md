# Bananers — Implementation Plan

Companion to [DESIGN.md](./DESIGN.md). Phases 0–2 are **implemented in this
change** and verified by the e2e suite; phases 3+ are the forward plan.

## Phase 0 — Skeleton & platform ✅ (this change)
- MV3 manifest, zero default host permissions, `optional_host_permissions`
  opt-in flow (popup gesture → `permissions.request` → SW registers
  persistent `document_start` scripts per origin).
- Shared no-build module system (`globalThis.Bananers` namespace) loadable in
  content scripts, extension pages, and the SW.
- Storage schema v1 with `hostIndex` hot path + `schemaVersion` for future
  migrations; Banana God policy seam (`policy.decide` / `policy.install`).

## Phase 1 — Core loop ✅ (this change)
- Detection heuristics (fixed/dialog + coverage + affordances + type
  classification; backdrop pairing; own-UI exclusion).
- Fingerprinting (normalized token sets, FNV-1a hash, stable selector,
  Jaccard drift matching; re-learn updates in place).
- Dismissal engine: 4 strategy kinds, per-character fallback chains ending in
  `css-kill`; never-accept safety invariant enforced twice.
- "Cloak, then close" document_start suppression with removal-based recall
  verification; scroll-lock release.
- One-time-per-type micro-prompt; per-type `typeOverrides` respected by the
  page-load policy path.

## Phase 2 — Characters, UI, verification ✅ (this change)
- 5-character roster (3 aligned axes each), SVG sprites shared across
  surfaces, overlay animation framework with reduced-motion support, replay
  logs re-animated in the dashboard.
- Toolbar popup (site status, roster picker, suggestion, remember-this-site
  deploy) and Learn dashboard (roster, memory browser + forget, replays,
  settings/grants/revoke, onboarding disclosure).
- Playwright e2e suite (36 assertions) + icon generation tooling.

## Phase 3 — Robustness (next)
| Item | Notes |
|---|---|
| Shadow-DOM banner detection | pierce open roots during scan; track closed-root hosts by geometry |
| Pre-inserted hidden banners | watch `visibility`/`display` flips, not just insertions |
| SPA navigations | re-arm suppression on `history` API route changes |
| Selector healing | when recall matcher misses N times, re-run fuzzy match & refresh selector/strategy |
| Quota hygiene | LRU-evict fingerprints unseen for 90d; cap per-host records |
| Field telemetry (local only) | count cloak-vs-paint wins to decide whether the sync selector cache (DESIGN §5) is warranted |

## Phase 4 — Stretch
- `chrome.storage.sync` for settings + per-type overrides (fits quota);
  sharded fingerprint sync behind an off-by-default flag.
- CMP protocol awareness for Glitch (IAB TCF `__tcfapi` reject calls) —
  in-scope "shipped code" inspection, still never consenting on the user's
  behalf.
- Character marketplace format: roster records are already data-driven;
  validate + lazy-load sprite packs.
- Firefox port (MV3 `scripting` parity is close; `world: MAIN` differences).

## Phase 5 — Store submission
Reuse the existing submission checklist: icons ✅ (generated), screenshots
(roster, takedown, dashboard), privacy policy (all data local; enumerate the
four "never does" guarantees from onboarding), permission justifications
(storage/scripting/activeTab/optional hosts — the opt-in story is the
justification), single-purpose description.

## Deliberately out of scope (per spec §8)
Banana God orchestrator logic; cross-user learning; anti-adblock evasion;
the host product's own banners.
