/* Bananers Learn dashboard: roster, memory browser, replays, preferences,
 * and the onboarding disclosure. */
(() => {
  const B = globalThis.Bananers;
  const { MSG, TYPES, TYPE_LABELS } = B.constants;
  const $ = (s) => document.querySelector(s);

  /* ---------- routing ---------- */

  function route() {
    const view = (location.hash || "#roster").slice(1);
    const known = ["roster", "memory", "replays", "settings", "onboarding"];
    const v = known.includes(view) ? view : "roster";
    document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll("nav a").forEach((a) =>
      a.classList.toggle("active", a.dataset.view === v));
    $(`#view-${v}`).classList.add("active");
  }
  addEventListener("hashchange", () => { route(); render(); });

  /* Anything that ever touched page content (button labels quoted in replay
   * steps, hostnames, outcome strings) is escaped before innerHTML rendering —
   * a hostile page must not be able to smuggle markup into extension pages. */
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));

  const rel = (ts) => {
    if (!ts) return "never";
    const d = Date.now() - ts;
    if (d < 60e3) return "just now";
    if (d < 3600e3) return `${Math.round(d / 60e3)}m ago`;
    if (d < 86400e3) return `${Math.round(d / 3600e3)}h ago`;
    return `${Math.round(d / 86400e3)}d ago`;
  };

  /* ---------- roster ---------- */

  function renderRoster(st) {
    const counts = {};
    for (const fp of Object.values(st.fingerprints)) {
      counts[fp.bananerId] = (counts[fp.bananerId] || 0) + fp.timesDismissed;
    }
    $("#roster-cards").innerHTML = B.characters.ROSTER.map((c) => `
      <div class="char-card" style="--card-accent:${c.accent}">
        <div class="art">${B.characters.spriteFor(c.id)}</div>
        <h3>${c.name}</h3>
        <p class="tag">${c.tagline}</p>
        <dl>
          <div><dt>Appearance</dt><dd>${c.appearance}</dd></div>
          <div><dt>Investigation</dt><dd>${c.investigationLabel}</dd></div>
          <div><dt>Closing technique</dt><dd>${c.techniqueLabel}</dd></div>
        </dl>
        <p class="stat"><b>${counts[c.id] || 0}</b> popups dismissed</p>
      </div>`).join("");
  }

  /* ---------- memory ---------- */

  function renderMemory(st) {
    $("#type-toggles").innerHTML = Object.values(TYPES).map((t) => {
      const on = !!st.settings.typeOverrides[t]?.show;
      return `<label><input type="checkbox" data-type="${t}" ${on ? "checked" : ""}/>
        Keep showing me <b>${TYPE_LABELS[t]}</b> popups (let me watch the takedown)</label>`;
    }).join("");
    $("#type-toggles").querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", async () => {
        await B.store.setTypeOverride(input.dataset.type, input.checked);
      });
    });

    const byHost = {};
    for (const fp of Object.values(st.fingerprints)) (byHost[fp.host] ??= []).push(fp);
    const hosts = Object.keys(byHost).sort();

    $("#memory-list").innerHTML = hosts.length ? hosts.map((host) => `
      <div class="site-group">
        <h3>${esc(host)}</h3>
        <table>
          <thead><tr><th>Type</th><th>Learned by</th><th>Strategy</th><th>Dismissed</th><th>Last seen</th><th></th></tr></thead>
          <tbody>
            ${byHost[host].map((fp) => `
              <tr>
                <td>${TYPE_LABELS[fp.type] || fp.type}</td>
                <td><span class="mini">${B.characters.spriteFor(fp.bananerId)}</span>${B.characters.byId(fp.bananerId).name}</td>
                <td><code>${fp.strategy?.kind || "?"}</code></td>
                <td>${fp.timesDismissed}×${fp.timesFailed ? ` <span class="muted">(${fp.timesFailed} contained)</span>` : ""}</td>
                <td>${rel(fp.lastSeenAt)}</td>
                <td><button class="btn small" data-forget="${fp.id}">Forget</button></td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`).join("")
      : `<div class="panel muted">Nothing learned yet. Deploy a bananer from the toolbar popup on a site with an annoying popup.</div>`;

    $("#memory-list").querySelectorAll("[data-forget]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await B.store.forgetFingerprint(btn.dataset.forget);
        render();
      });
    });
  }

  /* ---------- replays ---------- */

  let selectedEvent = null;

  function renderReplays(st) {
    const events = [...st.eventLog].reverse().slice(0, 40);
    $("#event-list").innerHTML = events.length ? events.map((e, i) => `
      <div class="event ${selectedEvent === i ? "sel" : ""}" data-i="${i}">
        <span class="mini">${B.characters.spriteFor(e.bananerId)}</span>
        <div>
          <div>${e.action === "recall" ? "Auto-closed" : "Deployed on"} <b>${esc(e.host)}</b> — ${esc(TYPE_LABELS[e.type] || e.type || "popup")}</div>
          <div class="when">${new Date(e.ts).toLocaleString()} · ${esc(e.outcome)}</div>
        </div>
      </div>`).join("")
      : `<div class="panel muted">No activity yet.</div>`;

    $("#event-list").querySelectorAll(".event").forEach((el) => {
      el.addEventListener("click", () => {
        selectedEvent = Number(el.dataset.i);
        playReplay(st, events[selectedEvent]);
        renderReplays(st);
      });
    });
  }

  function playReplay(st, evt) {
    const stage = $("#replay-stage");
    const fp = evt.fpId ? st.fingerprints[evt.fpId] : null;
    const char = B.characters.byId(evt.bananerId);
    const steps = fp?.replay?.length ? fp.replay : [
      { t: 0, act: "step", label: evt.action === "recall" ? "Recognized a known banner before paint." : "Investigated the popup." },
      { t: 1, act: evt.outcome?.startsWith("dismissed") || evt.outcome === "click-dismiss" ? "dismissed" : "verdict", label: `outcome: ${evt.outcome}` },
    ];
    stage.innerHTML = `
      <div class="head">
        <span class="mini">${B.characters.spriteFor(char.id)}</span>
        <div><b>${char.name}</b> on ${esc(evt.host)}<br/><span class="muted">${new Date(evt.ts).toLocaleString()}</span></div>
      </div>`;
    steps.forEach((s, i) => {
      const div = document.createElement("div");
      div.className = "step";
      div.style.animationDelay = `${i * 0.45}s`;
      div.innerHTML = `<span class="t">+${Number(s.t) || 0}ms</span><span>${s.act === "dismissed" ? "💥 " : s.act === "verdict" ? "🎯 " : ""}${esc(s.label)}</span>`;
      stage.appendChild(div);
    });
  }

  /* ---------- settings ---------- */

  async function renderSettings(st) {
    const sel = $("#default-bananer");
    sel.innerHTML = B.characters.ROSTER
      .map((c) => `<option value="${c.id}" ${st.settings.defaultBananer === c.id ? "selected" : ""}>${c.name}</option>`)
      .join("");
    sel.onchange = () => B.store.patch((s) => { s.settings.defaultBananer = sel.value; return s; });

    const sug = $("#suggest-toggle");
    sug.checked = st.settings.suggestBananer;
    sug.onchange = () => B.store.patch((s) => { s.settings.suggestBananer = sug.checked; return s; });

    const motion = $("#motion-select");
    motion.value = st.settings.reducedMotion;
    motion.onchange = () => B.store.patch((s) => { s.settings.reducedMotion = motion.value; return s; });

    const grants = await chrome.runtime.sendMessage({ type: MSG.LIST_GRANTS }).catch(() => null);
    $("#grant-list").innerHTML = grants?.origins?.length
      ? grants.origins.map((o) => `<li><span>${o}</span><button class="btn small" data-revoke="${o}">Revoke</button></li>`).join("")
      : `<li class="muted">No sites allowed yet.</li>`;
    $("#grant-list").querySelectorAll("[data-revoke]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await chrome.runtime.sendMessage({ type: MSG.REVOKE_ORIGIN, origin: btn.dataset.revoke });
        render();
      });
    });

    $("#wipe").onclick = async () => {
      if (confirm("Forget every learned banner, strategy, and log entry?")) {
        await B.store.wipeMemory();
        render();
      }
    };
  }

  /* ---------- boot ---------- */

  async function render() {
    const st = await B.store.getAll();
    renderRoster(st);
    renderMemory(st);
    renderReplays(st);
    renderSettings(st);
  }

  $("#onboard-done").addEventListener("click", async () => {
    await B.store.patch((s) => { s.settings.onboarded = true; return s; });
    location.hash = "#roster";
  });

  chrome.storage.onChanged.addListener(() => render());

  route();
  render();
})();
