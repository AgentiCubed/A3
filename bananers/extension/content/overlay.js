/* Bananers on-page overlay: the visible character layer.
 * One fixed, max-z container with an OPEN shadow root (open for testability;
 * everything is namespaced and pointer-events:none except interactive cards).
 * Honors prefers-reduced-motion and the user's reducedMotion setting: with
 * motion reduced the whole performance collapses to brief captions.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.overlay) return;

  let host = null;
  let shadow = null;
  let reduced = null; // resolved lazily

  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function motionReduced() {
    if (reduced !== null) return reduced;
    try { reduced = matchMedia("(prefers-reduced-motion: reduce)").matches; }
    catch { reduced = false; }
    return reduced;
  }

  const CSS_TEXT = `
    :host { all: initial; }
    * { box-sizing: border-box; }
    .stage { position: fixed; inset: 0; pointer-events: none; z-index: 2147483647;
             font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
    .bananer { position: fixed; width: 92px; height: 92px; left: 20px; bottom: -110px;
               transition: transform .55s cubic-bezier(.34,1.56,.64,1), left .55s ease,
                           top .55s ease, bottom .55s ease, opacity .3s ease; }
    .bananer svg { width: 100%; height: 100%; filter: drop-shadow(0 4px 10px rgba(0,0,0,.35)); }
    .bananer.in { bottom: 18px; }
    .bananer.working { animation: bnr-bob 1.1s ease-in-out infinite; }
    .bananer.lunge { animation: bnr-lunge .5s ease-out 1; }
    .bubble { position: fixed; max-width: 260px; background: #1f2430; color: #f4f1e8;
              border: 2px solid var(--accent, #c9a227); border-radius: 12px 12px 12px 2px;
              padding: 8px 12px; font-size: 13px; line-height: 1.35; left: 118px; bottom: 40px;
              box-shadow: 0 6px 24px rgba(0,0,0,.35); transition: opacity .25s ease; }
    .scanbox { position: fixed; border: 2px solid var(--accent, #c9a227); border-radius: 8px;
               background: color-mix(in srgb, var(--accent, #c9a227) 12%, transparent);
               animation: bnr-pulse .9s ease-in-out infinite; }
    .lens { position: fixed; width: 70px; height: 70px; border: 3px solid var(--accent);
            border-radius: 50%; box-shadow: 0 0 0 2000px rgba(0,0,0,.12);
            animation: bnr-sweep 1.4s ease-in-out infinite alternate; }
    .coderain { position: fixed; overflow: hidden; border-radius: 8px;
                background: rgba(8,14,10,.55); color: #31c48d;
                font: 10px/1.2 monospace; white-space: pre; padding: 4px;
                text-shadow: 0 0 6px #31c48d; }
    .frost { position: fixed; border-radius: 8px;
             background: linear-gradient(135deg, rgba(190,229,247,.55), rgba(255,255,255,.25));
             backdrop-filter: blur(1px); animation: bnr-frost .8s ease-out forwards; }
    .slash { position: fixed; height: 3px; background: linear-gradient(90deg, transparent, #fff, #cbd5f5, transparent);
             transform-origin: left center; animation: bnr-slash .35s ease-in forwards; }
    .impact { position: fixed; font-size: 42px; animation: bnr-pop .5s ease-out forwards; }
    .card { position: fixed; right: 18px; bottom: 18px; width: 320px; pointer-events: auto;
            background: #1f2430; color: #f4f1e8; border-radius: 14px; padding: 14px;
            border: 2px solid #c9a227; box-shadow: 0 10px 34px rgba(0,0,0,.45); font-size: 13px; }
    .card .row { display: flex; gap: 10px; align-items: center; }
    .card .mini { width: 46px; height: 46px; flex: 0 0 auto; }
    .card .btns { display: flex; gap: 8px; margin-top: 12px; justify-content: flex-end; }
    .card button { pointer-events: auto; border: 0; border-radius: 8px; padding: 7px 11px;
                   font-size: 12.5px; cursor: pointer; background: #3a4152; color: #f4f1e8; }
    .card button.primary { background: #c9a227; color: #221c05; font-weight: 600; }
    .card .x { position: absolute; top: 6px; right: 10px; background: none; font-size: 15px;
               color: #8b92a5; padding: 2px 6px; }
    @keyframes bnr-bob { 0%,100% { transform: translateY(0) rotate(-2deg); }
                         50% { transform: translateY(-7px) rotate(3deg); } }
    @keyframes bnr-pulse { 0%,100% { opacity: .9; } 50% { opacity: .4; } }
    @keyframes bnr-sweep { from { transform: translate(0,0); } to { transform: translate(26px,14px); } }
    @keyframes bnr-frost { from { opacity: 0; } to { opacity: 1; } }
    @keyframes bnr-slash { from { transform: scaleX(0) rotate(var(--ang, -18deg)); }
                           to { transform: scaleX(1) rotate(var(--ang, -18deg)); } }
    @keyframes bnr-pop { 0% { transform: scale(.3); opacity: 0; } 40% { transform: scale(1.25); opacity: 1; }
                         100% { transform: scale(1); opacity: 0; } }
    @keyframes bnr-lunge { 0% { transform: translateX(0); } 45% { transform: translateX(34px) rotate(8deg); }
                           100% { transform: translateX(0); } }
    @media (prefers-reduced-motion: reduce) {
      .bananer, .bubble, .scanbox, .lens, .coderain, .frost, .slash, .impact { animation: none !important; transition: none !important; }
    }
  `;

  function ensure() {
    if (host && host.isConnected) return shadow;
    host = document.createElement("div");
    host.setAttribute("data-bananers-ui", "");
    shadow = host.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = CSS_TEXT;
    const stage = document.createElement("div");
    stage.className = "stage";
    shadow.append(style, stage);
    (document.body || document.documentElement).appendChild(host);
    return shadow;
  }

  const stage = () => ensure().querySelector(".stage");

  function place(node, rect, pad = 8) {
    if (!rect) return;
    node.style.left = `${Math.max(0, rect.left - pad)}px`;
    node.style.top = `${Math.max(0, rect.top - pad)}px`;
    node.style.width = `${rect.width + pad * 2}px`;
    node.style.height = `${rect.height + pad * 2}px`;
  }

  function effectFor(style, rect, accent) {
    const s = stage();
    let node;
    if (style === "visual") {
      node = document.createElement("div");
      node.className = "lens";
      node.style.setProperty("--accent", accent);
      node.style.left = `${rect.left + 12}px`;
      node.style.top = `${rect.top + 12}px`;
    } else if (style === "listeners") {
      node = document.createElement("div");
      node.className = "coderain";
      place(node, rect, 0);
      node.textContent = Array.from({ length: 8 }, (_, i) =>
        `> addEventListener("click") ${i % 2 ? "✓ traced" : "…"}`.padEnd(36)
      ).join("\n");
    } else if (style === "styles") {
      node = document.createElement("div");
      node.className = "frost";
      place(node, rect, 0);
    } else {
      node = document.createElement("div");
      node.className = "scanbox";
      node.style.setProperty("--accent", accent);
      place(node, rect);
    }
    s.appendChild(node);
    return node;
  }

  /* Controller for one deployment performance. */
  function begin(character, { reducedMotion = false } = {}) {
    const noMotion = reducedMotion || motionReduced();
    const sh = ensure();
    const s = stage();
    s.querySelectorAll(".bananer,.bubble,.scanbox,.lens,.coderain,.frost,.slash,.impact").forEach((n) => n.remove());

    const sprite = document.createElement("div");
    sprite.className = "bananer";
    sprite.innerHTML = B.characters.spriteFor(character.id);
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.style.setProperty("--accent", character.accent);
    bubble.textContent = `${character.name} on the case.`;
    s.append(sprite, bubble);

    let effects = [];
    const say = (text) => { bubble.textContent = text; };

    if (!noMotion) requestAnimationFrame(() => sprite.classList.add("in", "working"));
    else sprite.classList.add("in");

    return {
      character,
      noMotion,
      say,
      async step(label, rect) {
        say(label);
        if (noMotion) return wait(60);
        if (rect) {
          const fx = effectFor(character.investigation, rect, character.accent);
          effects.push(fx);
          setTimeout(() => fx.remove(), 1600);
        }
        return wait(rect ? 750 : 450);
      },
      async finish(ok, targetRect) {
        effects.forEach((n) => n.remove());
        effects = [];
        if (ok && !noMotion && targetRect) {
          if (character.technique === "slice") {
            const slash = document.createElement("div");
            slash.className = "slash";
            slash.style.left = `${targetRect.left}px`;
            slash.style.top = `${targetRect.top + targetRect.height / 2}px`;
            slash.style.width = `${targetRect.width}px`;
            stage().appendChild(slash);
            setTimeout(() => slash.remove(), 600);
          } else if (character.technique === "deep-freeze") {
            const fr = document.createElement("div");
            fr.className = "frost";
            place(fr, targetRect, 0);
            stage().appendChild(fr);
            setTimeout(() => fr.remove(), 900);
          } else if (character.technique === "haymaker") {
            sprite.classList.add("lunge");
            const imp = document.createElement("div");
            imp.className = "impact";
            imp.textContent = "💥";
            imp.style.left = `${targetRect.left + targetRect.width / 2 - 21}px`;
            imp.style.top = `${targetRect.top + targetRect.height / 2 - 21}px`;
            stage().appendChild(imp);
            setTimeout(() => imp.remove(), 700);
          } else {
            const imp = document.createElement("div");
            imp.className = "impact";
            imp.textContent = character.technique === "protocol" ? "⌁" : "🔓";
            imp.style.left = `${targetRect.left + Math.min(targetRect.width - 40, targetRect.width * 0.8)}px`;
            imp.style.top = `${targetRect.top + 8}px`;
            stage().appendChild(imp);
            setTimeout(() => imp.remove(), 700);
          }
          await wait(500);
        }
        say(ok ? "Gone. 🍌" : "This one fought back — contained it instead.");
        sprite.classList.remove("working");
        await wait(noMotion ? 300 : 1100);
        sprite.classList.remove("in");
        bubble.style.opacity = "0";
        await wait(noMotion ? 50 : 500);
        sprite.remove();
        bubble.remove();
      },
    };
  }

  /* Interactive card in the same shadow root (used by the micro-prompt). */
  function card(html) {
    const sh = ensure();
    const s = stage();
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = html;
    s.appendChild(el);
    return el;
  }

  B.overlay = { ensure, begin, card, motionReduced };
})();
