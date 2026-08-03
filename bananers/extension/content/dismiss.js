/* Bananers dismissal engine.
 * Each character's closing technique maps to a strategy kind; every kind has
 * a fallback chain that ends in css-kill, so a deployed bananer always leaves
 * the user popup-free (utility first), while the strategy that actually
 * worked is what gets written into memory for preemptive replay.
 *
 * Safety invariant: no strategy ever activates an accept/opt-in control while
 * settings.safety.neverAccept is on (ranking already excludes them; realClick
 * re-checks as a second line of defense).
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

  function isAcceptControl(el) {
    const label = labelOf(el);
    return C.ACCEPT_WORDS.some((w) =>
      w.length <= 2 ? label === w : label.includes(w)
    ) && !C.REJECT_WORDS.some((w) => label.includes(w));
  }

  function realClick(el, { neverAccept = true } = {}) {
    if (!el || !el.isConnected) return false;
    if (neverAccept && isAcceptControl(el)) return false;
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

  function unlockScroll() {
    for (const el of [document.documentElement, document.body].filter(Boolean)) {
      const cs = getComputedStyle(el);
      if (cs.overflow === "hidden" || cs.overflowY === "hidden") {
        el.style.setProperty("overflow", "visible", "important");
      }
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

    switch (kind) {
      case "click-dismiss": {
        for (const d of findings.dismiss.slice(0, 5)) {
          if (d.kind === "accept") continue;
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
        // Fall back to firing the full pointer protocol at the top candidate.
        const d = findings.dismiss[0];
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
   * freshly recognized element (no animations, retries while the popup's own
   * scripts finish wiring up).
   *
   * IMPORTANT: while the pre-paint cloak is active the element already
   * computes display:none, so visibility-based checks would falsely report
   * success before the real dismissal (e.g. the reject click that actually
   * registers the user's refusal) has run. Click/Escape strategies therefore
   * verify REMOVAL from the DOM, not invisibility. */
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

    for (const delay of [0, 150, 500, 1200]) {
      if (delay) await wait(delay);
      if (removed()) return { ok: true, how: "already-gone" };

      if (strategy.kind === "click-dismiss" && strategy.clickSelector) {
        const btn = document.querySelector(strategy.clickSelector) ||
          el.querySelector?.(strategy.clickSelector);
        if (btn && realClick(btn, { neverAccept }) && (await waitRemoved(700))) {
          return { ok: true, how: "click-dismiss" };
        }
      } else if (strategy.kind === "event-dispatch") {
        dispatchEscape([document, document.body, el].filter(Boolean));
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

  B.dismiss = { executeWithFallback, recall, injectKillStyle, unlockScroll, isGone, verify, realClick };
})();
