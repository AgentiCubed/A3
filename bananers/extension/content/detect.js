/* Bananers popup detection.
 * Heuristic scan for third-party popup surfaces: cookie/consent modals,
 * newsletter interstitials, ad takeovers, generic dialogs. Third-party pages
 * only by construction — content scripts never run on the product's own UI
 * (spec §2), and our own overlay is tagged data-bananers-ui and excluded.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.detect) return;
  const C = B.constants;
  const T = C.TYPES;

  function isVisible(el) {
    if (!el.isConnected) return false;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || Number(cs.opacity) < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 8 && r.height > 8;
  }

  function coverage(el) {
    const r = el.getBoundingClientRect();
    const vw = Math.max(1, innerWidth);
    const vh = Math.max(1, innerHeight);
    const w = Math.min(r.right, vw) - Math.max(r.left, 0);
    const h = Math.min(r.bottom, vh) - Math.max(r.top, 0);
    if (w <= 0 || h <= 0) return 0;
    return (w * h) / (vw * vh);
  }

  const CMP_TOKEN = /(cookie|consent|gdpr|cmp|onetrust|didomi|usercentric|cookiebot|sp_message|qc-cmp|truste|privacy)/i;

  function classify(el) {
    const text = (el.innerText || "").toLowerCase().slice(0, 4000);
    const idcls = `${el.id} ${typeof el.className === "string" ? el.className : ""}`;
    const scores = { [T.COOKIE]: 0, [T.NEWSLETTER]: 0, [T.AD]: 0 };
    for (const [type, words] of Object.entries(C.TYPE_KEYWORDS)) {
      for (const w of words) if (text.includes(w)) scores[type] += 1;
    }
    if (CMP_TOKEN.test(idcls)) scores[T.COOKIE] += 2;
    if (el.querySelector('input[type="email"]')) scores[T.NEWSLETTER] += 2;
    const best = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
    return best[1] > 0 ? best[0] : T.GENERIC;
  }

  function inOwnUI(el) {
    return !!el.closest("[data-bananers-ui]");
  }

  function isBar(el) {
    const r = el.getBoundingClientRect();
    return r.width >= innerWidth * 0.9 &&
      r.height >= C.DETECT.BAR_MIN_HEIGHT &&
      (r.top <= 4 || r.bottom >= innerHeight - 4);
  }

  /* Full-viewport, low-text overlays behind/around a popup. */
  function findBackdrops(excludeWithin) {
    const out = [];
    for (const el of document.querySelectorAll("div,section")) {
      if (out.length >= 4) break;
      if (inOwnUI(el) || el === excludeWithin || excludeWithin?.contains(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.position !== "fixed") continue;
      if (!isVisible(el)) continue;
      if (coverage(el) < 0.85) continue;
      if ((el.innerText || "").trim().length >= 40 && !el.contains(excludeWithin)) continue;
      out.push(el);
    }
    return out;
  }

  function scan() {
    const nodes = [...document.querySelectorAll(
      'div,section,aside,dialog,form,[role="dialog"],[role="alertdialog"],[aria-modal="true"]'
    )].slice(0, C.DETECT.MAX_NODES);

    const raw = [];
    for (const el of nodes) {
      if (inOwnUI(el)) continue;
      if (!isVisible(el)) continue;
      const cs = getComputedStyle(el);
      const dialogish = el.tagName === "DIALOG" ||
        el.getAttribute("role") === "dialog" ||
        el.getAttribute("role") === "alertdialog" ||
        el.getAttribute("aria-modal") === "true";
      const fixedish = cs.position === "fixed" || cs.position === "sticky";
      if (!fixedish && !dialogish) continue;

      const cov = coverage(el);
      const bar = isBar(el);
      if (!dialogish && cov < C.DETECT.MIN_COVERAGE && !bar) continue;
      if (dialogish && cov < 0.02) continue;

      const z = parseInt(cs.zIndex, 10) || 0;
      if (!dialogish && !bar && z < C.DETECT.MIN_Z_INDEX && cov < 0.5) continue;

      const type = classify(el);
      const hasAffordance = !!findDismissCandidates(el, { quick: true }).length;
      // Bare full-screen veils (no text, nothing clickable) are backdrops, not
      // popups — skip them here; findBackdrops() attaches them to the real
      // candidate so slice/css strategies still take them down.
      if (cov >= 0.85 && !hasAffordance && (el.innerText || "").trim().length < 40) continue;
      const score =
        cov * 100 +
        Math.min(z, 10000) / 100 +
        (hasAffordance ? 25 : 0) +
        (type !== T.GENERIC ? 15 : 0) +
        (dialogish ? 20 : 0);

      raw.push({ el, type, score, coverage: cov, z, bar });
    }

    // Keep outermost of nested candidates (highest score wins ties).
    raw.sort((a, b) => b.score - a.score);
    const picked = [];
    for (const c of raw) {
      if (picked.some((p) => p.el.contains(c.el) || c.el.contains(p.el))) continue;
      picked.push(c);
    }
    for (const c of picked) c.backdrops = findBackdrops(c.el).filter((b) => !c.el.contains(b) && b !== c.el);
    return picked;
  }

  function labelFor(el) {
    const s = el.getAttribute?.("aria-label") || el.innerText || el.value || el.title || "";
    return s.replace(/\s+/g, " ").trim().toLowerCase().slice(0, 80);
  }

  function wordMatch(label, word) {
    if (!label) return false;
    if (word.length <= 2) return label === word;      // glyphs: ×, x, no
    return label.includes(word);
  }

  const CLOSE_GLYPHS = new Set(["×", "x", "✕", "✖", "╳", "+"]);

  /* Ranked dismissal candidates inside a popup container.
   * Accept-style controls are EXCLUDED unless allowAccept (spec: never opt the
   * user in; settings.safety.neverAccept). */
  function findDismissCandidates(container, { allowAccept = false, quick = false } = {}) {
    const sel = 'button, a[href], [role="button"], input[type="button"], input[type="submit"], ' +
      '[onclick], [aria-label], [class*="close" i], [class*="dismiss" i], [class*="reject" i]';
    const els = [...container.querySelectorAll(sel)].slice(0, 150);
    const crect = container.getBoundingClientRect();
    const out = [];
    const seen = new Set();

    for (const el of els) {
      if (seen.has(el) || !isVisible(el) || inOwnUI(el)) continue;
      seen.add(el);
      const label = labelFor(el);
      const cls = `${el.className || ""} ${el.getAttribute("aria-label") || ""}`.toLowerCase();

      const acceptIdx = C.ACCEPT_WORDS.findIndex((w) => wordMatch(label, w));
      const rejectIdx = C.REJECT_WORDS.findIndex((w) => wordMatch(label, w));
      // "reject all" contains no accept word, but "accept all" contains none of
      // reject's either; when both match (rare), reject wins only if it is the
      // more specific (longer) match.
      const isAccept = acceptIdx >= 0 && (rejectIdx < 0 || C.ACCEPT_WORDS[acceptIdx].length > C.REJECT_WORDS[rejectIdx].length);
      const isReject = rejectIdx >= 0 && !isAccept;
      const isClose = !isReject && !isAccept && (
        C.CLOSE_WORDS.some((w) => wordMatch(label, w)) ||
        CLOSE_GLYPHS.has(label) ||
        /(^|\s|-)(close|dismiss)($|\s|-)/.test(cls)
      );

      const r = el.getBoundingClientRect();
      const smallCorner =
        r.width <= 56 && r.height <= 56 &&
        r.top - crect.top <= crect.height * 0.25 &&
        crect.right - r.right <= crect.width * 0.3;

      let kind = "neutral";
      let score = 10;
      if (isAccept) { kind = "accept"; score = 1; }
      else if (isReject) { kind = "reject"; score = 100 - rejectIdx; }
      else if (isClose) { kind = "close"; score = 60 + (smallCorner ? 15 : 0); }
      else if (smallCorner && (!label || label.length <= 2)) { kind = "close"; score = 55; }
      else score += smallCorner ? 10 : 0;

      if (kind === "accept" && !allowAccept) continue;
      out.push({ el, label, kind, score });
      if (quick && out.length >= 3) break;
    }

    out.sort((a, b) => b.score - a.score);
    if (!quick) {
      for (const c of out) c.selector = B.fingerprint.bestSelector(c.el);
    }
    return out;
  }

  B.detect = { scan, findDismissCandidates, isVisible, coverage, classify, findBackdrops };
})();
