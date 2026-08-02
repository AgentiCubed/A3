# Profile README — setup and design notes

This directory holds a ready-to-publish GitHub **profile README** for
[@JamesTRichmond](https://github.com/JamesTRichmond), plus the SVG hero assets it
depends on. It is staged here because this repository is where the work lives;
it is *deployed* by copying it into a special-purpose repository.

---

## Deploying it

A GitHub profile README lives in a public repository whose name exactly matches
the username.

1. Create a **public** repo named `JamesTRichmond/JamesTRichmond` and initialize
   it with a README.
2. Copy the contents of this directory into that repo's root:

   ```
   README.md
   assets/hero-dark.svg
   assets/hero-light.svg
   ```

   (`SETUP.md` does not need to go with it.)
3. Commit and push to that repo's default branch. GitHub renders it on
   <https://github.com/JamesTRichmond> immediately.

The image paths in `README.md` are **relative** (`assets/hero-*.svg`), so they
resolve correctly once the assets sit beside the README in that repo. Do not
rewrite them to `raw.githubusercontent.com` URLs — relative paths survive renames
and avoid the image proxy caching a stale hero for hours after an edit.

---

## Fill these in before publishing

Four placeholders are deliberately left blank rather than guessed:

| Location | What to add |
|---|---|
| `NOW` block | Exact AI4 dates, if you want them stated. |
| ACTIVE SYSTEMS → StreamKill | A one-line description. The repo itself also has no description set on GitHub — worth fixing in both places. |
| CONTACT → Email | A public-facing address. `showcase/docs/ai4-positioning.md` already flags that a personal inbox is the wrong thing to publish here. |
| CONTACT → LinkedIn | Profile URL. |

Search the README for `<!--` to find them; each is marked with an HTML comment
that will not render on the page.

---

## The design system

The reference the layout answers to is a dense operations console — a lot of
state, legible at a glance, nothing decorative. Concretely:

**No emoji.** Section markers use `▍`, a typographic block, which reads as a
panel tab rather than as decoration. Status is carried by inline-code chips
(`` `LIVE` ``, `` `BUILD` ``, `` `STAGED` ``, `` `RESEARCH` ``, `` `PRIVATE` ``)
which GitHub renders as small bordered pills — the HUD element you want, with
zero external dependencies.

**Monochrome badges, one accent.** Every badge shares
`labelColor=070B10` and `color=11202B`, with logos forced to cyan
(`logoColor=22D3EE`). This is the single biggest visual departure from the usual
profile README: a rainbow of vendor-branded badges reads as a sticker collection,
one desaturated row reads as instrumentation. If you add a badge, copy an
existing one and change only the name and `logo=` slug.

**Palette**

| Token | Dark | Light |
|---|---|---|
| Surface | `#070B10` | `#F7F9FB` |
| Panel | `#11202B` | `#FFFFFF` |
| Accent | `#22D3EE` | `#0E7490` |
| Text | `#E6EDF3` | `#0F172A` |
| Muted | `#7D93A6` | `#475569` |

**Hero.** `assets/hero-dark.svg` and `assets/hero-light.svg` are the same
composition in two palettes, swapped by `<picture>` + `prefers-color-scheme` so
it tracks the viewer's GitHub theme. Both carry two SMIL animations — a sweep
along the top rail and a slow vertical scanline — plus a pulsing `ACTIVE`
indicator. These animate inside GitHub's image proxy; they are also the first
thing to remove if you ever want it stiller. Type is set in generic families
(`monospace`, `Helvetica/Arial`) because the SVG renders on the viewer's machine
with the viewer's fonts, and the layout carries enough horizontal slack to absorb
the metric differences between platforms.

**Structure.** Hero → status row → nav → thesis → NOW → systems table → method →
stack → open questions → contact. Depth lives inside `<details>` blocks so the
default view stays one scroll. The ordering is deliberate: the thesis paragraph
appears above every project link, because the differentiator is the argument, not
the repo count.

---

## Maintenance

The `NOW` block is the only line that goes stale fast — it is the most-read text
on the page after the hero. Everything else is structural and should survive
months without edits.

When a project changes state, edit its chip in the ACTIVE SYSTEMS table rather
than reordering the table. The order is roughly "flagship first, then live, then
in-build," which stays true through most state changes.
