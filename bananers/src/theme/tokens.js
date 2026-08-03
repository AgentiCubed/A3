// The six designed lifecycle stages. Every stage is a complete token set;
// interpolate.js blends between them and clamps text tokens to WCAG AA.
// Celebration, not decay: no stage is "rotten" — see docs/bananers-theming-design.md.

export const STAGES = Object.freeze([
  {
    t: 0.0,
    id: 'just-picked',
    name: 'Just Picked',
    texture: 'peel',
    tokens: {
      bg: '#f2f7ec', surface: '#ffffff', surfaceElevated: '#e9f2df',
      text: '#1e2b16', textSecondary: '#44543a',
      accent: '#3f7d2c', accentText: '#ffffff',
      border: '#c4d6b4', focus: '#2c6b1a',
      success: '#2f7d32', warn: '#8a6408', error: '#b3362b',
    },
  },
  {
    t: 0.2,
    id: 'turning',
    name: 'Turning',
    texture: 'peel',
    tokens: {
      bg: '#f7f8e4', surface: '#fffef5', surfaceElevated: '#eff1d2',
      text: '#2a2b12', textSecondary: '#54562b',
      accent: '#556f10', accentText: '#ffffff',
      border: '#d8dcb2', focus: '#557010',
      success: '#3d7d32', warn: '#8a6408', error: '#b3362b',
    },
  },
  {
    t: 0.4,
    id: 'peak-peel',
    name: 'Peak Peel',
    texture: 'peel',
    tokens: {
      bg: '#fdf6d8', surface: '#fffdf2', surfaceElevated: '#faedb8',
      text: '#332a09', textSecondary: '#635315',
      accent: '#f5c518', accentText: '#332a09',
      border: '#e8d78f', focus: '#8a6d00',
      success: '#3d7d32', warn: '#8a5d08', error: '#b3362b',
    },
  },
  {
    t: 0.6,
    id: 'freckled',
    name: 'Freckled',
    texture: 'speckle',
    tokens: {
      bg: '#fbf0cf', surface: '#fff9e6', surfaceElevated: '#f5e5ac',
      text: '#38290c', textSecondary: '#66521e',
      accent: '#96601b', accentText: '#ffffff',
      border: '#e0cd8e', focus: '#7d5510',
      success: '#3d7d32', warn: '#8a5408', error: '#b3362b',
    },
  },
  {
    t: 0.8,
    id: 'bruised-beautiful',
    name: 'Bruised & Beautiful',
    texture: 'bruise',
    tokens: {
      bg: '#2e2118', surface: '#3a2a1e', surfaceElevated: '#473527',
      text: '#f5e6cf', textSecondary: '#d3b592',
      accent: '#d99a4e', accentText: '#2e2118',
      border: '#5c4630', focus: '#e8b06a',
      success: '#7fbf6f', warn: '#e0b45c', error: '#e88a7a',
    },
  },
  {
    t: 1.0,
    id: 'banana-bread',
    name: "Banana Bread O'Clock",
    texture: 'bruise',
    tokens: {
      bg: '#1c1410', surface: '#251a13', surfaceElevated: '#302218',
      text: '#f2e2c8', textSecondary: '#cfb694',
      accent: '#c98844', accentText: '#1c1410',
      border: '#453325', focus: '#daa268',
      success: '#7fbf6f', warn: '#e0b45c', error: '#e88a7a',
    },
  },
]);

// The polarity crossover: text tokens switch from light-stage to dark-stage
// values at this point instead of lerping through illegible mid-grays.
export const POLARITY_SWITCH_T = 0.7;

export const TOKEN_NAMES = Object.freeze(Object.keys(STAGES[0].tokens));

// Tokens whose value is text-on-background and must be polarity-switched
// rather than blended across the light→dark crossover.
export const TEXT_TOKENS = Object.freeze(['text', 'textSecondary', 'accentText']);

export function nearestStage(t) {
  let best = STAGES[0];
  for (const s of STAGES) if (Math.abs(s.t - t) < Math.abs(best.t - t)) best = s;
  return best;
}
