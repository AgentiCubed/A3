/* Bananers MAIN-world probe (runs in the page's own JS world).
 *
 * Purpose: content scripts live in an isolated world and cannot see the
 * page's event listeners. This probe, injected at document_start into the
 * MAIN world, wraps EventTarget.prototype.addEventListener to keep a
 * lightweight registry, and answers listener queries from the isolated
 * world over window.postMessage.
 *
 * Coverage note (honest limitation, see docs/DESIGN.md §6): only listeners
 * added AFTER document_start are recorded. In practice popup/banner scripts
 * attach their listeners well after this runs. Listeners attached via
 * on* properties are detected separately by the isolated inspector.
 *
 * The reply channel is unauthenticated by design — the page could spoof it.
 * Replies are therefore used ONLY for investigation display/ranking, never
 * as a privileged capability.
 */
(() => {
  if (window.__bananersProbe) return;
  window.__bananersProbe = true;

  const registry = new WeakMap(); // EventTarget -> Map<eventType, count>
  const origAdd = EventTarget.prototype.addEventListener;
  const origRemove = EventTarget.prototype.removeEventListener;

  EventTarget.prototype.addEventListener = function (type, listener, opts) {
    try {
      if (this && (this instanceof Element || this === document || this === window)) {
        let m = registry.get(this);
        if (!m) registry.set(this, (m = new Map()));
        m.set(type, (m.get(type) || 0) + 1);
      }
    } catch { /* never break the page */ }
    return origAdd.call(this, type, listener, opts);
  };

  EventTarget.prototype.removeEventListener = function (type, listener, opts) {
    try {
      const m = registry.get(this);
      if (m && m.has(type)) {
        const n = m.get(type) - 1;
        if (n <= 0) m.delete(type); else m.set(type, n);
      }
    } catch { /* ignore */ }
    return origRemove.call(this, type, listener, opts);
  };

  function summarize(el) {
    const out = {};
    let node = el;
    // Include listeners on the element and up to 3 ancestors (delegation).
    for (let depth = 0; node && depth < 4; depth += 1) {
      const m = registry.get(node);
      if (m) for (const [t, n] of m) out[t] = (out[t] || 0) + n;
      node = node.parentElement;
    }
    const doc = registry.get(document);
    if (doc) for (const [t, n] of doc) out[`doc:${t}`] = n;
    return out;
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (ev.source !== window || !d || d.__bananers !== "listener-query") return;
    let summary = null;
    try {
      const el = document.querySelector(`[data-bananers-probe-target="${d.token}"]`);
      if (el) summary = summarize(el);
    } catch { /* ignore */ }
    window.postMessage(
      { __bananers: "listener-reply", token: d.token, summary },
      "*"
    );
  });
})();
