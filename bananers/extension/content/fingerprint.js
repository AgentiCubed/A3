/* Bananers fingerprinting.
 * A banner fingerprint = host + structural signature (token set + FNV-1a hash)
 * + a best-effort stable selector. Token sets survive minor DOM/markup churn:
 * random-looking tokens are normalized away and recognition falls back to
 * Jaccard similarity when the exact hash misses (spec §5).
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.fingerprint) return;
  const C = B.constants;

  /* Random-ish token → '*' so hashed builds / A-B variants still match. */
  function stableToken(tok) {
    const t = String(tok || "").toLowerCase();
    if (!t) return null;
    if (t.length > 24) return null;
    if (/\d{3,}/.test(t)) return null;                    // counters, build ids
    if (/^[0-9a-f]{6,}$/.test(t)) return null;            // hex hashes
    if (/^[a-z0-9]{8,}$/.test(t) && !/[aeiou]/.test(t)) return null; // minified
    return t;
  }

  function pushTokens(set, prefix, raw) {
    for (const part of String(raw || "").split(/[\s_.-]+/)) {
      const t = stableToken(part);
      if (t) set.add(`${prefix}:${t}`);
    }
  }

  function coverageBucket(el) {
    const r = el.getBoundingClientRect();
    const cov = (r.width * r.height) / Math.max(1, innerWidth * innerHeight);
    if (cov >= 0.8) return "full";
    if (cov >= 0.4) return "half";
    if (cov >= 0.12) return "quarter";
    return "bar";
  }

  function tokenize(el) {
    const set = new Set();
    set.add(`tag:${el.tagName.toLowerCase()}`);
    pushTokens(set, "id", el.id);
    pushTokens(set, "cls", el.className && el.className.baseVal !== undefined ? "" : el.className);
    for (const a of el.attributes || []) {
      if (/^(role|aria-modal|aria-label|data-[\w-]+)$/.test(a.name)) {
        set.add(`attr:${a.name}`);
      }
    }

    // Sample descendants breadth-first (structure matters more than depth).
    const queue = [...el.children];
    let seen = 0;
    while (queue.length && seen < 60) {
      const n = queue.shift();
      seen += 1;
      set.add(`d:${n.tagName.toLowerCase()}`);
      pushTokens(set, "did", n.id);
      if (typeof n.className === "string") pushTokens(set, "dcls", n.className);
      if (n.children.length && seen < 40) queue.push(...n.children);
    }

    // Vocabulary words present in the text (not raw text — keeps tokens stable
    // across copy tweaks and avoids storing page content).
    const text = (el.innerText || "").toLowerCase().slice(0, 4000);
    const vocab = [
      ...Object.values(C.TYPE_KEYWORDS).flat(),
      ...C.REJECT_WORDS,
      ...C.ACCEPT_WORDS.slice(0, 6),
    ];
    for (const w of vocab) if (text.includes(w)) set.add(`txt:${w}`);

    try {
      const cs = getComputedStyle(el);
      if (cs.position === "fixed" || cs.position === "sticky") set.add("geo:fixed");
      set.add(`geo:${coverageBucket(el)}`);
    } catch { /* detached */ }

    return [...set].sort();
  }

  function fnv1a(str) {
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i += 1) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193);
    }
    return (h >>> 0).toString(36);
  }

  const hashTokens = (tokens) => fnv1a(tokens.join("|"));

  function cssEscape(s) {
    return (globalThis.CSS && CSS.escape) ? CSS.escape(s) : s.replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  }

  function uniqueIn(doc, sel) {
    try { return doc.querySelectorAll(sel).length === 1 ? sel : null; }
    catch { return null; }
  }

  // A selector is "stable" if it is anchored to identity (id/class/data/role),
  // not to sibling position. Only stable selectors are trusted on the
  // pre-paint path (cloak) or as the sole basis for recall; positional
  // fallbacks must be re-verified against the fingerprint once the element
  // exists. See suppress.js / dismiss.js.
  function isStableSelector(sel) {
    return !!sel && !sel.includes(":nth-of-type(");
  }

  /* Best-effort stable, unique selector for an element. */
  function bestSelector(el, doc = document) {
    if (el.id && stableToken(el.id) !== null && el.id.length <= 40) {
      const s = uniqueIn(doc, `#${cssEscape(el.id)}`);
      if (s) return s;
    }
    if (typeof el.className === "string" && el.className.trim()) {
      const classes = el.className.trim().split(/\s+/).map(stableToken).filter(Boolean).slice(0, 3);
      if (classes.length) {
        const s = uniqueIn(doc, `${el.tagName.toLowerCase()}.${classes.map(cssEscape).join(".")}`);
        if (s) return s;
      }
    }
    for (const a of el.attributes || []) {
      if (/^data-[\w-]+$/.test(a.name) && a.value && a.value.length <= 40 && stableToken(a.value)) {
        const s = uniqueIn(doc, `${el.tagName.toLowerCase()}[${a.name}="${a.value}"]`);
        if (s) return s;
      }
    }
    if (el.getAttribute("role") === "dialog" || el.getAttribute("aria-modal") === "true") {
      const s = uniqueIn(doc, `${el.tagName.toLowerCase()}[role="dialog"]`) ||
                uniqueIn(doc, `${el.tagName.toLowerCase()}[aria-modal="true"]`);
      if (s) return s;
    }
    // Positional fallback (least stable — similarity matching compensates).
    const parts = [];
    let node = el;
    for (let depth = 0; node && node !== doc.body && depth < 5; depth += 1) {
      const tag = node.tagName.toLowerCase();
      const idx = 1 + [...(node.parentElement?.children || [])]
        .filter((s) => s.tagName === node.tagName)
        .indexOf(node);
      parts.unshift(`${tag}:nth-of-type(${idx})`);
      node = node.parentElement;
    }
    return `body > ${parts.join(" > ")}`;
  }

  function jaccard(a, b) {
    const sa = new Set(a);
    const sb = new Set(b);
    let inter = 0;
    for (const t of sa) if (sb.has(t)) inter += 1;
    const union = sa.size + sb.size - inter;
    return union === 0 ? 0 : inter / union;
  }

  /* Find the stored fingerprint matching a live element (exact hash first,
   * then similarity ≥ threshold). */
  function match(storedFps, tokens, hash) {
    for (const fp of storedFps) if (fp.signature?.hash === hash) return { fp, sim: 1 };
    let best = null;
    for (const fp of storedFps) {
      const sim = jaccard(fp.signature?.tokens || [], tokens);
      if (sim >= C.DETECT.SIM_THRESHOLD && (!best || sim > best.sim)) best = { fp, sim };
    }
    return best;
  }

  B.fingerprint = { tokenize, hashTokens, bestSelector, isStableSelector, jaccard, match, stableToken };
})();
