// The single source of truth for every user-facing string. Writers edit this
// file; UI code references keys and never inlines prose. Canon and tone
// guardrails: docs/bananers-lore-design.md. tests/voice.test.mjs lints this
// catalog mechanically.

export const VOICE = Object.freeze({
  onboarding: Object.freeze({
    greeting: 'Greetings, ape. We have work to do.',
    permissionNote:
      'I only act on sites you deploy me to. Your first deploy on a site is your invitation — nothing is watched before that.',
  }),
  popup: Object.freeze({
    deployCta: 'Deploy {name}',
    noBanners: 'No popups on this branch of the jungle. I remain ready.',
    statsLine: '{count} banners learned. Each one a small kindness to a fellow ape.',
    chooseBananer: 'Choose your bananer',
  }),
  dashboard: Object.freeze({
    title: 'Learn',
    rosterIntro:
      'Every bananer is grateful to be here, and each has their own way with a popup. Pick who walks with you.',
    memoryIntro:
      'Everything we have learned together. Each entry closes itself now, before you ever see it.',
    emptyMemory: "A peaceful stretch of jungle. It won't last. It never does.",
    prefsIntro:
      'Some popups are more fun to watch than to miss. Keep a type visible and your bananer will handle it live, for your amusement.',
    ripenessIntro:
      'Where in the life of a banana would you like to live? Every stage is a good one.',
  }),
  errors: Object.freeze({
    dismissFailed:
      'This banner resisted me today. All things ripen in time — deploy me again and I will relearn it.',
    noBannerFound:
      'I searched every branch of this page and found no popup. A rare, quiet place.',
  }),
  destructive: Object.freeze({
    forgetTitle: 'Return this knowledge?',
    forgetBody:
      'I will return what I learned about this banner to the Great Banana Tree in the Sky. I can always learn it again.',
    forgetConfirm: 'Return it',
    forgetCancel: 'Keep it',
    resetTitle: 'Return everything?',
    resetBody:
      'This erases every learned banner and every preference — all of it returns to the Great Banana Tree in the Sky. We would begin again, together, from the first peel.',
    resetConfirm: 'Return it all',
    resetCancel: 'Keep our memories',
  }),
  prompt: Object.freeze({
    keepShowingTitle: 'Enjoyed that?',
    keepShowingBody:
      'I can let {type} popups keep appearing — purely so you can watch me work. Otherwise they vanish before you ever see them.',
    keepShowingYes: 'Keep the show',
    keepShowingNo: 'Vanish them',
  }),
  farewell: Object.freeze({
    uninstall:
      'Thank you for every deploy, ape. I return to the Great Banana Tree in the Sky exactly as I arrived: grateful.',
  }),
});

// Tiny slot-filler: fill('Deploy {name}', {name: 'Ninjanana'}).
export function fill(str, vars = {}) {
  return str.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
}
