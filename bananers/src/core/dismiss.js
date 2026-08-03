// Dismissal planning and execution. buildPlan() inspects a banner root and
// produces a serializable DismissalPlan that can be persisted and replayed on
// later visits. For cookie banners the privacy-preserving choice (reject /
// necessary only) is preferred over accept. No anti-automation bypass: if a
// site defeats a stored plan, the plan simply fails and is re-learned on the
// next manual deploy.

import { CATEGORIES } from '../shared/constants.js';

// --- selector generation ----------------------------------------------------

export function stableSelector(el, doc = document) {
  if (el.id && !/\d{3,}/.test(el.id)) return `#${CSS.escape(el.id)}`;
  for (const attr of ['data-testid', 'data-cy', 'aria-label']) {
    const v = el.getAttribute(attr);
    if (v) {
      const sel = `${el.tagName.toLowerCase()}[${attr}="${CSS.escape(v)}"]`;
      if (doc.querySelectorAll(sel).length === 1) return sel;
    }
  }
  // Positional path fallback, capped depth.
  const parts = [];
  let node = el;
  for (let depth = 0; node && node.tagName && node.tagName !== 'BODY' && depth < 6; depth++) {
    const tag = node.tagName.toLowerCase();
    const parent = node.parentElement;
    if (!parent) break;
    const index = [...parent.children].filter((c) => c.tagName === node.tagName).indexOf(node) + 1;
    parts.unshift(`${tag}:nth-of-type(${index})`);
    node = parent;
  }
  return `body > ${parts.join(' > ')}`;
}

// --- close-affordance search ------------------------------------------------

const GLYPHS = ['×', '✕', '✖', 'x'];
const REJECT_WORDS = ['reject all', 'reject', 'decline', 'necessary only', 'only necessary', 'refuse'];
const CLOSE_WORDS = ['close', 'dismiss', 'no thanks', 'not now', 'maybe later', 'got it', 'skip'];

function textOf(el) {
  return (el.textContent ?? '').trim().toLowerCase();
}

function clickables(root) {
  return [...root.querySelectorAll('button, [role="button"], a, input[type="button"], input[type="submit"]')];
}

export function findCloseTarget(root, category) {
  const els = clickables(root);
  const byText = (words) =>
    els.find((el) => {
      const t = textOf(el);
      return t.length <= 40 && words.some((w) => t === w || t.includes(w));
    });

  // Cookie banners: prefer the privacy-preserving button first.
  if (category === CATEGORIES.COOKIE) {
    const reject = byText(REJECT_WORDS);
    if (reject) return { el: reject, how: 'privacy-preserving choice' };
  }
  const byAria = els.find((el) => /close|dismiss/i.test(el.getAttribute('aria-label') ?? ''));
  if (byAria) return { el: byAria, how: 'aria-labelled close' };

  const byGlyph = els.find((el) => GLYPHS.includes(textOf(el)));
  if (byGlyph) return { el: byGlyph, how: 'glyph button' };

  const byWord = byText(CLOSE_WORDS);
  if (byWord) return { el: byWord, how: 'close wording' };

  const byClass = root.querySelector('[class*="close" i]');
  if (byClass) return { el: byClass, how: 'close-classed element' };

  // Top-right positioned small button.
  const rootRect = root.getBoundingClientRect();
  const topRight = els.find((el) => {
    const r = el.getBoundingClientRect();
    return (
      r.width <= 60 && r.height <= 60 &&
      r.top - rootRect.top < 60 && rootRect.right - r.right < 60
    );
  });
  if (topRight) return { el: topRight, how: 'top-right position' };

  return null;
}

// --- plan build & execute ---------------------------------------------------

export function buildPlan(root, category, doc = document) {
  const rootSel = stableSelector(root, doc);
  const target = findCloseTarget(root, category);
  const steps = [];
  if (target) {
    steps.push({ kind: 'click', selector: stableSelector(target.el, doc), how: target.how });
  } else {
    steps.push({ kind: 'remove', selector: rootSel, how: 'no close affordance found — overlay removal' });
  }
  return {
    steps,
    hideSelectors: [rootSel],
    scrollUnlock: true,
  };
}

// Replays a stored plan. Returns true if at least one step succeeded.
export function executePlan(plan, doc = document) {
  let ok = false;
  for (const step of plan.steps) {
    const el = doc.querySelector(step.selector);
    if (!el) continue;
    if (step.kind === 'click') {
      el.click();
      ok = true;
    } else if (step.kind === 'remove') {
      el.remove();
      ok = true;
    }
  }
  if (plan.scrollUnlock) {
    doc.body.style.overflow = '';
    doc.documentElement.style.overflow = '';
  }
  return ok;
}
