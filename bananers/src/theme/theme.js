// Theme application: the single writer of the --bn-* custom properties and
// the data-bn-texture attribute. Extension surfaces (popup, dashboard) call
// initTheme() once; the ripeness slider calls applyTheme() live while
// dragging and persists on release.

import { themeAt } from './interpolate.js';
import { STAGES } from './tokens.js';
import * as store from '../shared/store.js';

const VAR_MAP = {
  bg: '--bn-bg', surface: '--bn-surface', surfaceElevated: '--bn-surface-elevated',
  text: '--bn-text', textSecondary: '--bn-text-secondary',
  accent: '--bn-accent', accentText: '--bn-accent-text',
  border: '--bn-border', focus: '--bn-focus',
  success: '--bn-success', warn: '--bn-warn', error: '--bn-error',
};

export function applyTheme(doc, t) {
  const theme = themeAt(t);
  const root = doc.documentElement;
  for (const [token, cssVar] of Object.entries(VAR_MAP)) {
    root.style.setProperty(cssVar, theme.tokens[token]);
  }
  root.dataset.bnTexture = theme.texture;
  root.dataset.bnStage = theme.stageId;
  return theme;
}

// First run honors prefers-color-scheme: light apes start at Peak Peel,
// dark apes at Bruised & Beautiful. The slider overrides forever after.
export function defaultRipeness(win = window) {
  return win.matchMedia('(prefers-color-scheme: dark)').matches ? 0.8 : 0.4;
}

export async function initTheme(doc = document, win = window) {
  const settings = await store.getSettings();
  const t = settings.ripeness ?? defaultRipeness(win);
  return applyTheme(doc, t);
}

export async function persistRipeness(t) {
  await store.setSettings({ ripeness: t });
}

export { STAGES, themeAt };
