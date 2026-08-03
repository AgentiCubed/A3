# Bananers — Lifecycle Theming Design & Implementation Plan

Design doc owned by the **theming spec** (ripeness slider). Companions: `bananers-core-design.md`, `bananers-lore-design.md`.
Implementation: [`bananers/src/theme/`](../bananers/src/theme/).

## 1. Token architecture

Every extension surface styles itself exclusively through CSS custom properties set on `:root`:

```
--bn-bg, --bn-surface, --bn-surface-elevated,
--bn-text, --bn-text-secondary,
--bn-accent, --bn-accent-text, --bn-border, --bn-focus,
--bn-success, --bn-warn, --bn-error
```

plus a `data-bn-texture` attribute selecting the stage's background texture. `theme.js#applyTheme(doc, t)` is the single writer; components never hard-code colors.

## 2. Stages

Six designed stages at fixed slider positions `t`:

| t | Stage | Role |
|---|---|---|
| 0.0 | Just Picked | crisp light, stem-green accents |
| 0.2 | Turning | warm light, green→yellow |
| 0.4 | Peak Peel | flagship light, canonical yellow |
| 0.6 | Freckled | warm light, sugar-spot speckle texture |
| 0.8 | Bruised & Beautiful | warm dark, caramel/bruise browns |
| 1.0 | Banana Bread O'Clock | full dark, near-black peel + umber |

The arc doubles as the light→dark control. First run honors `prefers-color-scheme`: light → default `t = 0.4` (Peak Peel), dark → `t = 0.8` (Bruised & Beautiful). The slider always overrides afterward; the choice persists in `bananers/v1/settings.ripeness`.

## 3. Interpolation scheme

`interpolate.js#themeAt(t)`:

1. Find the bracketing stages and linearly interpolate every color token in sRGB space (adequate for these hue-adjacent palettes; stages were designed so no lerp path crosses a muddy zone).
2. **Contrast clamp** (the AA guarantee): after interpolation, `contrast.js#ensureContrast(fg, bg, 4.5)` walks the text tokens (`--bn-text`, `--bn-text-secondary`, `--bn-accent-text` vs. their backgrounds) toward black or white — whichever direction the nearer designed stage uses — until WCAG AA (≥ 4.5:1) holds. Focus ring is clamped to ≥ 3:1 against `--bn-bg` (AA for non-text UI).

Because the clamp runs on the *output* of every interpolation, **every slider position is legible by construction**, not just the six designed stops. The unit test sweeps `t = 0 → 1` in steps of 0.01 and asserts the ratios; a stage redesign that breaks the guarantee fails CI-style at `node --test`.

The critical zone is the light→dark crossover between Freckled (0.6) and Bruised (0.8): text tokens flip polarity there. Rather than lerping text through mid-gray, text tokens **switch at the midpoint (t = 0.7)** and are then clamp-verified — no slider position ever shows gray-on-gray.

## 4. Textures

CSS/inline-SVG only, applied via `data-bn-texture`:
- `peel` — faint vertical fiber grain (repeating-linear-gradient), all stages.
- `speckle` — scattered sugar-spot dots (inline SVG data-URI), Freckled onward, density grows with ripeness.
- `bruise` — large soft radial blotches at low opacity, Bruised and Banana Bread.

All textures sit under content at ≤ 0.06 opacity so they can never affect text contrast (they modulate the background by less than the clamp's safety margin).

## 5. The slider component (`slider.js`)

- A real `<input type="range" min="0" max="1000">` for full keyboard/AT accessibility, visually styled: the track is the live lifecycle gradient, the thumb is a small banana SVG that re-colors and gains speckles/bruises as it moves (posture slumps slightly in the final stages).
- **Gentle snapping**: on release (`change`), if within 0.03 of a named stage the value snaps to it; free positions in between are kept. `aria-valuetext` announces the nearest stage name ("Freckled") rather than a raw number.
- Dragging live-applies `themeAt(t)` so ripening plays in fast-forward. With `prefers-reduced-motion`, theme changes apply instantly (no transition animation) — the same values, no tweening.
- Stage tick labels under the track double as click-to-jump targets.

## 6. Application plan

- Popup and dashboard share `theme.js` (imported as an ES module) and a common `tokens.css` consuming the custom properties.
- The in-page overlay (bananer animations on third-party sites) deliberately does **not** consume the theme — non-goal: third-party pages are never themed, and the overlay must be legible on arbitrary sites, so it uses its own fixed high-contrast palette.
- Slider lives in the dashboard's Preferences section; the popup reflects the theme but hosts no slider (space).

## 7. Tone

Stage names and any theming microcopy celebrate every stage — "Bruised & Beautiful", "Banana Bread O'Clock" — never "overripe/rotten". Voice strings live in the shared catalog (see `bananers-lore-design.md`) so the guardrail lint covers them.
