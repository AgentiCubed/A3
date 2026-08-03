/* Bananers preemptive suppression — the document_start path (spec §5).
 *
 * Timeline ("cloak, then close"):
 *   t=0 (document_start) → one chrome.storage.local read of this host's fps.
 *   t≈1–5ms → CLOAK: inject a <style> hiding STABLE learned kill-selectors
 *     whose policy decision is 'suppress'; arm a MutationObserver.
 *   later → recognize the element (verified selector match, else fuzzy match
 *     against popup-like candidates) → hide it immediately, then silently
 *     replay the stored strategy. The cloak keeps it invisible throughout.
 *
 * Safety hardening (from review):
 *  - Only STABLE selectors (identity-anchored, not positional nth-of-type) are
 *    trusted on the pre-paint cloak — a positional selector could otherwise
 *    hide unrelated first-party content on a later visit.
 *  - EVERY selector match is re-verified against the stored fingerprint
 *    (tokenize + similarity) before any destructive action, and fuzzy matching
 *    is restricted to popup-like elements, so a structurally-similar SPA
 *    wrapper is never removed by a slice-remove strategy.
 *  - On DOM drift the matched element is hidden BEFORE recall, so suppression
 *    never degrades to a visible flash-and-close.
 *
 * The honest boundary (docs/DESIGN.md §5): JS cannot beat paint for DOM in the
 * initial server HTML that races the first frame; the cloak read usually wins,
 * and a fuzzy sweep of existing candidates catches drifted server-rendered
 * banners the observer missed.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.suppress) return;
  const C = B.constants;

  const state = {
    settings: null,
    fingerprints: [],
    suppressible: [],  // [{ fp, decision }]
    handled: new WeakSet(),
    cloaked: false,
    observer: null,
    lastScan: null,
    disabled: false,   // set when the user revokes this origin mid-session
  };

  function looksLikePopup(node) {
    if (!node || node.nodeType !== 1 || !node.isConnected) return false;
    const role = node.getAttribute?.("role");
    if (node.tagName === "DIALOG" || role === "dialog" || role === "alertdialog" ||
        node.getAttribute?.("aria-modal") === "true") return true;
    try {
      const cs = getComputedStyle(node);
      return cs.position === "fixed" || cs.position === "sticky";
    } catch { return false; }
  }

  /* Popup-like elements to consider for an added subtree: the node itself if
   * it qualifies, plus any popup-like descendants (so a banner nested inside a
   * bulk-inserted SPA subtree is found — and acted on as the BANNER, never the
   * wrapper). Capped to keep mutation handling cheap on busy pages. */
  function popupCandidatesIn(node) {
    const out = [];
    if (looksLikePopup(node)) out.push(node);
    if (node.querySelectorAll) {
      const desc = node.querySelectorAll('[role="dialog"],[role="alertdialog"],[aria-modal="true"],dialog');
      for (let i = 0; i < desc.length && out.length < 8; i += 1) {
        if (looksLikePopup(desc[i])) out.push(desc[i]);
      }
    }
    return out;
  }

  function verifyAgainst(fp, el) {
    try {
      const tokens = B.fingerprint.tokenize(el);
      const hash = B.fingerprint.hashTokens(tokens);
      return !!B.fingerprint.match([fp], tokens, hash);
    } catch { return false; }
  }

  function cloak() {
    // Pre-paint hiding trusts ONLY stable selectors; positional fallbacks
    // can't be identity-verified before the element exists, so they are never
    // cloaked (they are still handled post-insertion with verification).
    const selectors = state.suppressible
      .flatMap(({ fp }) => [
        fp.signature?.selector,
        ...(fp.strategy?.killSelectors || []),
      ])
      .filter((s) => B.fingerprint.isStableSelector(s));
    if (!selectors.length) return;
    const valid = selectors.filter((s) => {
      try { document.createDocumentFragment().querySelector(s); return true; }
      catch { return false; }
    });
    if (!valid.length) return;
    const style = document.createElement("style");
    style.setAttribute("data-bananers-cloak", "");
    style.textContent = `${[...new Set(valid)].join(",\n")} { display: none !important; }`;
    document.documentElement.appendChild(style);
    state.cloaked = true;
  }

  /* Recognize a mutation-added node. Returns { entry, el } or null.
   * Selector matches are VERIFIED against the fingerprint; fuzzy matches run
   * only on popup-like candidates. */
  function matchNode(node) {
    // 1) verified selector match (stable or positional — both must verify).
    for (const entry of state.suppressible) {
      const sel = entry.fp.signature?.selector;
      if (!sel) continue;
      try {
        let hit = null;
        if (node.matches?.(sel)) hit = node;
        else hit = node.querySelector?.(sel) || null;
        if (hit && verifyAgainst(entry.fp, hit)) return { entry, el: hit };
      } catch { /* bad stored selector */ }
    }
    // 2) fuzzy fallback — popup-like candidates only (never arbitrary roots).
    for (const el of popupCandidatesIn(node)) {
      try {
        const tokens = B.fingerprint.tokenize(el);
        const hash = B.fingerprint.hashTokens(tokens);
        const m = B.fingerprint.match(state.suppressible.map((s) => s.fp), tokens, hash);
        if (m) return { entry: state.suppressible.find((s) => s.fp.id === m.fp.id), el };
      } catch { /* detached mid-scan */ }
    }
    return null;
  }

  async function handleRecall(entry, el) {
    if (!entry || state.handled.has(el) || state.disabled) return;
    state.handled.add(el);
    // Hide immediately so a drift-detected banner never flashes before the
    // strategy runs (the pre-paint cloak already covers stable-selector hits).
    try { el.style.setProperty("display", "none", "important"); } catch { /* ignore */ }

    const { fp } = entry;
    const res = await B.dismiss.recall(fp, el, { settings: state.settings });

    await B.store.touchFingerprint(fp.id, (rec) => {
      rec.lastSeenAt = Date.now();
      if (res.ok && res.how !== "cloak-only") rec.timesDismissed += 1;
      else if (res.how === "cloak-only") rec.timesFailed += 1;
    });
    await B.store.log({
      host: location.hostname, fpId: fp.id, type: fp.type,
      bananerId: fp.bananerId, action: "recall", outcome: res.how,
    });
    try {
      chrome.runtime.sendMessage({ type: C.MSG.DISMISSED, fpId: fp.id });
    } catch { /* SW asleep between events is fine */ }
  }

  /* Sweep already-present elements: verified stored selectors first, then a
   * fuzzy pass over detected popup candidates (server-rendered drift the
   * observer never saw inserted). */
  function checkExisting() {
    if (!document.body || state.disabled) return;
    for (const entry of state.suppressible) {
      const sel = entry.fp.signature?.selector;
      if (!sel) continue;
      try {
        const el = document.querySelector(sel);
        if (el && verifyAgainst(entry.fp, el)) handleRecall(entry, el);
      } catch { /* ignore */ }
    }
    fuzzySweep();
  }

  function fuzzySweep() {
    if (state.disabled || !state.suppressible.length) return;
    let cands;
    try { cands = B.detect.scan(); } catch { return; }
    for (const c of cands) {
      if (state.handled.has(c.el)) continue;
      try {
        const tokens = B.fingerprint.tokenize(c.el);
        const hash = B.fingerprint.hashTokens(tokens);
        const m = B.fingerprint.match(state.suppressible.map((s) => s.fp), tokens, hash);
        if (m) handleRecall(state.suppressible.find((s) => s.fp.id === m.fp.id), c.el);
      } catch { /* ignore */ }
    }
  }

  function observe() {
    if (!state.suppressible.length) return;
    state.observer = new MutationObserver((muts) => {
      if (state.disabled) return;
      for (const m of muts) {
        for (const node of m.addedNodes) {
          if (node.nodeType !== 1) continue;
          const hit = matchNode(node);
          if (hit) handleRecall(hit.entry, hit.el);
        }
      }
    });
    state.observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  /* Tear down page artifacts when the user revokes this origin mid-session
   * (the SW can unregister future injections but not stop us already running).*/
  function disable() {
    state.disabled = true;
    try { state.observer?.disconnect(); } catch { /* ignore */ }
    document.querySelectorAll("style[data-bananers-cloak],style[data-bananers-kill]")
      .forEach((n) => n.remove());
    try { B.dismiss.restoreScroll(); } catch { /* ignore */ }
  }

  async function arm() {
    const host = location.hostname;
    const { settings, fingerprints } = await B.store.getSuppressionContext(host);
    state.settings = settings;
    state.fingerprints = fingerprints;

    state.suppressible = fingerprints
      .map((fp) => ({
        fp,
        decision: B.policy.decide({
          host,
          origin: location.origin,
          type: fp.type,
          fingerprint: fp,
          settings,
          encounter: "page-load",
        }),
      }))
      .filter(({ decision }) => decision.action === "suppress");

    if (state.suppressible.length) {
      cloak();
      observe();
      checkExisting();
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", checkExisting, { once: true });
      }
      // One more fuzzy sweep after load for late server-rendered banners.
      window.addEventListener("load", () => setTimeout(fuzzySweep, 300), { once: true });
    }

    schedulePassiveReport();
  }

  /* After the page settles, count NOT-yet-learned popups and tell the SW so
   * the toolbar badge can suggest a deploy. Purely informational. */
  function schedulePassiveReport() {
    const report = () => setTimeout(async () => {
      if (state.disabled) return;
      try {
        const cands = B.detect.scan();
        const unlearned = cands.filter((c) => {
          const tokens = B.fingerprint.tokenize(c.el);
          const hash = B.fingerprint.hashTokens(tokens);
          return !B.fingerprint.match(state.fingerprints, tokens, hash);
        });
        state.lastScan = { at: Date.now(), candidates: cands.length, unlearned: unlearned.length };
        chrome.runtime.sendMessage({
          type: C.MSG.PAGE_REPORT,
          spotted: unlearned.length,
          types: [...new Set(unlearned.map((c) => c.type))],
        }).catch(() => {});
      } catch { /* never break the page */ }
    }, 1200);
    if (document.readyState === "complete") report();
    else window.addEventListener("load", report, { once: true });
  }

  /* Merge a freshly learned/updated record into the in-memory snapshot so a
   * later insertion on the same SPA page recalls it instead of re-learning. */
  function remember(fp) {
    const idx = state.fingerprints.findIndex((f) => f.id === fp.id);
    if (idx >= 0) state.fingerprints[idx] = fp; else state.fingerprints.push(fp);
  }

  B.suppress = { arm, state, disable, remember, fuzzySweep };
})();
