// The Learn dashboard: roster gallery, ripeness slider, per-type "keep the
// show" toggles, and the memory browser (with gentle send-offs for forgetting).

import { ROSTER } from '../shared/roster.js';
import { VOICE } from '../shared/voice.js';
import { CATEGORIES, CATEGORY_LABELS } from '../shared/constants.js';
import * as store from '../shared/store.js';
import { initTheme, defaultRipeness } from '../theme/theme.js';
import { createRipenessSlider } from '../theme/slider.js';

const $ = (id) => document.getElementById(id);

// --- confirm dialog (gentle send-off, per lore) -----------------------------

function confirmDialog({ title, body, ok, cancel }) {
  return new Promise((resolve) => {
    const dlg = $('confirm');
    $('confirm-title').textContent = title;
    $('confirm-body').textContent = body;
    $('confirm-ok').textContent = ok;
    $('confirm-cancel').textContent = cancel;
    const done = (v) => { dlg.close(); resolve(v); };
    $('confirm-ok').onclick = () => done(true);
    $('confirm-cancel').onclick = () => done(false);
    dlg.oncancel = () => resolve(false);
    dlg.showModal();
  });
}

// --- sections ---------------------------------------------------------------

async function renderRoster() {
  const settings = await store.getSettings();
  const grid = $('roster');
  grid.innerHTML = '';
  for (const b of ROSTER) {
    const card = document.createElement('div');
    card.className = 'bn-card char-card';
    card.dataset.active = String(b.id === settings.activeBananer);
    card.innerHTML = `
      ${b.svg}
      <h3>${b.name}</h3>
      <div class="bn-muted outfit">${b.outfit}</div>
      <div class="bn-muted outfit">${b.investigationStyle} · ${b.closingTechnique}</div>
      <p class="bio">${b.voice.bio}</p>
      <button class="bn-btn secondary" data-pick="${b.id}">Walk with ${b.name.split(' ')[0]}</button>
    `;
    card.querySelector('[data-pick]').addEventListener('click', async () => {
      await store.setSettings({ activeBananer: b.id });
      renderRoster();
    });
    grid.appendChild(card);
  }
}

async function renderRipeness() {
  const settings = await store.getSettings();
  const t = settings.ripeness ?? defaultRipeness(window);
  const holder = $('ripeness-holder');
  holder.innerHTML = '';
  holder.appendChild(createRipenessSlider(document, t));
}

async function renderTypePrefs() {
  const holder = $('type-prefs');
  holder.innerHTML = '';
  for (const category of Object.values(CATEGORIES)) {
    const pref = await store.getTypePref(category);
    const row = document.createElement('div');
    row.className = 'pref-row';
    const inputId = `pref-${category}`;
    row.innerHTML = `
      <div>
        <strong>${CATEGORY_LABELS[category]}</strong>
        <div class="bn-muted" style="font-size:12px">
          ${pref.keepShowing ? 'Stays visible — your bananer handles it live.' : 'Vanishes before you see it.'}
        </div>
      </div>
      <label class="bn-toggle" for="${inputId}">
        <input type="checkbox" id="${inputId}" ${pref.keepShowing ? 'checked' : ''} />
        Keep the show
      </label>
    `;
    row.querySelector('input').addEventListener('change', async (e) => {
      await store.setTypePref(category, { keepShowing: e.target.checked });
      renderTypePrefs();
    });
    holder.appendChild(row);
  }
}

async function renderMemory() {
  const learned = await store.getLearned();
  const holder = $('memory');
  holder.innerHTML = '';
  const entries = Object.values(learned).sort((a, b) => b.lastSeenAt - a.lastSeenAt);

  if (entries.length === 0) {
    holder.innerHTML = `<div class="bn-card"><p class="bn-muted">${VOICE.dashboard.emptyMemory}</p></div>`;
    return;
  }

  for (const entry of entries) {
    const card = document.createElement('div');
    card.className = 'bn-card';
    const learnedBy = ROSTER.find((b) => b.id === entry.learnedBy);
    card.innerHTML = `
      <div class="mem-head">
        <div>
          <strong>${new URL(entry.fingerprint.origin).host}</strong>
          <span class="bn-muted"> · ${CATEGORY_LABELS[entry.fingerprint.category] ?? entry.fingerprint.category}</span>
        </div>
        <button class="bn-btn secondary" data-forget>${VOICE.destructive.forgetConfirm}</button>
      </div>
      <dl class="mem-detail bn-muted">
        <dt>Learned by</dt><dd>${learnedBy?.name ?? entry.learnedBy} — dismissed ${entry.timesDismissed}×</dd>
        <dt>Structure</dt><dd>${entry.investigation.domSummary}</dd>
        <dt>Presentation</dt><dd>${entry.investigation.cssSummary}</dd>
        <dt>Wiring</dt><dd>${entry.investigation.listenerHints.join(' · ')}</dd>
        <dt>How it closes</dt><dd>${entry.plan.steps.map((s) => `${s.kind} (${s.how})`).join(', ')}</dd>
      </dl>
    `;
    card.querySelector('[data-forget]').addEventListener('click', async () => {
      const yes = await confirmDialog({
        title: VOICE.destructive.forgetTitle,
        body: VOICE.destructive.forgetBody,
        ok: VOICE.destructive.forgetConfirm,
        cancel: VOICE.destructive.forgetCancel,
      });
      if (yes) {
        await store.forgetLearned(entry.fingerprint.id);
        renderMemory();
      }
    });
    holder.appendChild(card);
  }
}

async function main() {
  await initTheme(document, window);
  $('title').textContent = VOICE.dashboard.title;
  $('permission-note').textContent = VOICE.onboarding.permissionNote;
  $('roster-intro').textContent = VOICE.dashboard.rosterIntro;
  $('ripeness-intro').textContent = VOICE.dashboard.ripenessIntro;
  $('prefs-intro').textContent = VOICE.dashboard.prefsIntro;
  $('memory-intro').textContent = VOICE.dashboard.memoryIntro;
  $('reset-all').textContent = VOICE.destructive.resetTitle;

  $('reset-all').addEventListener('click', async () => {
    const yes = await confirmDialog({
      title: VOICE.destructive.resetTitle,
      body: VOICE.destructive.resetBody,
      ok: VOICE.destructive.resetConfirm,
      cancel: VOICE.destructive.resetCancel,
    });
    if (yes) {
      await store.forgetAll();
      renderMemory();
    }
  });

  await Promise.all([renderRoster(), renderRipeness(), renderTypePrefs(), renderMemory()]);
}

main();
