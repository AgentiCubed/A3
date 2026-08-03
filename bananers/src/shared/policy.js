// Popup-handling policy. This module is the designated extension point for the
// future "Banana God" orchestrator (see docs/bananers-core-design.md §9): it
// may register a hook that decides case-by-case; nothing about it is
// implemented here beyond the seam itself.

export const ACTIONS = Object.freeze({
  SUPPRESS: 'suppress-preemptively',
  SHOW_ANIMATED: 'show-and-dismiss-animated',
  LEAVE: 'leave-alone',
});

const hooks = [];

// A hook receives the same ctx as decide() and returns a decision or null to
// abstain. First non-null hook result wins over the default policy.
export function registerPolicyHook(fn) {
  hooks.push(fn);
}

/**
 * @param {object} ctx
 * @param {string} ctx.origin        page origin
 * @param {string} ctx.category     banner category
 * @param {boolean} ctx.originEnabled user opted this origin into automatic handling
 * @param {boolean} ctx.keepShowing  user opted this category into watch-mode
 * @param {boolean} ctx.isLearned    banner has a stored dismissal plan
 * @returns {{action: string, reason: string}}
 */
export function decide(ctx) {
  for (const hook of hooks) {
    const verdict = hook(ctx);
    if (verdict) return verdict;
  }
  if (!ctx.originEnabled) {
    return { action: ACTIONS.LEAVE, reason: 'origin not opted in' };
  }
  if (!ctx.isLearned) {
    return { action: ACTIONS.LEAVE, reason: 'not yet learned — deploy a bananer' };
  }
  if (ctx.keepShowing) {
    return { action: ACTIONS.SHOW_ANIMATED, reason: 'user keeps this type for the show' };
  }
  return { action: ACTIONS.SUPPRESS, reason: 'learned and not kept' };
}
