// Deploy pipeline: detect → investigate → animate in character → dismiss →
// learn → (once per category) offer the keep-showing micro-prompt.

import { findBanners } from '../core/detect.js';
import { classify } from '../core/detect.js';
import { extractFeatures } from '../core/fingerprint.js';
import { buildPlan, executePlan, findCloseTarget } from '../core/dismiss.js';
import * as store from '../shared/store.js';
import { getBananer } from '../shared/roster.js';
import { VOICE, fill } from '../shared/voice.js';
import { CATEGORY_LABELS } from '../shared/constants.js';
import { playSequence, showMicroPrompt, showToast } from './animate.js';

const origin = location.origin;

// Best-effort, honest listener inspection: real getEventListeners() is
// devtools-only, so we census what a content script can legitimately see.
function inspectListeners(root) {
  const hints = [];
  const inlineHandlers = root.querySelectorAll('[onclick], [onsubmit], [onmousedown]');
  if (inlineHandlers.length > 0) hints.push(`${inlineHandlers.length} inline on* handler(s)`);
  const clickable = root.querySelectorAll('button, [role="button"], a').length;
  hints.push(`${clickable} clickable element(s)`);
  if (root.querySelector('form')) hints.push('contains a form');
  return hints;
}

function investigate(root, category) {
  const style = getComputedStyle(root);
  return {
    domSummary: `<${root.tagName.toLowerCase()}> with ${root.querySelectorAll('*').length} descendants`,
    cssSummary: `position:${style.position}; z-index:${style.zIndex}; ${Math.round(root.getBoundingClientRect().width)}×${Math.round(root.getBoundingClientRect().height)}px`,
    listenerHints: inspectListeners(root),
    notes: [
      `classified as ${CATEGORY_LABELS[category] ?? category}`,
      'listener info is best-effort: inline handlers and clickable census only',
    ],
  };
}

export async function deploy(bananerId) {
  const settings = await store.getSettings();
  const bananer = getBananer(bananerId ?? settings.activeBananer);

  const banners = findBanners(document, window);
  if (banners.length === 0) {
    showToast(bananer, VOICE.errors.noBannerFound);
    return { ok: false, reason: 'no-banner' };
  }

  // The deploy is the opt-in for automatic handling on this origin.
  await store.enableOrigin(origin);

  const root = banners[0];
  const category = classify(root.textContent ?? '');
  const fingerprint = extractFeatures(root, origin, category);
  const investigation = investigate(root, category);
  const plan = buildPlan(root, category, document);
  const target = findCloseTarget(root, category);

  await playSequence(bananer, root, target?.el ?? null);

  const dismissed = executePlan(plan, document);
  if (!dismissed) {
    showToast(bananer, VOICE.errors.dismissFailed);
    return { ok: false, reason: 'plan-failed' };
  }

  await store.saveLearned({
    fingerprint,
    plan,
    learnedBy: bananer.id,
    learnedAt: Date.now(),
    lastSeenAt: Date.now(),
    timesDismissed: 1,
    investigation,
  });
  showToast(bananer, bananer.voice.success);

  // One-time-per-category micro-prompt, never repeated regardless of answer.
  const pref = await store.getTypePref(category);
  if (!pref.promptShown) {
    await store.setTypePref(category, { promptShown: true });
    const keep = await showMicroPrompt({
      title: VOICE.prompt.keepShowingTitle,
      body: fill(VOICE.prompt.keepShowingBody, { type: (CATEGORY_LABELS[category] ?? category).toLowerCase() }),
      yes: VOICE.prompt.keepShowingYes,
      no: VOICE.prompt.keepShowingNo,
    });
    await store.setTypePref(category, { keepShowing: keep });
  }

  return { ok: true, category, fingerprintId: fingerprint.id };
}

// Watch-mode: categories the user opted to keep visible. When a learned,
// kept banner shows up, its bananer walks out and handles it live.
export async function handleKeptBanners(entries) {
  const { extractFeatures: extract } = await import('../core/fingerprint.js');
  const { isMatch } = await import('../core/fingerprint.js');

  const run = async () => {
    const roots = findBanners(document, window);
    for (const entry of entries) {
      for (const root of roots) {
        const candidate = extract(root, origin, entry.fingerprint.category);
        if (!isMatch(entry.fingerprint, candidate)) continue;
        const bananer = getBananer(entry.learnedBy);
        const target = findCloseTarget(root, entry.fingerprint.category);
        await playSequence(bananer, root, target?.el ?? null);
        const freshPlan = buildPlan(root, entry.fingerprint.category, document);
        if (executePlan(freshPlan, document)) {
          await store.recordDismissal(entry.fingerprint.id);
          showToast(bananer, bananer.voice.success);
        }
      }
    }
  };
  // Give late banners a moment to render before the show starts.
  setTimeout(() => run().catch(() => {}), 600);
}
