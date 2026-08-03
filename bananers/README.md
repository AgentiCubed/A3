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

Loads the extension headless, drives three synthetic banner pages, and
asserts the whole contract: learning, safe dismissal (site records
*rejected* consent), pre-paint suppression on revisit, one-time micro-prompt,
per-type opt-in, scroll unlock, dashboard rendering — 36 assertions.

## Regenerate icons

```bash
node bananers/tools/make-icons.mjs
```
