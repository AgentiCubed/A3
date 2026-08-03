// Storage wrapper around chrome.storage.local. All reads/writes go through here
// so the schema stays in one place and can be migrated by key-prefix version.

import { KEYS, DEFAULT_SETTINGS } from './constants.js';

const area = () => chrome.storage.local;

async function get(key, fallback) {
  const out = await area().get(key);
  return out[key] ?? fallback;
}

async function set(key, value) {
  await area().set({ [key]: value });
}

// --- learned banners -------------------------------------------------------

export async function getLearned() {
  return get(KEYS.LEARNED, {});
}

export async function getLearnedForOrigin(origin) {
  const all = await getLearned();
  return Object.values(all).filter((l) => l.fingerprint.origin === origin);
}

export async function saveLearned(learned) {
  const all = await getLearned();
  all[learned.fingerprint.id] = learned;
  await set(KEYS.LEARNED, all);
}

export async function recordDismissal(fingerprintId) {
  const all = await getLearned();
  const entry = all[fingerprintId];
  if (!entry) return;
  entry.timesDismissed += 1;
  entry.lastSeenAt = Date.now();
  await set(KEYS.LEARNED, all);
}

// "Return this knowledge to the Great Banana Tree in the Sky."
export async function forgetLearned(fingerprintId) {
  const all = await getLearned();
  delete all[fingerprintId];
  await set(KEYS.LEARNED, all);
}

export async function forgetAll() {
  await set(KEYS.LEARNED, {});
}

// --- preferences -----------------------------------------------------------

const DEFAULT_PREFS = { typePrefs: {}, enabledOrigins: [] };

export async function getPrefs() {
  const prefs = await get(KEYS.PREFS, null);
  return prefs ?? structuredClone(DEFAULT_PREFS);
}

export async function getTypePref(category) {
  const prefs = await getPrefs();
  return prefs.typePrefs[category] ?? { keepShowing: false, promptShown: false };
}

export async function setTypePref(category, patch) {
  const prefs = await getPrefs();
  prefs.typePrefs[category] = { ...(await getTypePref(category)), ...patch };
  await set(KEYS.PREFS, prefs);
}

export async function isOriginEnabled(origin) {
  const prefs = await getPrefs();
  return prefs.enabledOrigins.includes(origin);
}

// A manual deploy on an origin IS the opt-in for automatic handling there.
export async function enableOrigin(origin) {
  const prefs = await getPrefs();
  if (!prefs.enabledOrigins.includes(origin)) {
    prefs.enabledOrigins.push(origin);
    await set(KEYS.PREFS, prefs);
  }
}

export async function disableOrigin(origin) {
  const prefs = await getPrefs();
  prefs.enabledOrigins = prefs.enabledOrigins.filter((o) => o !== origin);
  await set(KEYS.PREFS, prefs);
}

// --- settings --------------------------------------------------------------

export async function getSettings() {
  const s = await get(KEYS.SETTINGS, null);
  return { ...DEFAULT_SETTINGS, ...(s ?? {}) };
}

export async function setSettings(patch) {
  const s = await getSettings();
  await set(KEYS.SETTINGS, { ...s, ...patch });
}
