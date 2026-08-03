/* Bananers entertainment opt-in micro-prompt (spec §6).
 * Shown ONCE per banner type, ever — after the first successful interactive
 * dismissal of that type. Any resolution (either button, the ×, or the 20s
 * auto-timeout) counts as shown and it never appears again for that type.
 * The persistent, revisitable control is the per-type toggle in the Learn
 * dashboard. Default remains "close it before I ever see it".
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.microprompt) return;
  const C = B.constants;

  async function maybeShow(type, character) {
    const first = await B.store.shouldShowMicroPrompt(type);
    if (!first) return { shown: false };

    const label = C.TYPE_LABELS[type] || type;
    const card = B.overlay.card(`
      <button class="x" data-act="close" aria-label="Dismiss">×</button>
      <div class="row">
        <div class="mini">${B.characters.spriteFor(character.id)}</div>
        <div>Enjoyed that? Keep showing me <b>${label}</b> popups so I can deal with them.</div>
      </div>
      <div class="btns">
        <button data-act="show">Keep showing them</button>
        <button class="primary" data-act="hide">Vanish them next time</button>
      </div>
    `);

    return new Promise((resolve) => {
      let done = false;
      const finish = async (act) => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        card.remove();
        if (act === "show") await B.store.setTypeOverride(type, true);
        if (act === "hide") await B.store.setTypeOverride(type, false);
        resolve({ shown: true, choice: act });
      };
      const timer = setTimeout(() => finish("timeout"), 20000);
      card.addEventListener("click", (ev) => {
        const act = ev.target?.dataset?.act;
        if (act === "show" || act === "hide") finish(act);
        else if (act === "close") finish("dismissed");
      });
    });
  }

  B.microprompt = { maybeShow };
})();
