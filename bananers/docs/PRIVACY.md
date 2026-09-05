# Bananers — Privacy Policy

_Last updated: 2026-09-05_

Bananers is a browser extension that dismisses third-party popups (cookie
consent modals, newsletter interstitials, ad takeovers) and remembers how, so
it can suppress them on later visits. This policy explains exactly what data
the extension handles.

## The short version

**Bananers collects no personal data and sends nothing off your device.**
Everything it learns is stored locally in your browser and never leaves it.
There are no servers, no accounts, no analytics, and no tracking.

## What Bananers stores (locally, on your device only)

To recognize and dismiss a popup it has seen before, Bananers saves the
following in your browser's local extension storage (`chrome.storage.local`):

- **Banner fingerprints** — a structural signature of each dismissed popup:
  its element tag/id/class tokens, a CSS selector, and geometry. This is a
  fingerprint of the *popup's markup*, not of you.
- **Dismissal strategies** — how each popup was closed (which reject/close
  control was clicked, or which elements to hide).
- **A short activity log** — recent dismissals (site hostname, popup type,
  which character acted, outcome), capped and kept only for the in-extension
  "Replays" view.
- **Your settings** — chosen default character, per-popup-type preferences,
  and motion/animation choices.

Bananers does **not** store the readable text content of pages or popups. It
records only whether a small fixed list of category keywords (e.g. "cookie",
"newsletter") is present, to classify the popup type.

## What Bananers does *not* do

- It does **not** transmit any data to us or to any third party. There is no
  backend server.
- It does **not** use analytics, telemetry, advertising, or tracking of any
  kind.
- It does **not** create an account or collect your name, email, or identity.
- It does **not** sell or share data — there is no data leaving your device to
  sell or share.
- It does **not** sync across your devices. (All storage is local. If a future
  version offers optional cross-device sync via `chrome.storage.sync`, this
  policy will be updated before that ships.)
- It does **not** read or act on your own product's / first-party UI, or on any
  site you have not explicitly enabled.
- It does **not** click "Accept", "Agree", or any opt-in control on your
  behalf — dismissals only reject, close, or hide.

## Permissions and why they are needed

- **`storage`** — to save the local knowledge base described above.
- **`scripting`** and **host access** — to run the content script that
  inspects and dismisses popups. Host access is **not** requested at install
  time; it is granted **per site, by you**, the first time you deploy on that
  site, and can be revoked at any time in the extension's Settings. Without a
  grant, Bananers runs on no pages.
- **`activeTab`** — to act on the current tab for a one-time deployment when
  you have not granted persistent access to that site.

All inspection is limited to the DOM structure, computed styles, attached
event listeners, and shipped markup of popups on sites you have enabled, and
happens entirely on your device.

## Your control over your data

- **Revoke a site** at any time in Settings → Site access; the extension then
  runs on no new pages for that site.
- **Forget everything** with the "Forget everything" button in Settings, which
  clears all fingerprints, strategies, and the activity log.
- **Uninstalling** the extension removes all of its locally stored data.

## Children

Bananers is a general-purpose utility and is not directed at children under 13.
It collects no personal information from anyone.

## Changes to this policy

If this policy changes, the "Last updated" date above will change and the
revised policy will be published at the same URL before the new behavior ships.

## Contact

Questions about this policy: **&lt;add your contact email before publishing&gt;**
