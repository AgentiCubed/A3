/* Bananers preemptive suppression — the document_start path (spec §5).
 *
 * Timeline ("cloak, then close"):
 *   t=0 (document_start, <html> exists, body not yet parsed)
 *     → kick off ONE chrome.storage.local read of this host's fingerprints.
 *   t≈1–5ms (read resolves; on virtually all pages this is before first paint,
 *     and always before banner scripts run — they load much later)
 *     → CLOAK: inject a <style> hiding every learned kill-selector whose
 *       policy decision is 'suppress'. Anything matching paints as nothing.
 *     → arm a MutationObserver.
 *   later (the banner's own script inserts its DOM)
 *     → observer recognizes the element (selector, then fuzzy fingerprint
 *       match) → CLOSE: silently replay the stored strategy (click the real
 *       reject/close control, Escape, removal, or css-kill). The cloak keeps
 *       it invisible during the entire recall, so even a slow strategy never
 *       flashes.
 *
 * The honest boundary: JS injection cannot beat paint for DOM that exists in
 * the initial server HTML *and* races the very first frame. The cloak read
 * usually wins even then; when it can't, the observer hides at insertion.
 * See docs/DESIGN.md §5 for the full analysis.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.suppress) return;

  const state = {
    settings: null,
    fingerprints: [],
    suppressible: [],  // [{ fp, decision }]
    handled: new WeakSet(),
    cloaked: false,
    observer: null,
    lastScan: null,
    armedAt: null,
    cloakAt: null,
  };

  function cloak() {
    const selectors = state.suppressible
      .flatMap(({ fp }) => [
        fp.signature?.selector,
        ...(fp.strategy?.killSelectors || []),
      ])
      .filter(Boolean);
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
    state.cloakAt = performance.now();
  }

  function matchNode(node) {
    for (const entry of state.suppressible) {
      const sel = entry.fp.signature?.selector;
      if (!sel) continue;
      try {
        if (node.matches?.(sel)) return { entry, el: node };
        const inner = node.querySelector?.(sel);
        if (inner) return { entry, el: inner };
      } catch { /* bad stored selector */ }
    }
    // Fuzzy second chance: only for sizable containers, and only if a cheap
    // token pass clears the similarity bar (markup drifted since learning).
    if (node.querySelectorAll && node.querySelectorAll("*").length >= 5) {
      try {
        const tokens = B.fingerprint.tokenize(node);
        const hash = B.fingerprint.hashTokens(tokens);
        const m = B.fingerprint.match(state.suppressible.map((s) => s.fp), tokens, hash);
        if (m) return { entry: state.suppressible.find((s) => s.fp.id === m.fp.id), el: node };
      } catch { /* detached mid-scan */ }
    }
    return null;
  }

  async function handleRecall(entry, el) {
    if (state.handled.has(el)) return;
    state.handled.add(el);
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
      chrome.runtime.sendMessage({ type: B.constants.MSG.DISMISSED, fpId: fp.id });
    } catch { /* SW asleep between events is fine */ }
  }

  function checkExisting() {
    if (!document.body) return;
    for (const { fp } of state.suppressible) {
      const sel = fp.signature?.selector;
      if (!sel) continue;
      try {
        const el = document.querySelector(sel);
        if (el) handleRecall(state.suppressible.find((s) => s.fp === fp), el);
      } catch { /* ignore */ }
    }
  }

  function observe() {
    if (!state.suppressible.length) return;
    state.observer = new MutationObserver((muts) => {
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

  async function arm() {
    state.armedAt = performance.now();
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
    }

    schedulePassiveReport();
  }

  /* After the page settles, count NOT-yet-learned popups and tell the SW so
   * the toolbar badge can suggest a deploy. Purely informational. */
  function schedulePassiveReport() {
    const report = () => setTimeout(async () => {
      try {
        const cands = B.detect.scan();
        const unlearned = cands.filter((c) => {
          const tokens = B.fingerprint.tokenize(c.el);
          const hash = B.fingerprint.hashTokens(tokens);
          return !B.fingerprint.match(state.fingerprints, tokens, hash);
        });
        state.lastScan = { at: Date.now(), candidates: cands.length, unlearned: unlearned.length };
        chrome.runtime.sendMessage({
          type: B.constants.MSG.PAGE_REPORT,
          spotted: unlearned.length,
          types: [...new Set(unlearned.map((c) => c.type))],
        }).catch(() => {});
      } catch { /* never break the page */ }
    }, 1200);
    if (document.readyState === "complete") report();
    else window.addEventListener("load", report, { once: true });
  }

  B.suppress = { arm, state };
})();
