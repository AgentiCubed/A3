// Mechanical enforcement of the lore guardrails (docs/bananers-lore-design.md §2).
// A writer can drift from canon; this test makes it loud.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { VOICE, fill } from '../src/shared/voice.js';
import { ROSTER } from '../src/shared/roster.js';

function allStrings(obj, path = 'VOICE') {
  const out = [];
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === 'string') out.push([`${path}.${k}`, v]);
    else if (v && typeof v === 'object') out.push(...allStrings(v, `${path}.${k}`));
  }
  return out;
}

const catalog = [
  ...allStrings(VOICE),
  ...ROSTER.flatMap((b) => allStrings(b.voice, `roster.${b.id}`)),
];

test('canon: no decay-shaming, fear, or guilt vocabulary anywhere', () => {
  // Serene, never morbid; affectionate, never insulting; gratitude, never guilt.
  const forbidden = [
    /rotten/i, /decay/i, /spoiled/i,
    /afraid/i, /\bfear/i, /terrif/i, /dread/i,
    /after all i'?ve done/i, /don'?t leave/i, /are you sure you want to abandon/i,
    /stupid/i, /dumb ape/i,
  ];
  for (const [key, str] of catalog) {
    for (const re of forbidden) {
      assert.ok(!re.test(str), `${key} violates canon (${re}): "${str}"`);
    }
  }
});

test('function first: destructive strings state plainly what happens', () => {
  assert.match(VOICE.destructive.forgetBody, /learn/i);
  assert.match(VOICE.destructive.resetBody, /erases/i);
  // Confirm labels are verbs a skimming ape can parse, not just lore.
  assert.ok(VOICE.destructive.forgetConfirm.length <= 20);
  assert.ok(VOICE.destructive.resetConfirm.length <= 20);
});

test('every required touchpoint key exists', () => {
  const required = [
    VOICE.onboarding.greeting, VOICE.onboarding.permissionNote,
    VOICE.popup.deployCta, VOICE.popup.noBanners, VOICE.popup.statsLine,
    VOICE.dashboard.emptyMemory, VOICE.dashboard.memoryIntro,
    VOICE.dashboard.rosterIntro, VOICE.dashboard.prefsIntro, VOICE.dashboard.ripenessIntro,
    VOICE.errors.dismissFailed, VOICE.errors.noBannerFound,
    VOICE.destructive.forgetTitle, VOICE.destructive.forgetBody,
    VOICE.destructive.resetTitle, VOICE.destructive.resetBody,
    VOICE.prompt.keepShowingTitle, VOICE.prompt.keepShowingBody,
    VOICE.farewell.uninstall,
  ];
  for (const s of required) assert.equal(typeof s, 'string');
});

test('every bananer has bio, deploy, and success lines', () => {
  for (const b of ROSTER) {
    assert.equal(typeof b.voice.bio, 'string', b.id);
    assert.equal(typeof b.voice.deploy, 'string', b.id);
    assert.equal(typeof b.voice.success, 'string', b.id);
  }
});

test('fill() substitutes slots and leaves unknown slots visible', () => {
  assert.equal(fill('Deploy {name}', { name: 'Ninjanana' }), 'Deploy Ninjanana');
  assert.equal(fill('Hello {missing}'), 'Hello {missing}');
});

test('the greeting addresses the user as a fellow ape, warmly', () => {
  assert.match(VOICE.onboarding.greeting, /ape/i);
});
