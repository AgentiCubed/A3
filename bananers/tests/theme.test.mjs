import { test } from 'node:test';
import assert from 'node:assert/strict';
import { contrastRatio, ensureContrast, hexToRgb, rgbToHex } from '../src/theme/contrast.js';
import { themeAt } from '../src/theme/interpolate.js';
import { STAGES } from '../src/theme/tokens.js';

test('hex round-trips', () => {
  assert.deepEqual(hexToRgb('#ffffff'), { r: 255, g: 255, b: 255 });
  assert.equal(rgbToHex({ r: 255, g: 0, b: 0 }), '#ff0000');
  assert.deepEqual(hexToRgb('#fff'), { r: 255, g: 255, b: 255 });
});

test('contrast ratio matches WCAG reference points', () => {
  assert.ok(Math.abs(contrastRatio('#000000', '#ffffff') - 21) < 0.01);
  assert.ok(Math.abs(contrastRatio('#777777', '#777777') - 1) < 0.01);
});

test('ensureContrast reaches the requested ratio', () => {
  const fixed = ensureContrast('#888888', '#999999', 4.5);
  assert.ok(contrastRatio(fixed, '#999999') >= 4.5);
});

test('every named stage passes AA out of the box', () => {
  for (const s of STAGES) {
    const { tokens } = s;
    assert.ok(contrastRatio(tokens.text, tokens.bg) >= 4.5, `${s.id} text/bg`);
    assert.ok(contrastRatio(tokens.text, tokens.surface) >= 4.5, `${s.id} text/surface`);
    assert.ok(contrastRatio(tokens.textSecondary, tokens.bg) >= 4.5, `${s.id} textSecondary/bg`);
    assert.ok(contrastRatio(tokens.accentText, tokens.accent) >= 4.5, `${s.id} accentText/accent`);
  }
});

test('THE GUARANTEE: every slider position is AA-legible (sweep 0→1)', () => {
  for (let i = 0; i <= 100; i++) {
    const t = i / 100;
    const { tokens } = themeAt(t);
    assert.ok(contrastRatio(tokens.text, tokens.bg) >= 4.5, `t=${t} text/bg`);
    assert.ok(contrastRatio(tokens.text, tokens.surface) >= 4.5, `t=${t} text/surface`);
    assert.ok(contrastRatio(tokens.textSecondary, tokens.bg) >= 4.5, `t=${t} textSecondary/bg`);
    assert.ok(contrastRatio(tokens.textSecondary, tokens.surface) >= 4.5, `t=${t} textSecondary/surface`);
    assert.ok(contrastRatio(tokens.accentText, tokens.accent) >= 4.5, `t=${t} accentText/accent`);
    assert.ok(contrastRatio(tokens.focus, tokens.bg) >= 3.0, `t=${t} focus/bg`);
  }
});

test('interpolation hits designed stages exactly at their positions', () => {
  const peak = themeAt(0.4);
  assert.equal(peak.stageId, 'peak-peel');
  assert.equal(peak.tokens.bg, STAGES[2].tokens.bg);
});

test('out-of-range t clamps instead of exploding', () => {
  assert.equal(themeAt(-1).stageId, 'just-picked');
  assert.equal(themeAt(2).stageId, 'banana-bread');
});

test('texture progresses peel → speckle → bruise', () => {
  assert.equal(themeAt(0).texture, 'peel');
  assert.equal(themeAt(0.6).texture, 'speckle');
  assert.equal(themeAt(1).texture, 'bruise');
});
