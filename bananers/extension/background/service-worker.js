/* Bananers service worker.
 * Owns everything that needs SW-only APIs: dynamic content-script
 * registration for opted-in origins, permission lifecycle, badge state,
 * and the onboarding page. Learning data itself is written by content
 * scripts straight into chrome.storage.local (see shared/storage.js).
 *
 * MV3 note: the service worker can be terminated at any time, so per-tab
 * report state lives in chrome.storage.session (not an in-memory Map) and
 * registration is single-flight to avoid duplicate-ID races.
 */
importScripts(
  "/shared/constants.js",
  "/shared/characters.js",
  "/shared/storage.js",
  "/shared/policy.js"
);

const { MSG } = Bananers.constants;

/* Files injected into opted-in pages, in dependency order. */
const CONTENT_FILES = [
  "shared/constants.js",
  "shared/characters.js",
  "shared/storage.js",
  "shared/policy.js",
  "content/fingerprint.js",
  "content/detect.js",
  "content/overlay.js",
  "content/investigate.js",
  "content/dismiss.js",
  "content/microprompt.js",
  "content/suppress.js",
  "content/main.js",
];
const PROBE_FILE = "content/main-world-probe.js";

/* ---------- per-tab report state (survives SW restart) ---------- */

const reportKey = (tabId) => `report:${tabId}`;
async function getReport(tabId) {
  const raw = await chrome.storage.session.get(reportKey(tabId));
  return raw[reportKey(tabId)] || null;
}
async function setReport(tabId, val) {
  await chrome.storage.session.set({ [reportKey(tabId)]: val });
}
async function clearReport(tabId) {
  await chrome.storage.session.remove(reportKey(tabId));
}

function setBadge(tabId, count) {
  const text = count > 0 ? String(count) : "";
  chrome.action.setBadgeText({ tabId, text }).catch(() => {});
  chrome.action.setBadgeBackgroundColor({ tabId, color: "#e0563f" }).catch(() => {});
}

/* ---------- dynamic registration for opted-in origins (single-flight) ---------- */

async function grantedOriginPatterns() {
  const { origins = [] } = await chrome.permissions.getAll();
  return origins.filter((o) => /^https?:\/\//.test(o) || o === "<all_urls>");
}

async function doSync() {
  const existing = await chrome.scripting.getRegisteredContentScripts({
    ids: ["bananers-core", "bananers-probe"],
  }).catch(() => []);
  if (existing.length) {
    await chrome.scripting.unregisterContentScripts({
      ids: existing.map((s) => s.id),
    }).catch(() => {});
  }
  const origins = await grantedOriginPatterns();
  if (!origins.length) return;

  await chrome.scripting.registerContentScripts([
    {
      id: "bananers-core",
      js: CONTENT_FILES,
      matches: origins,
      runAt: "document_start",
      world: "ISOLATED",
      persistAcrossSessions: true,
    },
    {
      id: "bananers-probe",
      js: [PROBE_FILE],
      matches: origins,
      runAt: "document_start",
      world: "MAIN",
      persistAcrossSessions: true,
    },
  ]).catch((err) => console.warn("[bananers] register failed:", err?.message));
}

// Serialize all registration mutations so concurrent callers
// (permissions.onAdded + GRANT_AND_DEPLOY) never race to register the same IDs.
let syncChain = Promise.resolve();
function syncRegisteredScripts() {
  syncChain = syncChain.then(doSync, doSync);
  return syncChain;
}

chrome.permissions.onAdded.addListener(() => syncRegisteredScripts());
chrome.permissions.onRemoved.addListener(() => syncRegisteredScripts());

/* ---------- lifecycle ---------- */

chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  await syncRegisteredScripts();
  if (reason === "install") {
    const { settings } = await Bananers.store.getAll();
    if (!settings.onboarded) {
      chrome.tabs.create({
        url: chrome.runtime.getURL("options/options.html#onboarding"),
      });
    }
  }
});

chrome.runtime.onStartup?.addListener(() => syncRegisteredScripts());

chrome.tabs.onRemoved.addListener((tabId) => clearReport(tabId));

// A top-level navigation invalidates the previous page's report/badge; if the
// destination has no grant, no content script runs to replace it.
chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status === "loading" && info.url) {
    clearReport(tabId);
    setBadge(tabId, 0);
  }
});

/* ---------- helpers ---------- */

function originPatternFor(url) {
  try {
    const u = new URL(url);
    if (!/^https?:$/.test(u.protocol)) return null;
    return `${u.protocol}//${u.hostname}/*`;
  } catch {
    return null;
  }
}

async function injectNow(tabId) {
  await chrome.scripting.executeScript({
    target: { tabId },
    files: CONTENT_FILES,
    world: "ISOLATED",
    injectImmediately: true,
  });
  await chrome.scripting.executeScript({
    target: { tabId },
    files: [PROBE_FILE],
    world: "MAIN",
    injectImmediately: true,
  }).catch(() => {}); // probe is best-effort (some pages block MAIN-world early)
}

/* ---------- message router ---------- */

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    switch (msg?.type) {
      case MSG.PAGE_REPORT: {
        const tabId = sender.tab?.id;
        if (tabId != null) {
          await setReport(tabId, { spotted: msg.spotted, types: msg.types });
          setBadge(tabId, msg.spotted);
        }
        return { ok: true };
      }

      case MSG.DISMISSED: {
        const tabId = sender.tab?.id;
        if (tabId != null) {
          const rep = await getReport(tabId);
          if (rep && rep.spotted > 0) {
            rep.spotted -= 1;
            await setReport(tabId, rep);
            setBadge(tabId, rep.spotted);
          }
        }
        return { ok: true };
      }

      case MSG.GET_SITE_STATE: {
        const pattern = msg.url ? originPatternFor(msg.url) : null;
        let granted = false;
        let host = null;
        if (pattern) {
          host = new URL(msg.url).hostname;
          granted = await chrome.permissions.contains({ origins: [pattern] });
        }
        const st = await Bananers.store.getAll();
        const learned = host ? (st.hostIndex[host] || []).length : 0;
        const report = msg.tabId != null ? await getReport(msg.tabId) : null;
        return {
          ok: true,
          supported: !!pattern,
          granted,
          host,
          learned,
          spotted: report?.spotted ?? null,
          policyId: Bananers.policy.installedId(),
        };
      }

      /* Popup already obtained the optional host permission (the request
       * must happen in the popup to keep the user gesture). Registration is
       * single-flight; we inject immediately regardless of registration
       * outcome so the first deploy always reaches the current page. */
      case MSG.GRANT_AND_DEPLOY: {
        await syncRegisteredScripts().catch(() => {});
        try {
          await injectNow(msg.tabId);
          return { ok: true };
        } catch (err) {
          return { ok: false, error: String(err?.message || err) };
        }
      }

      case MSG.LIST_GRANTS: {
        return { ok: true, origins: await grantedOriginPatterns() };
      }

      case MSG.REVOKE_ORIGIN: {
        await chrome.permissions.remove({ origins: [msg.origin] });
        await syncRegisteredScripts();
        // Tell any open tabs on that origin to tear down their live artifacts
        // (observer, cloak styles) — unregistering only stops future injection.
        try {
          const tabs = await chrome.tabs.query({ url: msg.origin });
          await Promise.all(tabs.map((t) =>
            chrome.tabs.sendMessage(t.id, { type: MSG.DISABLE_ORIGIN }).catch(() => {})
          ));
        } catch { /* best-effort */ }
        return { ok: true };
      }

      default:
        return undefined; // not ours
    }
  })().then(sendResponse, (err) => sendResponse({ ok: false, error: String(err?.message || err) }));
  return true; // async response
});
