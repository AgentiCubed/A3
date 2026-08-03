import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decide, registerPolicyHook, ACTIONS } from '../src/shared/policy.js';

const ctx = (over = {}) => ({
  origin: 'https://example.com',
  category: 'cookie-consent',
  originEnabled: true,
  keepShowing: false,
  isLearned: true,
  ...over,
});

test('default policy: learned + enabled + not kept → suppress', () => {
  assert.equal(decide(ctx()).action, ACTIONS.SUPPRESS);
});

test('default policy: kept types get the show', () => {
  assert.equal(decide(ctx({ keepShowing: true })).action, ACTIONS.SHOW_ANIMATED);
});

test('default policy: never acts on un-opted-in origins', () => {
  assert.equal(decide(ctx({ originEnabled: false })).action, ACTIONS.LEAVE);
});

test('default policy: unlearned banners are left for a manual deploy', () => {
  assert.equal(decide(ctx({ isLearned: false })).action, ACTIONS.LEAVE);
});

test('Banana God seam: a registered hook overrides; abstaining defers', () => {
  registerPolicyHook((c) =>
    c.origin === 'https://divine.example'
      ? { action: ACTIONS.LEAVE, reason: 'the banana god wills it' }
      : null
  );
  assert.equal(decide(ctx({ origin: 'https://divine.example' })).action, ACTIONS.LEAVE);
  assert.equal(decide(ctx()).action, ACTIONS.SUPPRESS); // abstain → default
});
