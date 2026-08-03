// Shared constants: banner categories, storage keys, message types.

export const CATEGORIES = Object.freeze({
  COOKIE: 'cookie-consent',
  NEWSLETTER: 'newsletter',
  AD: 'ad-interstitial',
  SURVEY: 'survey',
  GENERIC: 'generic-modal',
});

export const CATEGORY_LABELS = Object.freeze({
  [CATEGORIES.COOKIE]: 'Cookie consent',
  [CATEGORIES.NEWSLETTER]: 'Newsletter',
  [CATEGORIES.AD]: 'Ad interstitial',
  [CATEGORIES.SURVEY]: 'Survey',
  [CATEGORIES.GENERIC]: 'Modal',
});

// Versioned storage keys — bump the prefix for schema migrations.
export const KEYS = Object.freeze({
  LEARNED: 'bananers/v1/learned',
  PREFS: 'bananers/v1/prefs',
  SETTINGS: 'bananers/v1/settings',
});

export const MESSAGES = Object.freeze({
  DEPLOY: 'bananers:deploy',
  GET_TAB_STATUS: 'bananers:get-tab-status',
  BANNER_HANDLED: 'bananers:banner-handled',
});

// Fuzzy re-recognition threshold for fingerprint matching (see fingerprint.js).
export const MATCH_THRESHOLD = 0.6;

export const DEFAULT_SETTINGS = Object.freeze({
  activeBananer: 'sherlock-peel',
  ripeness: null, // null = derive from prefers-color-scheme on first UI load
  siteMode: 'enabled-only', // automatic handling only on origins the user opted into
});
