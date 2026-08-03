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

      if ($("#remember").checked && !siteState.granted) {
        // Must run in the popup to keep the user gesture.
        const ok = await chrome.permissions.request({ origins: [pattern] });
        if (!ok) showResult("No persistent access granted — deploying just this once.", false);
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
        showResult(`${B.characters.byId(res.bananer).name} took down a ${label} popup (${res.kind}). It won't bother you here again.`);
      } else if (res?.error === "no-popups-found") {
        showResult("No popups found on this page right now — the bananer stood down.", false);
      } else {
        showResult(`Dismissal failed (${res?.error || "unknown"}).`, true);
      }

      siteState = await chrome.runtime.sendMessage({
        type: MSG.GET_SITE_STATE, url: tab.url, tabId: tab.id,
      });
      renderStatus();
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

    // If the content script is live, ask it what's on the page to suggest a
    // matching bananer for the top candidate.
    try {
      const scan = await chrome.tabs.sendMessage(tab.id, { type: MSG.SCAN });
      if (scan?.ok && scan.candidates.length && st.settings.suggestBananer) {
        suggestedId = B.characters.suggestFor(scan.candidates[0].type);
        selectedId = suggestedId;
      }
    } catch { /* content not injected yet — fine */ }

    renderRoster();
    $("#deploy").disabled = false;
  }

  $("#deploy").addEventListener("click", deploy);
  $("#open-dashboard").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  init();
})();
