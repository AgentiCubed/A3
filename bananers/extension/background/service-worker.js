/* Bananers service worker.
 * Owns everything that needs SW-only APIs: dynamic content-script
 * registration for opted-in origins, permission lifecycle, badge state,
 * and the onboarding page. Learning data itself is written by content
 * scripts straight into chrome.storage.local (see shared/storage.js).
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

/* tabId → last page report ({ spotted, types }) for badge/popup state. */
const tabReports = new Map();

/* ---------- dynamic registration for opted-in origins ---------- */

async function grantedOriginPatterns() {
  const { origins = [] } = await chrome.permissions.getAll();
  return origins.filter((o) => /^https?:\/\//.test(o) || o === "<all_urls>");
}

async function syncRegisteredScripts() {
  const existing = await chrome.scripting.getRegisteredContentScripts({
    ids: ["bananers-core", "bananers-probe"],
  }).catch(() => []);
  if (existing.length) {
    await chrome.scripting.unregisterContentScripts({
      ids: existing.map((s) => s.id),
    });
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
  ]);
}

chrome.permissions.onAdded.addListener(syncRegisteredScripts);
chrome.permissions.onRemoved.addListener(syncRegisteredScripts);

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

chrome.runtime.onStartup?.addListener(syncRegisteredScripts);

chrome.tabs.onRemoved.addListener((tabId) => tabReports.delete(tabId));

/* ---------- helpers ---------- */

function setBadge(tabId, count) {
  const text = count > 0 ? String(count) : "";
  chrome.action.setBadgeText({ tabId, text }).catch(() => {});
  chrome.action.setBadgeBackgroundColor({ tabId, color: "#e0563f" }).catch(() => {});
}

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
          tabReports.set(tabId, { spotted: msg.spotted, types: msg.types });
          setBadge(tabId, msg.spotted);
        }
        return { ok: true };
      }

      case MSG.DISMISSED: {
        const tabId = sender.tab?.id;
        if (tabId != null) {
          const rep = tabReports.get(tabId);
          if (rep && rep.spotted > 0) {
            rep.spotted -= 1;
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
        const report = msg.tabId != null ? tabReports.get(msg.tabId) : null;
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
       * must happen in the popup to keep the user gesture). We register
       * persistent scripts and inject into the current page immediately. */
      case MSG.GRANT_AND_DEPLOY: {
        await syncRegisteredScripts();
        await injectNow(msg.tabId);
        return { ok: true };
      }

      case MSG.LIST_GRANTS: {
        return { ok: true, origins: await grantedOriginPatterns() };
      }

      case MSG.REVOKE_ORIGIN: {
        await chrome.permissions.remove({ origins: [msg.origin] });
        await syncRegisteredScripts();
        return { ok: true };
      }

      default:
        return undefined; // not ours
    }
  })().then(sendResponse, (err) => sendResponse({ ok: false, error: String(err?.message || err) }));
  return true; // async response
});
