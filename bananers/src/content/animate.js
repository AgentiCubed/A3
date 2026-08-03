// In-page bananer animation layer. Renders inside a closed shadow root with a
// fixed high-contrast palette (never the extension theme — third-party pages
// are not themed, and the overlay must be legible anywhere). Sequences are
// keyed by the character's investigationStyle and closingTechnique. Skippable
// by click; prefers-reduced-motion collapses everything to instants.

const OVERLAY_Z = 2147483646;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function makeOverlay() {
  const host = document.createElement('div');
  host.style.cssText = `position:fixed;inset:0;z-index:${OVERLAY_Z};pointer-events:none;`;
  const shadow = host.attachShadow({ mode: 'closed' });
  const style = document.createElement('style');
  style.textContent = `
    :host { all: initial; }
    .stage { position: fixed; inset: 0; font-family: system-ui, sans-serif; }
    .bananer { position: absolute; width: 72px; height: 108px; transition: transform .5s ease, left .6s ease, top .6s ease; will-change: transform; }
    .bananer svg { width: 100%; height: 100%; filter: drop-shadow(0 4px 6px rgba(0,0,0,.35)); }
    .quip { position: absolute; max-width: 240px; background: #1c1917; color: #fef3c7;
            border: 2px solid #fbbf24; border-radius: 10px; padding: 8px 12px; font-size: 13px;
            line-height: 1.35; box-shadow: 0 6px 18px rgba(0,0,0,.4); }
    .fx { position: absolute; pointer-events: none; }
    @keyframes bn-sweep { 0%{transform:translateX(-30px) rotate(-12deg)} 50%{transform:translateX(30px) rotate(12deg)} 100%{transform:translateX(-30px) rotate(-12deg)} }
    @keyframes bn-glyphs { 0%{opacity:0} 20%{opacity:1} 100%{opacity:0; transform:translateY(26px)} }
    @keyframes bn-scan { 0%{opacity:.0} 30%{opacity:.85} 100%{opacity:0} }
    @keyframes bn-bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-14px)} }
    @keyframes bn-slash { 0%{transform:scaleX(0) rotate(-24deg); opacity:1} 60%{transform:scaleX(1) rotate(-24deg); opacity:1} 100%{opacity:0} }
    @keyframes bn-flicker { 0%,100%{opacity:1} 25%{opacity:.2} 50%{opacity:.9} 75%{opacity:.3} }
    @keyframes bn-pow { 0%{transform:scale(.2); opacity:0} 40%{transform:scale(1.25); opacity:1} 100%{transform:scale(1); opacity:0} }
    @keyframes bn-wiggle { 0%,100%{transform:rotate(0)} 25%{transform:rotate(9deg)} 75%{transform:rotate(-9deg)} }
    .investigate-dom-detective { animation: bn-sweep 1.1s ease-in-out 2; }
    .investigate-visual-hunter  { animation: bn-wiggle .5s ease-in-out 3; }
    .investigate-listener-tracer{ animation: bn-flicker .9s linear 2; }
    .investigate-brute-force    { animation: bn-bounce .55s ease-in-out 3; }
    .glyphrain span { position:absolute; color:#4ade80; font: 12px monospace; animation: bn-glyphs 1.4s ease-out forwards; }
    .scanline { position:absolute; height:3px; background:#f87171; box-shadow:0 0 10px #f87171; animation: bn-scan 1.2s ease-in-out 2; }
    .slash { height:4px; background:linear-gradient(90deg,transparent,#fef3c7,#f59e0b,transparent); transform-origin:left center; animation: bn-slash .7s ease-out forwards; }
    .pow { color:#fbbf24; font-weight:800; font-size:30px; text-shadow:0 2px 0 #78350f; animation: bn-pow .8s ease-out forwards; }
  `;
  const stage = document.createElement('div');
  stage.className = 'stage';
  shadow.append(style, stage);
  document.documentElement.appendChild(host);
  return { host, stage };
}

function place(el, x, y) {
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function quip(stage, text, x, y) {
  const q = document.createElement('div');
  q.className = 'quip';
  q.textContent = text;
  place(q, x, y);
  stage.appendChild(q);
  return q;
}

function investigationFx(stage, style, rect) {
  if (style === 'listener-tracer') {
    const rain = document.createElement('div');
    rain.className = 'fx glyphrain';
    place(rain, rect.left + 10, rect.top + 10);
    rain.style.width = `${Math.max(60, rect.width - 20)}px`;
    for (let i = 0; i < 14; i++) {
      const s = document.createElement('span');
      s.textContent = ['{}', '()', '=>', '0x', 'fn', '::'][i % 6];
      s.style.left = `${(i * 37) % Math.max(40, rect.width - 40)}px`;
      s.style.animationDelay = `${(i % 5) * 120}ms`;
      rain.appendChild(s);
    }
    stage.appendChild(rain);
  } else if (style === 'visual-hunter') {
    const line = document.createElement('div');
    line.className = 'fx scanline';
    place(line, rect.left, rect.top + rect.height / 2);
    line.style.width = `${rect.width}px`;
    stage.appendChild(line);
  }
}

function closingFx(stage, technique, targetRect) {
  const cx = targetRect.left + targetRect.width / 2;
  const cy = targetRect.top + targetRect.height / 2;
  if (technique === 'slice') {
    const s = document.createElement('div');
    s.className = 'fx slash';
    place(s, cx - 70, cy);
    s.style.width = '140px';
    stage.appendChild(s);
  } else if (technique === 'smash') {
    const p = document.createElement('div');
    p.className = 'fx pow';
    p.textContent = 'SPLAT!';
    place(p, cx - 40, cy - 20);
    stage.appendChild(p);
  } else if (technique === 'hack') {
    const p = document.createElement('div');
    p.className = 'fx pow';
    p.textContent = '</popup>';
    p.style.color = '#4ade80';
    stage.appendChild(p);
    place(p, cx - 46, cy - 16);
  } else {
    // lockpick: a subtle wiggle marker at the close affordance
    const p = document.createElement('div');
    p.className = 'fx pow';
    p.textContent = '🔓';
    place(p, cx - 14, cy - 16);
    stage.appendChild(p);
  }
}

// The full in-character show: enter → quip → investigate → strike. Resolves
// when the dismissal should actually execute. Skippable via click.
export async function playSequence(bananer, bannerEl, closeTargetEl) {
  if (reducedMotion()) return; // instant dismissal, same outcome

  const { host, stage } = makeOverlay();
  host.style.pointerEvents = 'auto';
  let skipped = false;
  const skip = () => { skipped = true; };
  host.addEventListener('click', skip, { once: true });

  try {
    const rect = bannerEl.getBoundingClientRect();
    const actor = document.createElement('div');
    actor.className = 'bananer';
    actor.innerHTML = bananer.svg;
    place(actor, -80, Math.min(window.innerHeight - 130, rect.bottom + 8));
    stage.appendChild(actor);
    await wait(30);
    place(actor, Math.max(8, rect.left - 60), Math.min(window.innerHeight - 130, rect.bottom - 60));

    const q = quip(stage, bananer.voice.deploy, Math.max(8, rect.left - 40), Math.max(8, rect.top - 30));
    if (!skipped) await wait(900);
    q.remove();

    actor.classList.add(`investigate-${bananer.investigationStyle}`);
    investigationFx(stage, bananer.investigationStyle, rect);
    if (!skipped) await wait(1600);
    actor.classList.remove(`investigate-${bananer.investigationStyle}`);

    const targetRect = (closeTargetEl ?? bannerEl).getBoundingClientRect();
    closingFx(stage, bananer.closingTechnique, targetRect);
    if (!skipped) await wait(700);
  } finally {
    host.remove();
  }
}

// Small in-page toast in the bananer's voice (success, gentle failure).
export function showToast(bananer, text) {
  const { host, stage } = makeOverlay();
  const q = quip(stage, `${bananer.name}: ${text}`, 16, window.innerHeight - 90);
  q.style.pointerEvents = 'auto';
  setTimeout(() => host.remove(), 4200);
}

// One-time keep-showing micro-prompt. Resolves true (keep) / false (vanish).
// Dismissing it (clicking away) counts as "vanish" — the default behavior.
export function showMicroPrompt({ title, body, yes, no }) {
  return new Promise((resolve) => {
    const { host, stage } = makeOverlay();
    host.style.pointerEvents = 'auto';
    const card = document.createElement('div');
    card.className = 'quip';
    card.style.maxWidth = '300px';
    card.innerHTML = `
      <strong style="display:block;margin-bottom:4px">${title}</strong>
      <span>${body}</span>
      <div style="margin-top:10px;display:flex;gap:8px">
        <button data-a="yes" style="cursor:pointer;background:#fbbf24;color:#1c1917;border:0;border-radius:6px;padding:6px 10px;font-weight:600">${yes}</button>
        <button data-a="no" style="cursor:pointer;background:transparent;color:#fef3c7;border:1px solid #fbbf24;border-radius:6px;padding:6px 10px">${no}</button>
      </div>`;
    place(card, 16, window.innerHeight - 190);
    stage.appendChild(card);
    const done = (v) => { host.remove(); resolve(v); };
    card.querySelector('[data-a="yes"]').addEventListener('click', () => done(true));
    card.querySelector('[data-a="no"]').addEventListener('click', () => done(false));
    setTimeout(() => done(false), 20000);
  });
}
