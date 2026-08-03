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
 * FingerprintRecord:
 *   { id, host, origin, type, signature: { hash, tokens[] , selector },
 *     strategy: { kind, clickSelector?, killSelectors[], notes? },
 *     bananerId, createdAt, lastSeenAt, timesDismissed, timesFailed,
 *     replay: [ { t, act, label } ] }
 *
 * Cross-device sync via chrome.storage.sync is a stretch goal (quota: 100KB
 * total / 8KB per item) — see docs/DESIGN.md §9.
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

  // Serialize read-modify-write cycles within this JS context. Cross-context
  // races (SW vs content script) are tolerated for v1: writers own disjoint
  // keys in practice (content: fingerprints/log; pages: settings).
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

    async patch(mutator) {
      return withLock(async () => {
        const state = await S.getAll();
        const out = (await mutator(state)) || state;
        await chrome.storage.local.set(out);
        return out;
      });
    },

    fpIdFor: (host, hash) => `${host}::${hash}`,

    async saveFingerprint(fp) {
      return S.patch((st) => {
        st.fingerprints[fp.id] = fp;
        const list = new Set(st.hostIndex[fp.host] || []);
        list.add(fp.id);
        st.hostIndex[fp.host] = [...list];
        return st;
      });
    },

    async touchFingerprint(id, apply) {
      return S.patch((st) => {
        const fp = st.fingerprints[id];
        if (fp) apply(fp);
        return st;
      });
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
      });
    },

    async log(evt) {
      return S.patch((st) => {
        st.eventLog.push({ ts: Date.now(), ...evt });
        if (st.eventLog.length > C.LOG_CAP) st.eventLog = st.eventLog.slice(-C.LOG_CAP);
        return st;
      });
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
      });
      return first;
    },

    async setTypeOverride(type, show) {
      return S.patch((st) => {
        st.settings.typeOverrides[type] = { show: !!show };
        return st;
      });
    },

    async wipeMemory() {
      return S.patch((st) => {
        st.fingerprints = {};
        st.hostIndex = {};
        st.eventLog = [];
        return st;
      });
    },
  };

  B.store = S;
})();
