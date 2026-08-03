// MV3 service worker: message routing between UI surfaces and tabs, plus a
// badge that counts banners learned. Deliberately thin — all logic lives in
// shared/core modules.

import * as store from '../shared/store.js';

async function refreshBadge() {
  const learned = await store.getLearned();
  const count = Object.keys(learned).length;
  await chrome.action.setBadgeText({ text: count > 0 ? String(count) : '' });
  await chrome.action.setBadgeBackgroundColor({ color: '#f5d94b' });
}

chrome.runtime.onInstalled.addListener(() => {
  refreshBadge();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes['bananers/v1/learned']) refreshBadge();
});

// Popup → active tab relay (popup can't always message content scripts on
// its own if the tab query happens after the popup closes).
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === 'bananers:deploy-active-tab') {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) return sendResponse({ ok: false, error: 'no active tab' });
      try {
        const result = await chrome.tabs.sendMessage(tab.id, {
          type: 'bananers:deploy',
          bananerId: msg.bananerId,
        });
        sendResponse(result ?? { ok: false, error: 'no response from page' });
      } catch (err) {
        sendResponse({ ok: false, error: 'content script unavailable on this page' });
      }
    })();
    return true;
  }
  return false;
});
