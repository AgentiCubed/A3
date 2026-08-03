/* Bananers dismissal engine.
 * Each character's closing technique maps to a strategy kind; every kind has
 * a fallback chain that ends in css-kill, so a deployed bananer always leaves
 * the user popup-free (utility first), while the strategy that actually
 * worked is what gets written into memory for preemptive replay.
 *
 * Safety invariants:
 *  - No strategy ever activates an accept/opt-in control while
 *    settings.safety.neverAccept is on. The accept guard is FAIL-CLOSED: any
 *    accept word in a control's accessible name marks it accept, and a control
 *    bearing BOTH accept and reject phrasing is treated as ambiguous and never
 *    clicked.
 *  - Under neverAccept, click strategies only ever click POSITIVELY
 *    identified reject/close controls. Unclassified ("neutral") controls —
 *    including localized labels we don't recognize — are never clicked; they
 *    fall through to containment (slice/css-kill). This closes the
 *    DOM-order-picks-accept hole on non-English banners.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.dismiss) return;
  const C = B.constants;

  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function isGone(el, backdrops = []) {
    const goneOne = (n) =>
      !n || !n.isConnected || !B.detect.isVisible(n) || B.detect.coverage(n) === 0;
    return goneOne(el) && backdrops.every(goneOne);
  }

  async function verify(el, backdrops, timeoutMs = 900) {
    const t0 = performance.now();
    while (performance.now() - t0 < timeoutMs) {
      if (isGone(el, backdrops)) return true;
      await wait(120);
    }
    return isGone(el, backdrops);
  }

  function labelOf(el) {
    return (el.getAttribute?.("aria-label") || el.innerText || el.value || "")
      .replace(/\s+/g, " ").trim().toLowerCase().slice(0, 80);
  }

  const wordHit = (label, w) => (w.length <= 2 ? label === w : label.includes(w));

  /* Fail-closed: any accept word => accept. Callers must additionally refuse
   * ambiguous controls (both accept and reject phrasing present). */
  function isAcceptControl(el) {
    const label = labelOf(el);
    return C.ACCEPT_WORDS.some((w) => wordHit(label, w));
  }
  function isAmbiguousControl(el) {
    const label = labelOf(el);
    return C.ACCEPT_WORDS.some((w) => wordHit(label, w)) &&
      C.REJECT_WORDS.some((w) => wordHit(label, w));
  }

  function realClick(el, { neverAccept = true } = {}) {
    if (!el || !el.isConnected) return false;
    if (neverAccept && (isAcceptControl(el) || isAmbiguousControl(el))) return false;
    const opts = { bubbles: true, cancelable: true, composed: true, view: window };
    try {
      el.dispatchEvent(new PointerEvent("pointerdown", opts));
      el.dispatchEvent(new MouseEvent("mousedown", opts));
      el.dispatchEvent(new PointerEvent("pointerup", opts));
      el.dispatchEvent(new MouseEvent("mouseup", opts));
      el.click();
      return true;
    } catch {
      try { el.click(); return true; } catch { return false; }
    }
  }

  /* Under neverAccept, only reject/close controls are clickable. */
  function clickable(cand, neverAccept) {
    if (cand.kind === "accept") return false;
    if (neverAccept && cand.kind !== "reject" && cand.kind !== "close") return false;
    return true;
  }

  function dispatchEscape(targets) {
    const opts = {
      key: "Escape", code: "Escape", keyCode: 27, which: 27,
      bubbles: true, cancelable: true, composed: true,
    };
    for (const t of targets) {
      try {
        t.dispatchEvent(new KeyboardEvent("keydown", opts));
        t.dispatchEvent(new KeyboardEvent("keyup", opts));
      } catch { /* ignore */ }
    }
  }

  /* Release a scroll lock, remembering the exact prior inline value so it can
   * be restored (rather than permanently forcing overflow:visible, which would
   * break a later legitimate native dialog's background-scroll lock). */
  const scrollRestore = [];
  function unlockScroll() {
    for (const el of [document.documentElement, document.body].filter(Boolean)) {
      const cs = getComputedStyle(el);
      if (cs.overflow === "hidden" || cs.overflowY === "hidden") {
        scrollRestore.push({ el, prior: el.style.getPropertyValue("overflow"), priority: el.style.getPropertyPriority("overflow") });
        el.style.setProperty("overflow", "visible", "important");
      }
    }
  }
  function restoreScroll() {
    while (scrollRestore.length) {
      const { el, prior, priority } = scrollRestore.pop();
      if (prior) el.style.setProperty("overflow", prior, priority);
      else el.style.removeProperty("overflow");
    }
  }

  let killCount = 0;
  function injectKillStyle(selectors) {
    const valid = selectors.filter((s) => {
      try { document.querySelector(s); return true; } catch { return false; }
    });
    if (!valid.length) return null;
    const style = document.createElement("style");
    style.setAttribute("data-bananers-kill", String((killCount += 1)));
    style.textContent =
      `${valid.join(",\n")} { display: none !important; visibility: hidden !important; pointer-events: none !important; }`;
    (document.head || document.documentElement).appendChild(style);
    return valid;
  }

  /* One attempt with a specific strategy kind. Returns
   * { ok, kind, clickSelector?, clickLabel? } */
  async function attempt(kind, cand, findings, { neverAccept }) {
    const el = cand.el;
    const backdrops = findings.backdrops || [];
    const clickTargets = findings.dismiss.filter((d) => clickable(d, neverAccept));

    switch (kind) {
      // Peel Noir "picks the lock": the single best legitimate control, once.
      case "click-precise": {
        const d = clickTargets[0];
        if (d && realClick(d.el, { neverAccept }) && (await verify(el, backdrops))) {
          return { ok: true, kind, clickSelector: d.selector, clickLabel: d.label };
        }
        return { ok: false, kind };
      }

      // Bruce "haymaker": work the ranked candidates until one lands.
      case "click-dismiss": {
        for (const d of clickTargets.slice(0, 5)) {
          if (!realClick(d.el, { neverAccept })) continue;
          if (await verify(el, backdrops)) {
            return { ok: true, kind, clickSelector: d.selector, clickLabel: d.label };
          }
        }
        return { ok: false, kind };
      }

      case "event-dispatch": {
        dispatchEscape([document, document.body, el].filter(Boolean));
        if (await verify(el, backdrops, 600)) return { ok: true, kind };
        const d = clickTargets[0];
        if (d && realClick(d.el, { neverAccept }) && (await verify(el, backdrops))) {
          return { ok: true, kind: "click-dismiss", clickSelector: d.selector, clickLabel: d.label };
        }
        return { ok: false, kind };
      }

      case "slice-remove": {
        try {
          el.remove();
          backdrops.forEach((b) => b.remove());
        } catch { /* ignore */ }
        if (findings.scrollLock) unlockScroll();
        return { ok: isGone(el, backdrops), kind };
      }

      case "css-kill": {
        const applied = injectKillStyle(findings.killSelectors || []);
        if (findings.scrollLock) unlockScroll();
        return { ok: !!applied && (await verify(el, backdrops, 400)), kind };
      }

      default:
        return { ok: false, kind };
    }
  }

  const CHAINS = {
    "click-precise": ["click-precise", "event-dispatch", "slice-remove", "css-kill"],
    "click-dismiss": ["click-dismiss", "event-dispatch", "slice-remove", "css-kill"],
    "event-dispatch": ["event-dispatch", "click-dismiss", "slice-remove", "css-kill"],
    "slice-remove": ["slice-remove", "css-kill"],
    "css-kill": ["css-kill", "slice-remove"],
  };

  /* Execute the character's preferred technique with fallbacks. */
  async function executeWithFallback(preferredKind, cand, findings, { settings } = {}) {
    const neverAccept = settings?.safety?.neverAccept !== false;
    // Cross-origin iframe CMPs: nothing to click from here — containment only.
    const chain = findings.iframeLocked
      ? ["slice-remove", "css-kill"]
      : CHAINS[preferredKind] || CHAINS["click-dismiss"];

    const tried = [];
    for (const kind of chain) {
      const res = await attempt(kind, cand, findings, { neverAccept });
      tried.push(kind);
      if (res.ok) return { ...res, tried };
    }
    return { ok: false, kind: null, tried };
  }

  /* Silent recall path used by the suppressor: replay a stored strategy on a
   * freshly recognized element (no animations).
   *
   * Two correctness points learned from review:
   *  - A click/Escape control is activated AT MOST ONCE across the whole retry
   *    loop, so a handler that hides-but-keeps-DOM (or a consent API call) is
   *    never fired repeatedly. Later iterations only re-check for success.
   *  - Success = the element left the DOM OR became genuinely hidden by the
   *    SITE (checked before our own cloak/kill would mask it). While the
   *    pre-paint cloak is active a click target already computes display:none,
   *    so click/Escape strategies verify REMOVAL; css/slice verify gone-ness. */
  async function recall(fp, el, { settings } = {}) {
    const neverAccept = settings?.safety?.neverAccept !== false;
    const strategy = fp.strategy || {};
    const removed = () => !el.isConnected;
    const waitRemoved = async (ms) => {
      const t0 = performance.now();
      while (performance.now() - t0 < ms) {
        if (removed()) return true;
        await wait(100);
      }
      return removed();
    };

    // Resolve a stored click target, scoped to the matched banner first so we
    // never click an unrelated element elsewhere in the page. A document-wide
    // hit is accepted only if it lives inside the banner.
    const resolveClickTarget = () => {
      const sel = strategy.clickSelector;
      if (!sel) return null;
      let btn = null;
      try { btn = el.querySelector?.(sel); } catch { /* bad selector */ }
      if (btn) return btn;
      let global = null;
      try { global = document.querySelector(sel); } catch { /* ignore */ }
      return global && el.contains(global) ? global : null;
    };

    let clickFired = false;
    for (const delay of [0, 150, 500, 1200]) {
      if (delay) await wait(delay);
      if (removed()) return { ok: true, how: "already-gone" };

      if ((strategy.kind === "click-dismiss" || strategy.kind === "click-precise") && strategy.clickSelector) {
        if (!clickFired) {
          const btn = resolveClickTarget();
          if (btn && realClick(btn, { neverAccept })) {
            clickFired = true;
            if (await waitRemoved(700)) return { ok: true, how: strategy.kind };
          }
        } else if (await waitRemoved(400)) {
          return { ok: true, how: strategy.kind };
        }
      } else if (strategy.kind === "event-dispatch") {
        if (!clickFired) {
          dispatchEscape([document, document.body, el].filter(Boolean));
          clickFired = true;
        }
        if (await waitRemoved(500)) return { ok: true, how: "event-dispatch" };
      } else if (strategy.kind === "slice-remove") {
        try { el.remove(); } catch { /* ignore */ }
        if (strategy.scrollLock) unlockScroll();
        if (removed()) return { ok: true, how: "slice-remove" };
      } else if (strategy.kind === "css-kill") {
        injectKillStyle(strategy.killSelectors || []);
        if (strategy.scrollLock) unlockScroll();
        if (await verify(el, [], 400)) return { ok: true, how: "css-kill" };
      }
    }

    // The cloak (if any) keeps it invisible even when the strategy misses.
    injectKillStyle(strategy.killSelectors || []);
    if (strategy.scrollLock) unlockScroll();
    return { ok: isGone(el, []), how: "cloak-only" };
  }

  B.dismiss = {
    executeWithFallback, recall, injectKillStyle,
    unlockScroll, restoreScroll, isGone, verify, realClick,
  };
})();
