import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, scoreCandidate, BANNER_SCORE_THRESHOLD } from '../src/core/detect.js';
import { CATEGORIES } from '../src/shared/constants.js';

test('classify maps lexicon hits to categories', () => {
  assert.equal(classify('We use cookies for GDPR consent'), CATEGORIES.COOKIE);
  assert.equal(classify('Subscribe to our newsletter, enter your email address'), CATEGORIES.NEWSLETTER);
  assert.equal(classify('Quick question — rate your experience in this survey'), CATEGORIES.SURVEY);
  assert.equal(classify('Limited time special offer, 50% discount'), CATEGORIES.AD);
  assert.equal(classify('Welcome to our site'), CATEGORIES.GENERIC);
});

test('a classic fixed overlay dialog scores as a banner', () => {
  const score = scoreCandidate({
    overlayPositioned: true,
    dialogRole: true,
    zIndex: 9999,
    areaRatio: 0.3,
    hasCloseAffordance: true,
    bodyScrollLocked: true,
  });
  assert.ok(score >= BANNER_SCORE_THRESHOLD, `score ${score}`);
});

test('ordinary page content does not score as a banner', () => {
  const score = scoreCandidate({
    overlayPositioned: false,
    dialogRole: false,
    zIndex: 0,
    areaRatio: 0.5,
    hasCloseAffordance: false,
    bodyScrollLocked: false,
  });
  assert.ok(score < BANNER_SCORE_THRESHOLD, `score ${score}`);
});

test('a full-viewport app shell is not mistaken for a banner', () => {
  const score = scoreCandidate({
    overlayPositioned: true, // sticky headers etc.
    dialogRole: false,
    zIndex: 10,
    areaRatio: 0.99, // covers everything — outside banner band
    hasCloseAffordance: false,
    bodyScrollLocked: false,
  });
  assert.ok(score < BANNER_SCORE_THRESHOLD, `score ${score}`);
});
