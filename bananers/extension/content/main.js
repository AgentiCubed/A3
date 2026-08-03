/* Bananers content-script entry point (registered last, document_start).
 * Arms preemptive suppression immediately, then serves deploy/scan requests
 * from the toolbar popup. Top frame only in v1.
 */
(() => {
  const B = globalThis.Bananers;
  if (!B || B.__mainStarted) return;
  B.__mainStarted = true;
  if (window.top !== window) return;

  const { MSG } = B.constants;

  B.suppress.arm();

  const domReady = () =>
    document.readyState === "loading"
      ? new Promise((r) => document.addEventListener("DOMContentLoaded", r, { once: true }))
      : Promise.resolve();

  async function deployFlow({ bananerId }) {
    await domReady();
    const settings = B.suppress.state.settings || (await B.store.getAll()).settings;

    const cands = B.detect.scan();
    if (!cands.length) return { ok: false, error: "no-popups-found" };
    const cand = cands[0]; // highest score

    const char = B.characters.byId(
      bananerId || (settings.suggestBananer ? B.characters.suggestFor(cand.type) : settings.defaultBananer)
    );

    // Fingerprint BEFORE dismissal — the element must still exist.
    const tokens = B.fingerprint.tokenize(cand.el);
    const hash = B.fingerprint.hashTokens(tokens);
    const selector = B.fingerprint.bestSelector(cand.el);
    const host = location.hostname;

    const reducedMotion =
      settings.reducedMotion === "reduce" || B.overlay.motionReduced();
    const ctl = B.overlay.begin(char, { reducedMotion });

    const { findings, steps } = await B.investigate.run(char, cand, { settings, ctl });
    const targetRect = cand.el.getBoundingClientRect();
    const result = await B.dismiss.executeWithFallback(char.strategyKind, cand, findings, { settings });

    steps.push({
      t: steps.length ? steps[steps.length - 1].t + 1 : 0,
      act: result.ok ? "dismissed" : "failed",
      label: result.ok ? `closed via ${result.kind}` : `failed (tried: ${result.tried.join(" → ")})`,
    });

    if (!result.ok) {
      await ctl.finish(false, targetRect);
      await B.store.log({ host, type: cand.type, bananerId: char.id, action: "deploy", outcome: "failed" });
      return { ok: false, error: "dismiss-failed", tried: result.tried };
    }

    // Persist memory: update the matching fingerprint if we already knew this
    // banner (markup drift), otherwise create a new record.
    const known = B.fingerprint.match(B.suppress.state.fingerprints, tokens, hash);
    const strategy = {
      kind: result.kind,
      clickSelector: result.clickSelector || null,
      killSelectors: findings.killSelectors,
      scrollLock: findings.scrollLock,
    };
    const now = Date.now();
    const base = known?.fp || {
      id: B.store.fpIdFor(host, hash),
      host,
      origin: location.origin,
      createdAt: now,
      timesDismissed: 0,
      timesFailed: 0,
    };
    const record = {
      ...base,
      type: cand.type,
      signature: { hash, tokens, selector },
      strategy,
      bananerId: char.id,
      lastSeenAt: now,
      timesDismissed: (base.timesDismissed || 0) + 1,
      replay: steps.slice(0, B.constants.REPLAY_CAP),
    };
    const fpId = record.id;
    await B.store.saveFingerprint(record);
    // Keep the in-memory suppression snapshot current so a re-insertion on the
    // same SPA page recalls this record instead of re-learning it.
    B.suppress.remember(record);

    await B.store.log({
      host, fpId, type: cand.type, bananerId: char.id,
      action: "deploy", outcome: `dismissed:${result.kind}`,
    });
    try { chrome.runtime.sendMessage({ type: MSG.DISMISSED, fpId }); } catch { /* ok */ }

    await ctl.finish(true, targetRect);
    // Fire-and-forget: the card waits for the user (or its 20s timeout);
    // the deploy response must not block on that choice.
    B.microprompt.maybeShow(cand.type, char).catch(() => {});

    return { ok: true, fpId, type: cand.type, kind: result.kind, bananer: char.id };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    (async () => {
      switch (msg?.type) {
        case MSG.PING:
          return { ok: true, ready: true };
        case MSG.DISABLE_ORIGIN:
          // User revoked this origin: stop observing and remove page artifacts.
          B.suppress.disable();
          return { ok: true };
        case MSG.SCAN: {
          await domReady();
          const cands = B.detect.scan();
          return {
            ok: true,
            candidates: cands.map((c) => ({
              type: c.type,
              score: Math.round(c.score),
              coverage: +c.coverage.toFixed(3),
            })),
          };
        }
        case MSG.DEPLOY:
          return deployFlow(msg);
        default:
          return undefined;
      }
    })().then(sendResponse, (err) => sendResponse({ ok: false, error: String(err?.message || err) }));
    return true;
  });
})();
