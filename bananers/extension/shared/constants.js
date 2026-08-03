/* Bananers shared constants.
 * Plain script (no modules): attaches to globalThis.Bananers so the same file
 * is loadable as a content script, in extension pages, and via importScripts()
 * in the service worker. */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.constants) return;

  const TYPES = {
    COOKIE: "cookie-consent",
    NEWSLETTER: "newsletter",
    AD: "ad-interstitial",
    GENERIC: "generic-modal",
  };

  B.constants = {
    SCHEMA_VERSION: 1,
    TYPES,
    TYPE_LABELS: {
      [TYPES.COOKIE]: "cookie consent",
      [TYPES.NEWSLETTER]: "newsletter",
      [TYPES.AD]: "ad interstitial",
      [TYPES.GENERIC]: "generic popup",
    },

    MSG: {
      DEPLOY: "bananers:deploy",
      SCAN: "bananers:scan",
      PING: "bananers:ping",
      PAGE_REPORT: "bananers:page-report",
      DISMISSED: "bananers:dismissed",
      GET_SITE_STATE: "bananers:get-site-state",
      GRANT_AND_DEPLOY: "bananers:grant-and-deploy",
      REVOKE_ORIGIN: "bananers:revoke-origin",
      LIST_GRANTS: "bananers:list-grants",
      DISABLE_ORIGIN: "bananers:disable-origin",
    },

    // Words that indicate a control ACCEPTS/opts in. Bananers never click these
    // (settings.safety.neverAccept, on by default).
    ACCEPT_WORDS: [
      "accept all", "accept", "agree", "i agree", "allow all", "allow",
      "enable", "turn on", "subscribe", "sign me up", "sign up", "yes please",
      "consent", "sounds good",
    ],

    // Words that indicate a control REJECTS or closes without opting in,
    // in descending order of preference.
    REJECT_WORDS: [
      "reject all", "reject", "refuse", "decline", "deny", "disagree",
      "necessary only", "only necessary", "essential only",
      "use necessary cookies only", "continue without agreeing",
      "continue without", "no thanks", "no, thanks", "not now", "maybe later",
    ],
    CLOSE_WORDS: ["close", "dismiss", "skip", "skip ad", "no", "got it", "×", "x", "✕", "✖", "╳"],

    // Keyword → banner-type classification vocab (lowercased match).
    TYPE_KEYWORDS: {
      [TYPES.COOKIE]: ["cookie", "cookies", "consent", "gdpr", "privacy choices", "data protection", "tracking technologies", "legitimate interest"],
      [TYPES.NEWSLETTER]: ["newsletter", "subscribe", "sign up", "inbox", "email address", "mailing list", "don't miss"],
      [TYPES.AD]: ["advertisement", "sponsored", "skip ad", "continue to site", "ad blocker", "adblock", "special offer"],
    },

    // Tunables for detection/fingerprinting.
    DETECT: {
      MAX_NODES: 5000,
      MIN_Z_INDEX: 10,
      MIN_COVERAGE: 0.08,      // fraction of viewport a candidate must cover…
      BAR_MIN_HEIGHT: 60,      // …unless it is a full-width top/bottom bar this tall.
      SIM_THRESHOLD: 0.6,      // Jaccard similarity for fuzzy fingerprint match.
    },

    LOG_CAP: 200,              // eventLog ring-buffer size
    REPLAY_CAP: 40,            // max steps stored per fingerprint replay
  };
})();
