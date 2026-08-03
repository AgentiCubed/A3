// Popup/banner detection. DOM walking lives in findBanners(); the scoring and
// classification logic is pure over extracted feature objects so it can be
// unit-tested without a DOM.

import { CATEGORIES } from '../shared/constants.js';

// --- classification (pure) --------------------------------------------------

const LEXICON = [
  { cat: CATEGORIES.COOKIE, words: ['cookie', 'cookies', 'consent', 'gdpr', 'privacy choices', 'tracking'] },
  { cat: CATEGORIES.NEWSLETTER, words: ['newsletter', 'subscribe', 'inbox', 'sign up', 'signup', 'email address'] },
  { cat: CATEGORIES.SURVEY, words: ['survey', 'feedback', 'rate your', 'how did we do', 'quick question'] },
  { cat: CATEGORIES.AD, words: ['advertisement', 'sponsored', 'special offer', 'don’t miss', 'limited time', 'discount'] },
];

export function classify(text) {
  const t = (text ?? '').toLowerCase();
  let best = { cat: CATEGORIES.GENERIC, hits: 0 };
  for (const { cat, words } of LEXICON) {
    const hits = words.reduce((n, w) => n + (t.includes(w) ? 1 : 0), 0);
    if (hits > best.hits) best = { cat, hits };
  }
  return best.cat;
}

// --- scoring (pure) ---------------------------------------------------------

/**
 * @param {object} f candidate features
 * @param {boolean} f.overlayPositioned  position fixed/sticky
 * @param {boolean} f.dialogRole         role=dialog / aria-modal
 * @param {number}  f.zIndex
 * @param {number}  f.areaRatio          element area / viewport area
 * @param {boolean} f.hasCloseAffordance
 * @param {boolean} f.bodyScrollLocked
 * @returns {number} score in [0,1]; >= 0.5 counts as a banner
 */
export function scoreCandidate(f) {
  let score = 0;
  if (f.overlayPositioned) score += 0.3;
  if (f.dialogRole) score += 0.25;
  if (f.zIndex >= 100) score += 0.15;
  if (f.areaRatio >= 0.04 && f.areaRatio <= 0.95) score += 0.15;
  if (f.hasCloseAffordance) score += 0.1;
  if (f.bodyScrollLocked) score += 0.05;
  return Math.min(1, score);
}

export const BANNER_SCORE_THRESHOLD = 0.5;

// --- DOM walking ------------------------------------------------------------

const CLOSE_HINT = /close|dismiss|reject|decline|no.thanks|×|✕|✖/i;

export function extractCandidateFeatures(el, win) {
  const style = win.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  const viewport = win.innerWidth * win.innerHeight || 1;
  const bodyStyle = win.getComputedStyle(win.document.body);
  return {
    overlayPositioned: style.position === 'fixed' || style.position === 'sticky',
    dialogRole: el.getAttribute('role') === 'dialog' || el.getAttribute('aria-modal') === 'true',
    zIndex: Number.parseInt(style.zIndex, 10) || 0,
    areaRatio: (rect.width * rect.height) / viewport,
    hasCloseAffordance: CLOSE_HINT.test(el.innerHTML ?? ''),
    bodyScrollLocked: bodyStyle.overflow === 'hidden',
  };
}

// Returns banner root elements, highest score first, deduped by containment.
export function findBanners(doc = document, win = window) {
  const candidates = [];
  const els = doc.querySelectorAll(
    'div, section, aside, dialog, [role="dialog"], [aria-modal="true"], [class*="modal" i], [class*="banner" i], [class*="popup" i], [class*="consent" i], [class*="overlay" i]'
  );
  for (const el of els) {
    const rect = el.getBoundingClientRect();
    if (rect.width < 40 || rect.height < 24) continue; // invisible/trivial
    const features = extractCandidateFeatures(el, win);
    const score = scoreCandidate(features);
    if (score >= BANNER_SCORE_THRESHOLD) candidates.push({ el, score });
  }
  candidates.sort((a, b) => b.score - a.score);
  // Dedup: drop candidates contained inside a higher-scored candidate.
  const roots = [];
  for (const c of candidates) {
    if (!roots.some((r) => r.el.contains(c.el))) roots.push(c);
  }
  return roots.map((r) => r.el);
}
