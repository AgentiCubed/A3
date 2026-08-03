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
