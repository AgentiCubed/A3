// The bananer roster. Each character differs on three coupled axes:
// appearance (svg/outfit), investigationStyle, closingTechnique — all
// reinforcing one personality. Adding a bananer = one entry here (plus,
// optionally, a new animation sequence in content/animate.js).

const bananaBody = (peel, extras = '') => `
<svg viewBox="0 0 64 96" xmlns="http://www.w3.org/2000/svg" role="img">
  <path d="M20 10 C6 34 6 62 22 82 C30 91 44 91 52 80 C38 78 26 62 26 40 C26 28 29 18 34 10 C30 6 23 6 20 10 Z"
        fill="${peel}" stroke="#3a2d14" stroke-width="2"/>
  <rect x="27" y="4" width="8" height="9" rx="2" fill="#6d5a2a"/>
  <circle cx="27" cy="40" r="2.6" fill="#241a0c"/>
  <circle cx="38" cy="40" r="2.6" fill="#241a0c"/>
  <path d="M28 50 Q33 55 39 50" stroke="#241a0c" stroke-width="2" fill="none" stroke-linecap="round"/>
  ${extras}
</svg>`;

export const ROSTER = Object.freeze([
  {
    id: 'sherlock-peel',
    name: 'Sherlock Peel',
    outfit: 'Tweed trench coat, deerstalker cap, brass magnifying glass',
    investigationStyle: 'dom-detective',
    closingTechnique: 'lockpick',
    voice: {
      bio: 'Reads a popup the way one reads a footprint: structure first, motive second. Grateful for every mystery an ape brings him — each one ripens his mind a little further.',
      deploy: 'The game is a-peel, dear ape.',
      success: 'Elementary. Its lock was never going to hold.',
    },
    svg: bananaBody('#f5d94b', `
      <path d="M12 32 Q32 22 54 32 L54 38 Q32 28 12 38 Z" fill="#8a6d3b"/>
      <circle cx="50" cy="58" r="9" fill="none" stroke="#8a5a2b" stroke-width="3"/>
      <line x1="56" y1="65" x2="62" y2="72" stroke="#8a5a2b" stroke-width="3" stroke-linecap="round"/>
    `),
  },
  {
    id: 'ninjanana',
    name: 'Ninjanana',
    outfit: 'Midnight wrap, single eye-slit, cloth-bound stem',
    investigationStyle: 'visual-hunter',
    closingTechnique: 'slice',
    voice: {
      bio: 'Speaks rarely; strikes once. At peace with the Tree, and therefore unshakeable before any z-index.',
      deploy: '…',
      success: 'It is closed.',
    },
    svg: bananaBody('#e8c93e', `
      <path d="M14 30 L56 30 L56 48 L14 48 Z" fill="#2b2b3a"/>
      <rect x="24" y="36" width="18" height="6" rx="3" fill="#f5e9c8"/>
      <circle cx="29" cy="39" r="2" fill="#241a0c"/>
      <circle cx="38" cy="39" r="2" fill="#241a0c"/>
      <path d="M8 20 L20 26" stroke="#2b2b3a" stroke-width="4" stroke-linecap="round"/>
    `),
  },
  {
    id: 'glitch',
    name: 'Glitch',
    outfit: 'Oversized hoodie, mirrored shades, one earbud',
    investigationStyle: 'listener-tracer',
    closingTechnique: 'hack',
    voice: {
      bio: 'Traces what a popup listens for, then speaks its own language back to it. Considers apes the original open-source project.',
      deploy: 'Reading its little wires, ape. One sec.',
      success: 'Patched. It agreed to leave.',
    },
    svg: bananaBody('#d9e04a', `
      <path d="M10 26 Q32 12 56 26 L56 44 Q32 34 10 44 Z" fill="#3d4a5c"/>
      <rect x="21" y="36" width="10" height="7" rx="2" fill="#9fd8ff"/>
      <rect x="34" y="36" width="10" height="7" rx="2" fill="#9fd8ff"/>
      <line x1="31" y1="39" x2="34" y2="39" stroke="#3d4a5c" stroke-width="2"/>
    `),
  },
  {
    id: 'captain-mash',
    name: 'Captain Mash',
    outfit: 'Championship belt, tiny red boxing gloves, freckle scars',
    investigationStyle: 'brute-force',
    closingTechnique: 'smash',
    voice: {
      bio: 'Tries every button until one of them is the right button. Bruised often, beautiful always, bitter never.',
      deploy: "Point me at it, ape. I'll find the close button the honest way.",
      success: 'Down in round one. Good popup, no notes.',
    },
    svg: bananaBody('#e9b93a', `
      <circle cx="18" cy="66" r="7" fill="#c0392b"/>
      <circle cx="52" cy="60" r="7" fill="#c0392b"/>
      <path d="M16 74 L52 70 L52 78 L16 82 Z" fill="#8a6d3b"/>
      <circle cx="34" cy="76" r="4" fill="#f5d94b" stroke="#6d5a2a"/>
      <circle cx="30" cy="30" r="1.5" fill="#8a5a2b"/>
      <circle cx="35" cy="26" r="1.5" fill="#8a5a2b"/>
    `),
  },
]);

export function getBananer(id) {
  return ROSTER.find((b) => b.id === id) ?? ROSTER[0];
}
