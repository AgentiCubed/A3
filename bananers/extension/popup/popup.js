/* Bananers toolbar popup: quick actions — "deploy a bananer here".
 * The permission request happens HERE (user gesture required); persistent
 * registration + immediate injection are delegated to the service worker.
 */
(() => {
  const B = globalThis.Bananers;
  const { MSG, TYPE_LABELS } = B.constants;

  const $ = (sel) => document.querySelector(sel);
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  let tab = null;
  let siteState = null;
  let selectedId = null;
  let suggestedId = null;

  async function activeTab() {
    // ?tabId= override lets the e2e harness drive the popup as a normal page.
    const forced = new URLSearchParams(location.search).get("tabId");
    if (forced) return (await chrome.tabs.get(Number(forced))) || null;
    const [t] = await chrome.tabs.query({ active: true, currentWindow: true });
    return t || null;
  }

  function renderRoster() {
    const roster = $("#roster");
    roster.innerHTML = "";
    for (const c of B.characters.ROSTER) {
      const btn = document.createElement("button");
      btn.className = "chip";
      btn.setAttribute("role", "radio");
      btn.setAttribute("aria-checked", String(c.id === selectedId));
      btn.title = `${c.name} — ${c.tagline}`;
      btn.innerHTML = B.characters.spriteFor(c.id) +
        (c.id === suggestedId ? '<span class="suggest">PICK</span>' : "");
      btn.addEventListener("click", () => {
        selectedId = c.id;
        renderRoster();
        $("#char-blurb").textContent = `${c.name}: ${c.investigationLabel} ${c.techniqueLabel}`;
      });
      roster.appendChild(btn);
    }
    const sel = B.characters.byId(selectedId);
    $("#char-blurb").textContent = `${sel.name}: ${sel.investigationLabel} ${sel.techniqueLabel}`;
  }

  function renderStatus() {
    const el = $("#status");
    el.hidden = false;
    el.innerHTML = `
      <div class="stat"><b>${siteState.learned}</b><span>learned here</span></div>
      <div class="stat"><b>${siteState.spotted ?? "–"}</b><span>popups spotted</span></div>
      <div class="stat"><b>${siteState.granted ? "on" : "off"}</b><span>auto-handling</span></div>`;
  }

  function showResult(text, isErr = false) {
    const el = $("#result");
    el.hidden = false;
    el.textContent = text;
    el.className = `result${isErr ? " err" : ""}`;
  }

  async function pingContent(tabId, tries = 8) {
    for (let i = 0; i < tries; i += 1) {
      try {
        const res = await chrome.tabs.sendMessage(tabId, { type: MSG.PING });
        if (res?.ready) return true;
      } catch { /* not injected yet */ }
      await wait(150);
    }
    return false;
  }

  async function deploy() {
    const btn = $("#deploy");
    btn.disabled = true;
    btn.textContent = "Deploying…";
    try {
      const pattern = `${new URL(tab.url).protocol}//${new URL(tab.url).hostname}/*`;

      // Persistent access enables preemptive suppression on later visits.
      // Without it the deploy is a one-shot under activeTab and the learned
      // record can't be replayed — the result message must not promise recall.
      let persistent = siteState.granted;
      if (!persistent && $("#remember").checked) {
        // Must run in the popup to keep the user gesture.
        persistent = await chrome.permissions.request({ origins: [pattern] });
      }

      await chrome.runtime.sendMessage({ type: MSG.GRANT_AND_DEPLOY, tabId: tab.id });

      if (!(await pingContent(tab.id))) {
        showResult("Couldn't reach this page (it may block scripts). Try reloading it.", true);
        return;
      }

      const res = await chrome.tabs.sendMessage(tab.id, {
        type: MSG.DEPLOY,
        bananerId: selectedId,
      });

      if (res?.ok) {
        const label = TYPE_LABELS[res.type] || res.type;
        const name = B.characters.byId(res.bananer).name;
        showResult(persistent
          ? `${name} took down a ${label} popup (${res.kind}). It won't bother you here again.`
          : `${name} took down a ${label} popup (${res.kind}) — just this once. Tick “Remember this site” to have it handled automatically next time.`);
      } else if (res?.error === "no-popups-found") {
        showResult("No popups found on this page right now — the bananer stood down.", false);
      } else {
        showResult(`Dismissal failed (${res?.error || "unknown"}).`, true);
      }

      siteState = await chrome.runtime.sendMessage({
        type: MSG.GET_SITE_STATE, url: tab.url, tabId: tab.id,
      });
      renderStatus();
    } catch (err) {
      showResult(`Deploy failed (${err?.message || err}).`, true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Deploy bananer";
    }
  }

  async function init() {
    const st = await B.store.getAll();
    selectedId = st.settings.defaultBananer;

    tab = await activeTab();
    if (!tab?.url || !/^https?:/.test(tab.url)) {
      $("#site-line").textContent = "Bananers can't work on this page.";
      renderRoster();
      return;
    }
    const host = new URL(tab.url).hostname;
    $("#site-line").textContent = host;

    siteState = await chrome.runtime.sendMessage({
      type: MSG.GET_SITE_STATE, url: tab.url, tabId: tab.id,
    });
    renderStatus();

    // Render the roster and enable deploy immediately — the scan-based
    // suggestion is a best-effort enhancement layered on after.
    renderRoster();
    $("#deploy").disabled = false;

    // If the content script is live, ask what's on the page to suggest a
    // matching bananer. Time-boxed: its handler awaits DOMContentLoaded, which
    // can be slow on a still-loading page, and must not block the UI.
    try {
      const scan = await Promise.race([
        chrome.tabs.sendMessage(tab.id, { type: MSG.SCAN }),
        new Promise((r) => setTimeout(() => r(null), 1200)),
      ]);
      if (scan?.ok && scan.candidates.length && st.settings.suggestBananer) {
        suggestedId = B.characters.suggestFor(scan.candidates[0].type);
        selectedId = suggestedId;
        renderRoster();
      }
    } catch { /* content not injected yet — fine */ }
  }

  $("#deploy").addEventListener("click", deploy);
  $("#open-dashboard").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  init();
})();
