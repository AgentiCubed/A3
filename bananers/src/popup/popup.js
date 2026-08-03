// Toolbar popup: pick a bananer, deploy onto the active tab, see quick stats.

import { ROSTER, getBananer } from '../shared/roster.js';
import { VOICE, fill } from '../shared/voice.js';
import * as store from '../shared/store.js';
import { initTheme } from '../theme/theme.js';

const $ = (id) => document.getElementById(id);

async function render() {
  await initTheme(document, window);
  const settings = await store.getSettings();
  const learned = await store.getLearned();
  let selected = settings.activeBananer;

  $('greeting').textContent = VOICE.onboarding.greeting;
  $('stats').textContent = fill(VOICE.popup.statsLine, { count: Object.keys(learned).length });
  $('choose-label').textContent = VOICE.popup.chooseBananer;

  const rosterEl = $('roster');
  rosterEl.innerHTML = '';
  for (const b of ROSTER) {
    const btn = document.createElement('button');
    btn.className = 'roster-pick';
    btn.setAttribute('aria-pressed', String(b.id === selected));
    btn.title = b.outfit;
    btn.innerHTML = `${b.svg}<span class="nm">${b.name}</span>`;
    btn.addEventListener('click', async () => {
      selected = b.id;
      await store.setSettings({ activeBananer: b.id });
      rosterEl.querySelectorAll('.roster-pick').forEach((el) => el.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
      updateDeployLabel();
    });
    rosterEl.appendChild(btn);
  }

  function updateDeployLabel() {
    $('deploy').textContent = fill(VOICE.popup.deployCta, { name: getBananer(selected).name });
  }
  updateDeployLabel();

  $('deploy').addEventListener('click', async () => {
    $('status').textContent = getBananer(selected).voice.deploy;
    const result = await chrome.runtime.sendMessage({
      type: 'bananers:deploy-active-tab',
      bananerId: selected,
    });
    if (result?.ok) {
      $('status').textContent = getBananer(selected).voice.success;
    } else if (result?.reason === 'no-banner') {
      $('status').textContent = VOICE.popup.noBanners;
    } else {
      $('status').textContent = VOICE.errors.dismissFailed;
    }
  });

  $('open-dashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
}

render();
