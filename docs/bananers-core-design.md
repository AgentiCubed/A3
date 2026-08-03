# Bananers — Core Extension Design & Implementation Plan

Design doc owned by the **core extension spec**. Companions: `bananers-theming-design.md`, `bananers-lore-design.md`.
Implementation lives in the self-contained [`bananers/`](../bananers/) directory (portable: the directory plus these docs can be dropped into any repo unchanged).

## 1. Architecture overview

Manifest V3 browser extension, **zero-build vanilla ES modules** — no bundler, no npm install. Content scripts are classic scripts that dynamically `import(chrome.runtime.getURL(...))` shared modules (exposed via `web_accessible_resources`), which keeps every module plain, testable JavaScript.

```
bananers/
  manifest.json               MV3 manifest
  src/shared/                 constants, storage, policy hook, roster, voice catalog
  src/core/                   fingerprint, detect, dismiss (pure logic, unit-tested)
  src/content/                preempt (document_start), main (deploy flow), animate
  src/background/             service worker (message routing, badge)
  src/popup/                  toolbar popup
  src/dashboard/              "Learn" dashboard (options page)
  src/theme/                  see bananers-theming-design.md
  test-pages/                 local HTML pages with fake popups for manual testing
  tests/                      node:test unit tests (`node --test bananers/tests`)
```

## 2. Storage schema (`chrome.storage.local`, versioned keys)

| Key | Shape |
|---|---|
| `bananers/v1/learned` | `{ [fingerprintId]: LearnedBanner }` |
| `bananers/v1/prefs` | `{ typePrefs: { [category]: { keepShowing, promptShown } }, enabledOrigins: string[] }` |
| `bananers/v1/settings` | `{ activeBananer, ripeness, siteMode }` |

`LearnedBanner = { fingerprint, plan, learnedBy, learnedAt, lastSeenAt, timesDismissed, investigation }`
`investigation` is the human-readable report shown in the dashboard memory browser: DOM summary, CSS notes, listener hints (best-effort — real `getEventListeners` is devtools-only; we report inline `on*` attributes and clickable-descendant census, and say so honestly).

Schema is versioned by key prefix; a future migration reads `v1`, writes `v2`.

## 3. Fingerprinting (`src/core/fingerprint.js`)

Features extracted from a banner root element:

- `origin` — exact-match requirement (no cross-site recognition).
- `tagPath` — root's tag chain up to 5 ancestors with stable ids.
- `classTokens` — class names filtered of build-hash noise (tokens with >2 digits, length >24, or high-entropy shape are dropped).
- `textShingles` — normalized top keywords from visible text.
- `attrHints` — stable `id`/`data-*`/`role`/`aria-*` attributes.

`id = fnv1a(canonical serialization)`. Re-recognition is **fuzzy**: `matchScore(fp, candidateFeatures)` is a weighted blend of Jaccard similarity over class tokens and shingles plus tag-path similarity, gated on same origin; threshold 0.6 tolerates minor DOM churn while a full redesign correctly reads as a new banner.

## 4. Detection (`src/core/detect.js`)

Candidate scan: elements that are `fixed`/`sticky` or `role=dialog`/modal-classed, with z-index ≥ 100 and meaningful viewport coverage, plus body scroll-lock detection. Categories (`cookie-consent`, `newsletter`, `ad-interstitial`, `survey`, `generic-modal`) are assigned by a keyword lexicon over the banner's visible text. Scoring and classification are pure functions over extracted feature objects so they're unit-testable without a DOM.

## 5. Dismissal (`src/core/dismiss.js`)

`buildPlan(root)` searches for a close affordance in preference order: explicit `aria-label` close, glyph buttons (×/✕/✖), textual "close"/"no thanks"/"decline", `.close`-classed elements, top-right-positioned buttons. For `cookie-consent` banners, "reject all"/"necessary only" is preferred over "accept" — the privacy-preserving choice. Fallback: remove the overlay node and release the scroll lock. The output is a serializable `DismissalPlan { steps, hideSelectors, scrollUnlock }` using stable generated selectors — this is what gets persisted and replayed. No anti-automation bypass is attempted; a plan that stops working is re-learned on the next manual deploy.

## 6. Preemptive suppression (`src/content/preempt.js`, `document_start`)

1. At `document_start` the content script immediately reads learned banners for this origin from storage (single async read, typically resolves before first paint since parsing dominates).
2. For every learned banner whose category is *not* opted into "keep showing", it injects a `<style>` with the stored `hideSelectors` — the banner is invisible from its first frame.
3. On DOM ready + a `MutationObserver` window, it confirms matches by fingerprint score, executes the stored plan (real dismissal, not just hiding), releases scroll locks, and bumps stats.
4. Categories opted into "keep showing" skip the hide CSS; the assigned bananer instead plays its animated dismissal when the banner appears.

Honest framing: "before the user perceives it" = hide-at-first-frame + real dismissal moments later. True pre-paint suppression of arbitrary markup cannot be guaranteed for every popup pattern (e.g., late-injected scripts); the hide CSS covers the perceptual requirement.

## 7. Opt-in site scoping

`content_scripts` statically match `http(s)://*/*` for v1 simplicity, but the code is **policy-gated**: automatic (preemptive) handling only runs on `enabledOrigins`. An origin joins that list the first time the user manually deploys a bananer there — the deploy *is* the opt-in. Production path (noted, not built): move to `optional_host_permissions` + `chrome.scripting.registerContentScripts` per granted origin.

## 8. Deploy flow

Popup → `chrome.tabs.sendMessage(DEPLOY, {bananerId})` → `preempt.js` listener dynamically imports `main.js` → detect banners → investigate (build the report) → `animate.js` plays the character's investigation + closing sequence in a closed shadow-root overlay (skippable; `prefers-reduced-motion` collapses it to instant) → plan executes → banner learned → one-time per-category micro-prompt offers "keep showing this type".

## 9. Banana God extension point (flag only — not implemented)

`src/shared/policy.js` exposes `decide(ctx) -> { action, reason }` where `action ∈ { suppress-preemptively, show-and-dismiss-animated, leave-alone }`. The default policy implements today's rules (type prefs + origin enablement). `registerPolicyHook(fn)` lets a future orchestrator prepend its own decision; first non-null hook result wins. Nothing else about the Banana God is defined here, by design.

## 10. Character/animation framework

`src/shared/roster.js` defines each bananer: id, name, outfit, bio, `investigationStyle`, `closingTechnique`, inline SVG art. `src/content/animate.js` maps style/technique ids to CSS-keyframe sequences inside the shadow root. Adding a bananer = one roster entry + optionally one new sequence; no engine changes.

## 11. Implementation plan (milestones)

1. **M1 — Contracts**: constants, storage wrapper, policy hook, roster, voice catalog. ✅
2. **M2 — Engines**: fingerprint / detect / dismiss with unit tests. ✅
3. **M3 — Content pipeline**: preempt, main, animate; manual test pages. ✅
4. **M4 — Surfaces**: background worker, popup, dashboard (Learn hub). ✅
5. **M5 — Theming integration**: see `bananers-theming-design.md`. ✅
6. **M6 — Verification**: `node --test`, manual walkthrough on test pages. ✅

Deferred beyond v1: optional-permission scoping (§7), `storage.sync` cross-device memory, e2e automation via Playwright + `--load-extension`, toolbar icons.
