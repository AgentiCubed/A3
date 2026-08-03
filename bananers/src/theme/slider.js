// The ripeness slider: a real <input type="range"> (full keyboard/AT support)
// dressed as a banana lifecycle. The thumb is a small banana that ripens as
// it moves; the track is the live lifecycle gradient; positions near a named
// stage snap gently on release. aria-valuetext announces the stage name.

import { STAGES } from './tokens.js';
import { themeAt } from './interpolate.js';
import { applyTheme, persistRipeness } from './theme.js';

const SNAP_DISTANCE = 0.03;
const SCALE = 1000; // range input works in integers

function trackGradient() {
  const stops = STAGES.map((s) => `${s.tokens.bg} ${s.t * 100}%`);
  return `linear-gradient(90deg, ${stops.join(', ')})`;
}

function thumbSvg(t) {
  const theme = themeAt(t);
  const peel = theme.tokens.accent;
  const slump = t > 0.85 ? 'rotate(8 16 16)' : '';
  const speckles =
    t >= 0.55
      ? `<circle cx="13" cy="14" r="1.2" fill="#5c3a12"/><circle cx="18" cy="19" r="1.1" fill="#5c3a12"/><circle cx="15" cy="22" r="1" fill="#5c3a12"/>`
      : '';
  const bruise = t >= 0.75 ? `<ellipse cx="19" cy="13" rx="3" ry="2" fill="rgba(60,35,10,.55)"/>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><g transform="${slump}">
    <path d="M11 4 C6 12 6 22 12 27 C15 30 20 30 23 26 C18 25 13 19 13 12 C13 9 14 6 16 4 C14 2.5 12 2.5 11 4 Z"
          fill="${peel}" stroke="#3a2d14" stroke-width="1.2"/>${speckles}${bruise}</g></svg>`;
}

function nearestStageT(t) {
  let best = STAGES[0].t;
  for (const s of STAGES) if (Math.abs(s.t - t) < Math.abs(best - t)) best = s.t;
  return best;
}

export function createRipenessSlider(doc, initialT, { onChange } = {}) {
  const wrap = doc.createElement('div');
  wrap.className = 'bn-ripeness';
  wrap.innerHTML = `
    <input class="bn-ripeness-input" type="range" min="0" max="${SCALE}" step="1"
           aria-label="Banana ripeness — picks your theme" />
    <div class="bn-ripeness-ticks" role="presentation"></div>
  `;
  const input = wrap.querySelector('input');
  const ticks = wrap.querySelector('.bn-ripeness-ticks');
  input.style.setProperty('--bn-track', trackGradient());

  for (const s of STAGES) {
    const tick = doc.createElement('button');
    tick.type = 'button';
    tick.className = 'bn-ripeness-tick';
    tick.style.left = `${s.t * 100}%`;
    tick.textContent = s.name;
    tick.addEventListener('click', () => setValue(s.t, { persist: true }));
    ticks.appendChild(tick);
  }

  function updateVisuals(t) {
    const theme = applyTheme(doc, t);
    input.setAttribute('aria-valuetext', theme.stageName);
    const svg = encodeURIComponent(thumbSvg(t));
    input.style.setProperty('--bn-thumb', `url("data:image/svg+xml,${svg}")`);
    onChange?.(theme);
  }

  function setValue(t, { persist = false } = {}) {
    input.value = Math.round(t * SCALE);
    updateVisuals(t);
    if (persist) persistRipeness(t);
  }

  // Live ripening while dragging; gentle snap + persist on release.
  input.addEventListener('input', () => updateVisuals(input.value / SCALE));
  input.addEventListener('change', () => {
    let t = input.value / SCALE;
    const snap = nearestStageT(t);
    if (Math.abs(snap - t) <= SNAP_DISTANCE) t = snap;
    setValue(t, { persist: true });
  });

  setValue(initialT);
  return wrap;
}
