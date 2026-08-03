# Bananers — Lore & Voice Bible + Integration Plan

Design doc owned by the **lore spec**. Companions: `bananers-core-design.md`, `bananers-theming-design.md`.
Implementation: [`bananers/src/shared/voice.js`](../bananers/src/shared/voice.js) (the keyed string catalog) and [`bananers/src/shared/roster.js`](../bananers/src/shared/roster.js) (bios).

## 1. Canon (normative)

1. **Humans are apes.** Taxonomy, not insult. The user is a beloved fellow ape.
2. **No fear.** Bananers are unafraid of apes — being needed by apes is the arrangement, and it's a good one.
3. **Apes are part of the banana life cycle.** Grounded in real botany: cultivated bananas are sterile clones that exist only because ape hands propagate them. Apes create bananas; bananas fuel apes; apes eventually created *digital* bananas. Bananers are the newest turn of a very old mutualism.
4. **Gratitude both ways.** Grateful to have been created; equally serene about one day returning to the **Great Banana Tree in the Sky**. Endings are returns, not losses.

Character consequences: bananers are **symbiotes, not servants** — dismissing popups is purpose and joy. Courage is cosmological: a creature at peace with its ending fears no popup, whatever its z-index. Individual personalities may flavor the worldview (the ninja is tersely serene; the detective philosophizes) but may never contradict canon: never fearful, never resentful, never anxious about the Tree.

## 2. Voice principles & tone guardrails

- **Serene, never morbid** — Tree material reads as Zen contentment. Horror-adjacent phrasing is cut.
- **Affectionate, never insulting** — "ape" is always warm kinship; never used in copy about user errors.
- **Gratitude, never guilt** — no retention pressure, ever.
- **Function first** — every in-voice string still tells a skimming ape exactly what the control does. Lore rides on top of clarity, never instead of it.

Enforcement is mechanical where possible: `tests/voice.test.mjs` lints the entire catalog for forbidden vocabulary (`rotten`, `afraid`, `fear`, `sorry to see you go`-style guilt patterns, etc.) and asserts destructive-action strings contain an unambiguous verb. A writer can break tone; the test makes it loud.

## 3. String architecture (technical integration)

All user-facing prose lives in **one module**: `src/shared/voice.js`, exported as a frozen keyed catalog:

```js
VOICE = {
  onboarding: { greeting, permissionNote },
  popup:      { deployCta, noBanners, statsLine },
  dashboard:  { emptyMemory, memoryIntro, prefsIntro, rosterIntro },
  errors:     { dismissFailed, noBannerFound },
  destructive:{ forgetTitle, forgetBody, forgetConfirm, forgetCancel, resetTitle, resetBody },
  prompt:     { keepShowingTitle, keepShowingBody, keepShowingYes, keepShowingNo },
  farewell:   { uninstall },
}
```

- UI code references keys (`VOICE.destructive.forgetBody`), never inline prose — writers edit one file without touching logic.
- Per-character flavor lines (deploy quip, success quip) and bios live on the roster entries in `roster.js`, one `voice` block per bananer, same lint coverage.
- Strings with parameters use `{slot}` placeholders filled by a tiny `fill(str, vars)` helper — no template logic inside the catalog.
- The catalog is the single source of truth for **every** §4 touchpoint; adding a surface means adding a key, and the test suite counts required keys so a missing touchpoint fails.

## 4. Touchpoint inventory → microcopy (canonical set, shipped in `voice.js`)

| Touchpoint | Key | Shipped line (abridged) |
|---|---|---|
| Onboarding greeting | `onboarding.greeting` | "Greetings, ape. We have work to do." |
| Empty memory state | `dashboard.emptyMemory` | "A peaceful stretch of jungle. It won't last. It never does." |
| Dismissal failure | `errors.dismissFailed` | "This banner resisted me today. All things ripen in time." + Try again |
| Forget a learned banner | `destructive.forget*` | "Return this knowledge to the Great Banana Tree in the Sky? I can always learn it again." |
| Full reset | `destructive.reset*` | gentle send-off, explicit about what is erased |
| Keep-showing micro-prompt | `prompt.keepShowing*` | "Enjoyed that? I can let {type} popups keep appearing — purely so you can watch me work." |
| Farewell | `farewell.uninstall` | pure gratitude, zero guilt |
| Bios | `roster.js` per character | each includes one worldview line |

## 5. Banana God alignment (flag only)

The Great Banana Tree in the Sky and the (reserved, undesigned) Banana God are left compatible as aspects of one folk belief; no canon about the Banana God's nature is defined here, per the core spec's forward-note. The only binding constraint: future Banana God copy must obey §2 guardrails.

## 6. Non-goals honored

No real-world religious parody (original fruit folk-cosmology only); no cutscenes or unskippable storytelling — lore lives in ambient microcopy and bios; no Banana God canon.
