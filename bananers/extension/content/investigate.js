/* Bananers investigation engine.
 * Each investigation style examines the popup a different way — DOM structure,
 * rendered geometry, event listeners, clickable inventory, computed styles —
 * and every step is narrated through the overlay controller in character.
 * In-scope inspection surface (spec §5): DOM tree, computed styles, attached
 * event listeners, shipped markup. Nothing else.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.investigate) return;

  const rectOf = (el) => {
    const r = el.getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  };

  /* Ask the MAIN-world probe for listener info on an element (best-effort;
   * display/ranking only — see main-world-probe.js). */
  function queryListeners(el, timeoutMs = 300) {
    return new Promise((resolve) => {
      const token = `t${Math.floor(performance.now())}-${Math.floor(Math.random() * 1e6)}`;
      el.setAttribute("data-bananers-probe-target", token);
      const timer = setTimeout(() => { cleanup(); resolve(null); }, timeoutMs);
      function onMsg(ev) {
        const d = ev.data;
        if (ev.source !== window || !d || d.__bananers !== "listener-reply" || d.token !== token) return;
        cleanup();
        resolve(d.summary);
      }
      function cleanup() {
        clearTimeout(timer);
        window.removeEventListener("message", onMsg);
        el.removeAttribute("data-bananers-probe-target");
      }
      window.addEventListener("message", onMsg);
      window.postMessage({ __bananers: "listener-query", token }, "*");
    });
  }

  function crossOriginIframeOnly(el) {
    if (el.tagName === "IFRAME") {
      try { void el.contentDocument.body; return false; } catch { return true; }
    }
    const frames = el.querySelectorAll("iframe");
    if (!frames.length) return false;
    const clickables = B.detect.findDismissCandidates(el, { quick: true });
    if (clickables.length) return false;
    for (const f of frames) {
      try { void f.contentDocument.body; return false; } catch { /* locked */ }
    }
    return true;
  }

  async function run(character, cand, { settings, ctl }) {
    const el = cand.el;
    const style = character.investigation;
    const steps = [];
    const t0 = performance.now();
    const note = async (label, rect) => {
      steps.push({ t: Math.round(performance.now() - t0), act: "step", label });
      if (ctl) await ctl.step(label, rect);
    };

    const findings = {
      type: cand.type,
      scrollLock: false,
      iframeLocked: false,
      listeners: null,
      dismiss: [],
      killSelectors: [],
      backdrops: cand.backdrops || [],
    };

    // Everyone computes the containment set: without it neither the pre-paint
    // cloak nor the css-kill fallback can work.
    findings.killSelectors = [B.fingerprint.bestSelector(el)];
    for (const bd of findings.backdrops.slice(0, 3)) {
      findings.killSelectors.push(B.fingerprint.bestSelector(bd));
    }
    const htmlCS = getComputedStyle(document.documentElement);
    const bodyCS = document.body ? getComputedStyle(document.body) : null;
    findings.scrollLock =
      htmlCS.overflow === "hidden" || (bodyCS && bodyCS.overflow === "hidden");

    findings.iframeLocked = crossOriginIframeOnly(el);
    const allowAccept = settings?.safety?.neverAccept === false;
    findings.dismiss = B.detect.findDismissCandidates(el, { allowAccept });

    const r = rectOf(el);

    switch (style) {
      case "structural": {
        await note("Opening the case file on this popup…", r);
        const all = el.querySelectorAll("*").length;
        const buttons = el.querySelectorAll('button,[role="button"],a[href]').length;
        await note(`Case notes: ${all} elements, ${buttons} controls, role="${el.getAttribute("role") || "none"}".`);
        if (findings.iframeLocked) {
          await note("The mechanism is behind a vault door (cross-origin iframe). Switching to containment.");
        } else if (findings.dismiss[0]) {
          await note(`Found the lock: "${findings.dismiss[0].label || "unlabeled close"}".`, rectOf(findings.dismiss[0].el));
        } else {
          await note("No legitimate lock on this one. Improvising.");
        }
        break;
      }
      case "visual": {
        await note("Sweeping the visible surface…", r);
        const closer = findings.dismiss.find((d) => d.kind === "close") || findings.dismiss[0];
        if (closer) {
          await note(`Target acquired: "${closer.label || "×"}" at the ${closer.el.getBoundingClientRect().top < r.top + r.height / 2 ? "top" : "bottom"}.`, rectOf(closer.el));
        } else {
          await note("No visible exit. It hides its weakness well.");
        }
        break;
      }
      case "listeners": {
        await note("Jacking in… tracing event listeners.", r);
        const primary = findings.dismiss[0]?.el || el;
        findings.listeners = await queryListeners(primary);
        const inline = el.querySelectorAll("[onclick]").length;
        if (findings.listeners && Object.keys(findings.listeners).length) {
          const kinds = Object.entries(findings.listeners)
            .map(([k, v]) => `${k}×${v}`).slice(0, 4).join(", ");
          await note(`Traced: ${kinds}${inline ? ` + ${inline} inline handler(s)` : ""}.`);
        } else {
          await note(inline
            ? `Probe quiet, but ${inline} inline handler(s) exposed in the markup.`
            : "Listeners are shy today. Falling back to protocol basics (Escape).");
        }
        break;
      }
      case "brute": {
        await note("Sizing up the opposition…", r);
        await note(`${findings.dismiss.length} clickable suspect(s) lined up. Accept buttons excluded from the fight card.`);
        break;
      }
      case "styles": {
        await note("Examining the specimen under the lens…", r);
        const cs = getComputedStyle(el);
        await note(`Composition: position ${cs.position}, z-index ${cs.zIndex}, ${findings.backdrops.length} backdrop layer(s).`);
        await note(findings.scrollLock
          ? "Scroll lock detected on the page body — it froze the page, so I'll freeze it back."
          : "No scroll lock. A clean freeze will do.");
        break;
      }
      default:
        await note("Investigating…", r);
    }

    steps.push({ t: Math.round(performance.now() - t0), act: "verdict", label: `plan: ${character.strategyKind}` });
    return { findings, steps };
  }

  B.investigate = { run, queryListeners };
})();
