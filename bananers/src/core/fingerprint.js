// Banner fingerprinting: extract stable structural features from a banner
// root element, hash them into an id, and fuzzily re-recognize the banner on
// later visits despite minor DOM churn. Pure logic operates on feature
// objects so it is unit-testable without a DOM.

import { MATCH_THRESHOLD } from '../shared/constants.js';

// --- hashing ---------------------------------------------------------------

export function fnv1a(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, '0');
}

// --- feature filtering (pure) ----------------------------------------------

// Drop build-hash class noise: css-1a2b3c, _abc123XYZ, sc-gsTCUz…
export function isStableToken(token) {
  if (!token || token.length > 24) return false;
  const digits = (token.match(/\d/g) ?? []).length;
  if (digits > 2) return false;
  // hash-shaped: long run of mixed-case+digits with no vowels
  if (/^[a-z]{0,3}[-_]?[a-zA-Z0-9]{6,}$/.test(token) && !/[aeiou]/i.test(token.slice(-6))) {
    return false;
  }
  return true;
}

export function normalizeText(text) {
  return (text ?? '')
    .toLowerCase()
    .replace(/[^a-z\s]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length >= 4);
}

export function topShingles(text, n = 12) {
  const counts = new Map();
  for (const w of normalizeText(text)) counts.set(w, (counts.get(w) ?? 0) + 1);
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, n)
    .map(([w]) => w);
}

// --- feature extraction (DOM) ----------------------------------------------

export function extractFeatures(root, origin, category) {
  const classTokens = [];
  const attrHints = {};
  let el = root;
  const pathParts = [];
  for (let depth = 0; el && el.tagName && depth < 5; depth++, el = el.parentElement) {
    let part = el.tagName.toLowerCase();
    if (el.id && isStableToken(el.id)) part += `#${el.id}`;
    pathParts.unshift(part);
    if (depth === 0) {
      for (const c of el.classList ?? []) if (isStableToken(c)) classTokens.push(c);
      for (const name of ['id', 'role', 'aria-label', 'aria-modal', 'data-testid', 'data-cy']) {
        const v = el.getAttribute?.(name);
        if (v && isStableToken(v)) attrHints[name] = v;
      }
    }
  }
  return buildFingerprint({
    origin,
    category,
    tagPath: pathParts.join('>'),
    classTokens: [...new Set(classTokens)].sort(),
    textShingles: topShingles(root.textContent ?? ''),
    attrHints,
  });
}

// --- fingerprint construction & matching (pure) -----------------------------

export function buildFingerprint({ origin, category, tagPath, classTokens, textShingles, attrHints }) {
  const canonical = [origin, category, tagPath, classTokens.join('.'), textShingles.join('.')].join('|');
  return { id: fnv1a(canonical), origin, category, tagPath, classTokens, textShingles, attrHints };
}

function jaccard(a, b) {
  if (a.length === 0 && b.length === 0) return 1;
  const setA = new Set(a);
  const setB = new Set(b);
  let inter = 0;
  for (const x of setA) if (setB.has(x)) inter++;
  return inter / (setA.size + setB.size - inter);
}

function pathSimilarity(a, b) {
  const pa = a.split('>');
  const pb = b.split('>');
  let same = 0;
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) if (pa[pa.length - 1 - i] === pb[pb.length - 1 - i]) same++;
  return len === 0 ? 1 : same / len;
}

// Weighted blend in [0,1]; origin must match exactly or the score is 0.
export function matchScore(fp, candidate) {
  if (fp.origin !== candidate.origin) return 0;
  return (
    0.4 * jaccard(fp.classTokens, candidate.classTokens) +
    0.35 * jaccard(fp.textShingles, candidate.textShingles) +
    0.25 * pathSimilarity(fp.tagPath, candidate.tagPath)
  );
}

export function isMatch(fp, candidate, threshold = MATCH_THRESHOLD) {
  return matchScore(fp, candidate) >= threshold;
}
