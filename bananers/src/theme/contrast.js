// WCAG contrast math + the clamp that guarantees AA at every slider position.
// Pure module — unit-tested in tests/contrast.test.mjs.

export function hexToRgb(hex) {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  const n = parseInt(full, 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

export function rgbToHex({ r, g, b }) {
  const c = (v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0');
  return `#${c(r)}${c(g)}${c(b)}`;
}

export function relLuminance(hex) {
  const { r, g, b } = hexToRgb(hex);
  const lin = (v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

export function contrastRatio(a, b) {
  const la = relLuminance(a);
  const lb = relLuminance(b);
  const [hi, lo] = la >= lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

function mix(hexA, hexB, t) {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return rgbToHex({
    r: a.r + (b.r - a.r) * t,
    g: a.g + (b.g - a.g) * t,
    b: a.b + (b.b - a.b) * t,
  });
}

export const lerpHex = mix;

// Walk fg toward black or white until contrast against bg meets `min`.
// Prefers the direction fg already leans, but falls back to the opposite
// pole when that direction cannot reach the ratio (e.g. white text on a
// mid-tone accent). Converges in <= 20 steps.
export function ensureContrast(fg, bg, min = 4.5) {
  if (contrastRatio(fg, bg) >= min) return fg;
  const preferWhite = relLuminance(fg) >= relLuminance(bg);
  const preferred = preferWhite ? '#ffffff' : '#000000';
  const fallback = preferWhite ? '#000000' : '#ffffff';
  const goal = contrastRatio(preferred, bg) >= min ? preferred : fallback;
  for (let i = 1; i <= 20; i++) {
    const out = mix(fg, goal, i / 20);
    if (contrastRatio(out, bg) >= min) return out;
  }
  return goal;
}
