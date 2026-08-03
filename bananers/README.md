# 🍌 Bananers — Popup-Dismissing Learning Companions

Deploy anthropomorphized banana characters that investigate annoying
third-party popups (cookie consent modals, newsletter interstitials, ad
takeovers), dismiss them in character, and **remember how** — so on your next
visit the popup is gone before you ever see it.

A real Manifest V3 browser extension. No build step, no dependencies:
`extension/` loads as-is.

- **Design:** [docs/DESIGN.md](docs/DESIGN.md) — fingerprinting & storage
  schema, the document_start "cloak, then close" suppression mechanism,
  content-script/dashboard split, character framework, Banana God policy seam.
- **Plan:** [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)

## Run it in Chrome

1. `chrome://extensions` → enable **Developer mode**
2. **Load unpacked** → select `bananers/extension/`
3. Visit a site with a popup, click the 🍌 toolbar icon, pick a bananer,
   **Deploy**. First deploy on a site asks for that site's permission only —
   nothing runs anywhere you haven't opted in.
4. Open the **Learn dashboard** (options page) for the roster, per-site
   memory browser, replays, and per-type "keep showing me these" toggles.

The five bananers: **Peel Noir** (DOM detective — picks the lock),
**Splitsu** (ninja — slices overlay & backdrop), **Glitch** (hacker — event
protocols & Escape), **Bruce Bananer** (brute — ranked clicks), **Frost
Peel** (forensics — CSS deep freeze). None of them ever click "Accept".

## Test

End-to-end against real Chromium (uses the `playwright` package, local or
global):

```bash
node bananers/test/run-tests.mjs
```

Loads the extension headless, drives six synthetic banner pages, and
asserts the whole contract: learning, safe dismissal (site records
*rejected* consent), pre-paint suppression on revisit, one-time micro-prompt,
per-type opt-in, scroll unlock, dashboard rendering — plus safety regressions
for localized labels, sticky navbars, and positional-selector hazards — 49
assertions.

## Regenerate icons

```bash
node bananers/tools/make-icons.mjs
```
# Bananers 🍌

Deploy a bananer — one of a roster of banana characters — to investigate a
popup banner inside and out (UI and code), dismiss it in character, and
**learn it**: the next time that banner tries to appear, it's gone before you
ever see it. Unless you enjoyed the show — then you can keep that popup type
around purely to watch your bananer deal with it.

Design docs (each owned by its spec):

- [Core extension](../docs/bananers-core-design.md) — architecture, fingerprinting, preemptive suppression, policy seam
- [Lifecycle theming](../docs/bananers-theming-design.md) — the ripeness slider, six stages, the AA guarantee
- [Lore & voice](../docs/bananers-lore-design.md) — canon, tone guardrails, string architecture

## Try it

1. `chrome://extensions` → enable Developer mode → **Load unpacked** → select this `bananers/` directory.
2. Open `test-pages/cookie-banner.html` or `test-pages/newsletter-modal.html` (serve them over http, e.g. `python3 -m http.server` from this directory — content scripts don't run on `file://` by default).
3. Click the Bananers toolbar icon, choose a bananer, **Deploy**. Watch the investigation and the dismissal.
4. Reload the page: the banner never appears — it was learned.
5. Open the dashboard (popup footer link or extension options) for the roster, the memory browser, per-type "keep the show" toggles, and the ripeness slider.

## Tests

Zero dependencies — pure `node:test`:

```sh
node --test bananers/tests/
```

Covers fingerprint hashing/fuzzy matching, detection scoring/classification,
the policy seam (including the Banana God hook), the **AA contrast sweep across
every slider position**, and the lore-guardrail lint over every user-facing string.

## Architecture notes

- **Zero-build**: plain ES modules everywhere; content scripts dynamically
  `import(chrome.runtime.getURL(...))`. No bundler, no `node_modules`.
- **Opt-in scoping**: automatic handling only runs on origins where you've
  deployed a bananer at least once (the deploy *is* the opt-in). Production
  path for store review — `optional_host_permissions` + per-origin registered
  content scripts — is documented in the core design doc, not yet built.
- **Honesty**: "before you see it" = hide-CSS at `document_start` + real
  dismissal moments later. Listener inspection is a legitimate census (inline
  handlers, clickable elements), not devtools magic. No anti-adblock bypass.
- **Banana God**: not implemented — only the policy hook it will one day
  plug into (`src/shared/policy.js`), per spec.
