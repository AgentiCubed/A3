// Classic (non-module) content script injected at document_start. Two jobs:
// 1. Preemptive suppression: hide + dismiss banners this user's bananers have
//    already learned on this origin, before the user perceives them.
// 2. Listen for DEPLOY messages from the popup and lazy-load the full deploy
//    pipeline (main.js) only when asked.
// Everything heavier is dynamically imported so unvisited pages pay ~nothing.

(() => {
  if (window.top !== window) return; // top frame only for v1
  const origin = location.origin;
  const mod = (p) => import(chrome.runtime.getURL(p));

  // --- preemptive path (document_start) ------------------------------------

  let hideStyle = null;

  async function preempt() {
    const [store, policyMod] = await Promise.all([
      mod('src/shared/store.js'),
      mod('src/shared/policy.js'),
    ]);
    const learned = await store.getLearnedForOrigin(origin);
    if (learned.length === 0) return;
    const originEnabled = await store.isOriginEnabled(origin);

    const toSuppress = [];
    const toAnimate = [];
    for (const entry of learned) {
      const pref = await store.getTypePref(entry.fingerprint.category);
      const { action } = policyMod.decide({
        origin,
        category: entry.fingerprint.category,
        originEnabled,
        keepShowing: pref.keepShowing,
        isLearned: true,
      });
      if (action === policyMod.ACTIONS.SUPPRESS) toSuppress.push(entry);
      else if (action === policyMod.ACTIONS.SHOW_ANIMATED) toAnimate.push(entry);
    }

    // Invisible from the first frame: inject hide CSS immediately.
    if (toSuppress.length > 0) {
      hideStyle = document.createElement('style');
      hideStyle.textContent = toSuppress
        .flatMap((e) => e.plan.hideSelectors)
        .map((sel) => `${sel} { display: none !important; visibility: hidden !important; }`)
        .join('\n');
      (document.head ?? document.documentElement).appendChild(hideStyle);
    }

    // After DOM settles: really dismiss (not just hide), confirm by fingerprint,
    // record stats, and run watch-mode animations for kept categories.
    const settle = () => finishPreempt(toSuppress, toAnimate).catch(() => {});
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', settle, { once: true });
    } else {
      settle();
    }
  }

  async function finishPreempt(toSuppress, toAnimate) {
    const [store, dismiss, fingerprint, detect] = await Promise.all([
      mod('src/shared/store.js'),
      mod('src/core/dismiss.js'),
      mod('src/core/fingerprint.js'),
      mod('src/core/detect.js'),
    ]);

    const attempt = async (entry) => {
      if (dismiss.executePlan(entry.plan, document)) {
        await store.recordDismissal(entry.fingerprint.id);
        return true;
      }
      return false;
    };

    const pending = new Set();
    for (const entry of toSuppress) {
      if (!(await attempt(entry))) pending.add(entry);
    }

    // Late-injected banners: watch briefly, re-match by fuzzy fingerprint.
    if (pending.size > 0) {
      const observer = new MutationObserver(async () => {
        for (const entry of [...pending]) {
          const roots = detect.findBanners(document, window);
          for (const root of roots) {
            const candidate = fingerprint.extractFeatures(root, origin, entry.fingerprint.category);
            if (fingerprint.isMatch(entry.fingerprint, candidate)) {
              const freshPlan = dismiss.buildPlan(root, entry.fingerprint.category, document);
              dismiss.executePlan(freshPlan, document);
              await store.recordDismissal(entry.fingerprint.id);
              pending.delete(entry);
            }
          }
        }
        if (pending.size === 0) observer.disconnect();
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });
      setTimeout(() => observer.disconnect(), 8000);
    }

    // Watch-mode: the user keeps these types visible to enjoy the show.
    if (toAnimate.length > 0) {
      const main = await mod('src/content/main.js');
      main.handleKeptBanners(toAnimate);
    }
  }

  preempt().catch(() => {});

  // --- deploy path (popup-triggered) ----------------------------------------

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === 'bananers:deploy') {
      mod('src/content/main.js')
        .then((main) => main.deploy(msg.bananerId))
        .then((result) => sendResponse(result))
        .catch((err) => sendResponse({ ok: false, error: String(err) }));
      return true; // async response
    }
    if (msg?.type === 'bananers:get-tab-status') {
      mod('src/core/detect.js')
        .then((detect) => sendResponse({ banners: detect.findBanners(document, window).length }))
        .catch(() => sendResponse({ banners: 0 }));
      return true;
    }
    return false;
  });
})();
