// themeAt(t): the blended, AA-clamped theme for any slider position.
// Pure module — the sweep test in tests/interpolate.test.mjs asserts WCAG AA
// at every hundredth of the slider range.

import { STAGES, TOKEN_NAMES, TEXT_TOKENS, POLARITY_SWITCH_T, nearestStage } from './tokens.js';
import { lerpHex, ensureContrast } from './contrast.js';

function bracket(t) {
  for (let i = 0; i < STAGES.length - 1; i++) {
    if (t >= STAGES[i].t && t <= STAGES[i + 1].t) return [STAGES[i], STAGES[i + 1]];
  }
  return t < 0 ? [STAGES[0], STAGES[0]] : [STAGES.at(-1), STAGES.at(-1)];
}

export function themeAt(rawT) {
  const t = Math.max(0, Math.min(1, rawT));
  const [a, b] = bracket(t);
  const span = b.t - a.t || 1;
  const f = (t - a.t) / span;
  const crossesPolarity = a.texture !== 'bruise' && b.texture === 'bruise';

  const tokens = {};
  for (const name of TOKEN_NAMES) {
    if (crossesPolarity && TEXT_TOKENS.includes(name)) {
      // Never lerp text through mid-gray at the light→dark crossover.
      tokens[name] = t < POLARITY_SWITCH_T ? a.tokens[name] : b.tokens[name];
    } else {
      tokens[name] = lerpHex(a.tokens[name], b.tokens[name], f);
    }
  }

  // The AA guarantee: clamp on the *output* of every interpolation.
  tokens.text = ensureContrast(tokens.text, tokens.bg, 4.5);
  tokens.textSecondary = ensureContrast(tokens.textSecondary, tokens.bg, 4.5);
  const textOnSurface = ensureContrast(tokens.text, tokens.surface, 4.5);
  tokens.text = textOnSurface; // must hold on both bg and surface
  tokens.text = ensureContrast(tokens.text, tokens.bg, 4.5);
  tokens.textSecondary = ensureContrast(tokens.textSecondary, tokens.surface, 4.5);
  tokens.textSecondary = ensureContrast(tokens.textSecondary, tokens.bg, 4.5);
  tokens.accentText = ensureContrast(tokens.accentText, tokens.accent, 4.5);
  tokens.focus = ensureContrast(tokens.focus, tokens.bg, 3.0); // non-text UI: 3:1
  for (const s of ['success', 'warn', 'error']) {
    tokens[s] = ensureContrast(tokens[s], tokens.surface, 3.0);
  }

  const stage = nearestStage(t);
  return { t, stageId: stage.id, stageName: stage.name, texture: stage.texture, tokens };
}
