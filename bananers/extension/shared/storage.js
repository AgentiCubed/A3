/* Bananers storage layer over chrome.storage.local.
 *
 * Schema (v1) — all under top-level keys so content scripts can fetch only
 * what the pre-paint path needs in a single get():
 *
 *   meta          { schemaVersion }
 *   settings      { onboarded, defaultBananer, suggestBananer,
 *                   typeOverrides: { [type]: { show: bool } },
 *                   safety: { neverAccept: bool }, reducedMotion: 'auto'|'reduce' }
 *   microPrompt   { shownForType: { [type]: true } }        // one-time, forever
 *   fingerprints  { [fpId]: FingerprintRecord }
 *   hostIndex     { [host]: [fpId, ...] }
 *   eventLog      [ { ts, host, fpId, type, bananerId, action, outcome } ]
 *
 * Cross-context write safety: patch() only writes back the top-level keys a
 * mutation actually TOUCHED (its `keys` list), so a settings write from the
 * options page can never clobber a fingerprint write from a content script,
 * and vice-versa (chrome.storage.local.set merges at the top-key level). A
 * narrower residual race remains for two contexts editing the SAME key
 * concurrently (e.g. two tabs learning different banners in the same tick);
 * that is acceptable for v1 and documented in docs/DESIGN.md §4.2.
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.store) return;
  const C = B.constants;

  const DEFAULTS = () => ({
    meta: { schemaVersion: C.SCHEMA_VERSION },
    settings: {
      onboarded: false,
      defaultBananer: "peel-noir",
      suggestBananer: true,
      typeOverrides: {},
      safety: { neverAccept: true },
      reducedMotion: "auto",
    },
    microPrompt: { shownForType: {} },
    fingerprints: {},
    hostIndex: {},
    eventLog: [],
  });

  // Serialize read-modify-write cycles within this JS context.
  let chain = Promise.resolve();
  const withLock = (fn) => (chain = chain.then(fn, fn));

  const S = {
    DEFAULTS,

    async getAll() {
      const raw = await chrome.storage.local.get(null);
      const d = DEFAULTS();
      return {
        ...d,
        ...raw,
        settings: { ...d.settings, ...(raw.settings || {}), safety: { ...d.settings.safety, ...(raw.settings?.safety || {}) } },
        microPrompt: { shownForType: { ...(raw.microPrompt?.shownForType || {}) } },
      };
    },

    /* Fast path for document_start: one get(), only the keys suppression needs. */
    async getSuppressionContext(host) {
      const raw = await chrome.storage.local.get(["settings", "fingerprints", "hostIndex"]);
      const d = DEFAULTS();
      const settings = { ...d.settings, ...(raw.settings || {}) };
      const ids = raw.hostIndex?.[host] || [];
      const fps = ids.map((id) => raw.fingerprints?.[id]).filter(Boolean);
      return { settings, fingerprints: fps };
    },

    /* Read-modify-write, persisting ONLY the named top-level keys.
     * `keys` defaults to the settings-only case for the options page. */
    async patch(mutator, keys) {
      return withLock(async () => {
        const state = await S.getAll();
        const out = (await mutator(state)) || state;
        const persistKeys = keys && keys.length ? keys : Object.keys(out);
        const slice = {};
        for (const k of persistKeys) slice[k] = out[k];
        await chrome.storage.local.set(slice);
        return out;
      });
    },

    patchSettings: (fn) => S.patch((st) => { fn(st.settings, st); return st; }, ["settings"]),

    fpIdFor: (host, hash) => `${host}::${hash}`,

    async saveFingerprint(fp) {
      return S.patch((st) => {
        st.fingerprints[fp.id] = fp;
        const list = new Set(st.hostIndex[fp.host] || []);
        list.add(fp.id);
        st.hostIndex[fp.host] = [...list];
        return st;
      }, ["fingerprints", "hostIndex"]);
    },

    async touchFingerprint(id, apply) {
      return S.patch((st) => {
        const fp = st.fingerprints[id];
        if (fp) apply(fp);
        return st;
      }, ["fingerprints"]);
    },

    async forgetFingerprint(id) {
      return S.patch((st) => {
        const fp = st.fingerprints[id];
        delete st.fingerprints[id];
        if (fp && st.hostIndex[fp.host]) {
          st.hostIndex[fp.host] = st.hostIndex[fp.host].filter((x) => x !== id);
          if (!st.hostIndex[fp.host].length) delete st.hostIndex[fp.host];
        }
        return st;
      }, ["fingerprints", "hostIndex"]);
    },

    async log(evt) {
      return S.patch((st) => {
        st.eventLog.push({ ts: Date.now(), ...evt });
        if (st.eventLog.length > C.LOG_CAP) st.eventLog = st.eventLog.slice(-C.LOG_CAP);
        return st;
      }, ["eventLog"]);
    },

    /* One-time micro-prompt bookkeeping: returns true exactly once per type. */
    async shouldShowMicroPrompt(type) {
      let first = false;
      await S.patch((st) => {
        if (!st.microPrompt.shownForType[type]) {
          st.microPrompt.shownForType[type] = true;
          first = true;
        }
        return st;
      }, ["microPrompt"]);
      return first;
    },

    async setTypeOverride(type, show) {
      return S.patch((st) => {
        st.settings.typeOverrides[type] = { show: !!show };
        return st;
      }, ["settings"]);
    },

    async wipeMemory() {
      return S.patch((st) => {
        st.fingerprints = {};
        st.hostIndex = {};
        st.eventLog = [];
        return st;
      }, ["fingerprints", "hostIndex", "eventLog"]);
    },
  };

  B.store = S;
})();
