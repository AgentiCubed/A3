import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  fnv1a, isStableToken, topShingles, buildFingerprint, matchScore, isMatch,
} from '../src/core/fingerprint.js';

const base = {
  origin: 'https://example.com',
  category: 'cookie-consent',
  tagPath: 'body>div#overlay>div',
  classTokens: ['cookie', 'consent', 'banner'],
  textShingles: ['cookies', 'consent', 'privacy', 'tracking'],
  attrHints: { role: 'dialog' },
};

test('fnv1a is deterministic and spreads', () => {
  assert.equal(fnv1a('banana'), fnv1a('banana'));
  assert.notEqual(fnv1a('banana'), fnv1a('bananb'));
  assert.match(fnv1a('x'), /^[0-9a-f]{8}$/);
});

test('stable-token filter drops build-hash noise, keeps semantic classes', () => {
  assert.ok(isStableToken('cookie-banner'));
  assert.ok(isStableToken('modal'));
  assert.ok(!isStableToken('css-1a2b3c4d'));
  assert.ok(!isStableToken('a'.repeat(30)));
  assert.ok(!isStableToken('x9f2k81q'));
});

test('topShingles normalizes and ranks keywords', () => {
  const s = topShingles('Cookies! We use cookies for consent. COOKIES matter.');
  assert.equal(s[0], 'cookies');
  assert.ok(s.includes('consent'));
});

test('identical features → same id; different origin → different id', () => {
  const a = buildFingerprint(base);
  const b = buildFingerprint(base);
  const c = buildFingerprint({ ...base, origin: 'https://other.com' });
  assert.equal(a.id, b.id);
  assert.notEqual(a.id, c.id);
});

test('exact candidate matches at score 1', () => {
  const fp = buildFingerprint(base);
  assert.equal(matchScore(fp, base), 1);
  assert.ok(isMatch(fp, base));
});

test('minor DOM churn still matches; cross-origin never does', () => {
  const fp = buildFingerprint(base);
  const churned = {
    ...base,
    classTokens: ['cookie', 'consent', 'toast'], // one class renamed
    textShingles: ['cookies', 'consent', 'privacy', 'partners'], // copy tweak
  };
  assert.ok(isMatch(fp, churned), `score was ${matchScore(fp, churned)}`);
  assert.equal(matchScore(fp, { ...base, origin: 'https://evil.example' }), 0);
});

test('a full redesign reads as a new banner', () => {
  const fp = buildFingerprint(base);
  const redesign = {
    origin: 'https://example.com',
    category: 'cookie-consent',
    tagPath: 'body>aside>section>form',
    classTokens: ['privacy-center', 'drawer'],
    textShingles: ['preferences', 'partners', 'legitimate', 'interest'],
    attrHints: {},
  };
  assert.ok(!isMatch(fp, redesign), `score was ${matchScore(fp, redesign)}`);
});
