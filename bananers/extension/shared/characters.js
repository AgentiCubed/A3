/* Bananers character roster.
 * Each bananer differs along three axes that reinforce one personality:
 *   appearance (svg), investigation style (investigation), closing technique (technique).
 * The `strategyKind` is what the character records into memory when it wins —
 * it is also what the preemptive suppressor replays on later visits. */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.characters) return;

  const ROSTER = [
    {
      id: "peel-noir",
      name: "Peel Noir",
      tagline: "Half-peeled private eye in a trench coat. Nothing stays hidden.",
      appearance: "A half-peeled banana in a trench coat and fedora, magnifier tucked in the belt.",
      investigation: "structural",
      investigationLabel: "Reads the DOM like a case file — ids, roles, aria attributes, suspicious markup.",
      technique: "lockpick",
      techniqueLabel: "Picks the lock: identifies the popup's own single best dismiss control and clicks precisely that one.",
      strategyKind: "click-precise",
      accent: "#c9a227",
    },
    {
      id: "splitsu",
      name: "Splitsu",
      tagline: "Banana ninja. Sees the ×, strikes the ×.",
      appearance: "A banana in a ninja wrap with a headband, katana on the back.",
      investigation: "visual",
      investigationLabel: "Sweeps the rendered UI for close affordances — corner glyphs, contrast, geometry.",
      technique: "slice",
      techniqueLabel: "Clean slice: cuts the overlay and its backdrop out of the page and frees the scroll.",
      strategyKind: "slice-remove",
      accent: "#5b6ee1",
    },
    {
      id: "glitch",
      name: "Glitch",
      tagline: "Hacker banana. Speaks fluent event listener.",
      appearance: "A banana in sunglasses hunched over a tiny laptop, code rain on the lenses.",
      investigation: "listeners",
      investigationLabel: "Traces JS event listeners and inline handlers to find what the popup actually reacts to.",
      technique: "protocol",
      techniqueLabel: "Speaks machine: fires the exact event sequence the popup listens for (including Escape).",
      strategyKind: "event-dispatch",
      accent: "#31c48d",
    },
    {
      id: "bruce",
      name: "Bruce Bananer",
      tagline: "You wouldn't like him when he's interrupted.",
      appearance: "A thick-set banana with boxing gloves and a taped stem.",
      investigation: "brute",
      investigationLabel: "Lines up every clickable element in the popup and sizes each one up.",
      technique: "haymaker",
      techniqueLabel: "Works the candidates in ranked order until the popup goes down — never the Accept button.",
      strategyKind: "click-dismiss",
      accent: "#e0563f",
    },
    {
      id: "frost-peel",
      name: "Frost Peel",
      tagline: "Frozen banana forensics. Ice cold under pressure.",
      appearance: "A frosted banana in an ice cube, breath fogging a large magnifying glass.",
      investigation: "styles",
      investigationLabel: "Examines computed styles — z-index stacks, backdrops, scroll locks — under the lens.",
      technique: "deep-freeze",
      techniqueLabel: "Deep freeze: derives kill-selectors and freezes the popup out with CSS before it can blink.",
      strategyKind: "css-kill",
      accent: "#63b3ed",
    },
  ];

  // Inline SVG sprites (120×120 viewBox). Shared by the page overlay, the
  // toolbar popup, and the Learn dashboard so the characters look identical
  // everywhere.
  const BODY = (extra = "") => `
    <path d="M 30 96 C 12 84 8 58 22 38 C 26 32 30 34 31 40 C 34 62 46 78 68 86
             C 84 92 96 88 102 80 C 106 74 112 78 108 86 C 98 104 56 112 30 96 Z"
          fill="#f7d154" stroke="#8a6d1a" stroke-width="3" stroke-linejoin="round"/>
    <path d="M 24 40 C 22 34 24 30 28 28 L 32 26 C 34 30 33 36 31 40 Z"
          fill="#7c5f16"/>
    ${extra}`;

  const FACE = (x, y) => `
    <circle cx="${x}" cy="${y}" r="2.6" fill="#3d2f08"/>
    <circle cx="${x + 14}" cy="${y}" r="2.6" fill="#3d2f08"/>
    <path d="M ${x + 2} ${y + 9} q 5 5 10 0" stroke="#3d2f08" stroke-width="2.4"
          fill="none" stroke-linecap="round"/>`;

  const SPRITES = {
    "peel-noir": `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Peel Noir">
      ${BODY()}
      <path d="M 34 70 L 84 88 L 82 96 L 32 78 Z" fill="#6b5b3e"/>
      <path d="M 30 62 L 90 82 L 86 92 L 28 72 Z" fill="#857149"/>
      <path d="M 44 46 L 78 58 L 74 66 L 40 54 Z" fill="#4a4034"/>
      <path d="M 36 36 L 62 30 L 70 40 L 46 48 Z" fill="#4a4034"/>
      <rect x="46" y="38" width="20" height="6" rx="3" fill="#2e2820" transform="rotate(14 56 41)"/>
      ${FACE(48, 56)}
      <circle cx="86" cy="66" r="9" fill="none" stroke="#c9a227" stroke-width="3"/>
      <line x1="92" y1="73" x2="100" y2="82" stroke="#c9a227" stroke-width="3" stroke-linecap="round"/>
    </svg>`,
    "splitsu": `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitsu">
      ${BODY()}
      <path d="M 38 46 L 80 60 L 78 70 L 36 56 Z" fill="#333a56"/>
      <rect x="40" y="47" width="34" height="9" rx="4" fill="#5b6ee1" transform="rotate(16 57 51)"/>
      <path d="M 74 52 L 96 44 L 98 48 L 78 58 Z" fill="#5b6ee1"/>
      ${FACE(48, 60)}
      <line x1="88" y1="30" x2="106" y2="64" stroke="#cbd5f5" stroke-width="4" stroke-linecap="round"/>
      <rect x="84" y="24" width="8" height="10" rx="2" fill="#333a56"/>
    </svg>`,
    "glitch": `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Glitch">
      ${BODY()}
      <rect x="42" y="50" width="30" height="10" rx="5" fill="#101418" transform="rotate(14 57 55)"/>
      <rect x="44" y="52" width="10" height="6" rx="2" fill="#31c48d" transform="rotate(14 49 55)"/>
      <rect x="58" y="56" width="10" height="6" rx="2" fill="#31c48d" transform="rotate(14 63 59)"/>
      <path d="M ${48 + 2} ${72} q 5 4 10 0" stroke="#3d2f08" stroke-width="2.4" fill="none" stroke-linecap="round"/>
      <rect x="66" y="78" width="34" height="20" rx="3" fill="#1b222c"/>
      <rect x="69" y="81" width="28" height="11" rx="1.5" fill="#0c1116"/>
      <text x="71" y="90" font-family="monospace" font-size="8" fill="#31c48d">&gt;_</text>
    </svg>`,
    "bruce": `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bruce Bananer">
      ${BODY()}
      ${FACE(48, 56)}
      <path d="M 40 30 L 30 24 M 44 28 L 40 20" stroke="#8a6d1a" stroke-width="3" stroke-linecap="round"/>
      <circle cx="94" cy="58" r="12" fill="#e0563f" stroke="#912f1d" stroke-width="3"/>
      <circle cx="26" cy="86" r="11" fill="#e0563f" stroke="#912f1d" stroke-width="3"/>
      <rect x="88" y="66" width="12" height="7" rx="3" fill="#912f1d"/>
    </svg>`,
    "frost-peel": `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frost Peel">
      <rect x="10" y="26" width="100" height="84" rx="14" fill="#bfe3f7" opacity="0.55" stroke="#7cc0e8" stroke-width="3"/>
      ${BODY()}
      ${FACE(48, 56)}
      <path d="M 40 22 L 40 12 M 35 17 L 45 17 M 90 34 L 90 24 M 85 29 L 95 29"
            stroke="#7cc0e8" stroke-width="2.6" stroke-linecap="round"/>
      <circle cx="88" cy="72" r="11" fill="none" stroke="#63b3ed" stroke-width="3.4"/>
      <line x1="95" y1="81" x2="104" y2="92" stroke="#63b3ed" stroke-width="3.4" stroke-linecap="round"/>
    </svg>`,
  };

  B.characters = {
    ROSTER,
    byId: (id) => ROSTER.find((c) => c.id === id) || ROSTER[0],
    spriteFor: (id) => SPRITES[id] || SPRITES["peel-noir"],

    /* Suggest a bananer for a banner type. Kept as a plain map so the future
     * Banana God policy layer can replace it wholesale (see shared/policy.js). */
    suggestFor(type) {
      const T = B.constants.TYPES;
      const map = {
        [T.COOKIE]: "peel-noir",
        [T.NEWSLETTER]: "splitsu",
        [T.AD]: "frost-peel",
        [T.GENERIC]: "bruce",
      };
      return map[type] || "bruce";
    },
  };
})();
