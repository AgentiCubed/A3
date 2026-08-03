/* Banana God extension point (spec §7 — interface only, NO orchestrator logic).
 *
 * Every show/suppress/engage decision in the extension flows through
 * Bananers.policy.decide(). Today the installed policy is DefaultPolicy — a
 * deliberately simple rule set. A future "Banana God" orchestrator replaces it
 * via Bananers.policy.install() and receives the same DecisionContext, letting
 * it weigh privacy, security, usability, and per-user quirks case-by-case
 * across tabs WITHOUT any content-script or storage-schema changes.
 *
 * DecisionContext:
 *   { host, origin, type,            // banner classification
 *     fingerprint,                   // learned record or null
 *     settings,                      // user settings snapshot
 *     encounter: 'page-load' | 'user-deploy' }
 *
 * Decision:
 *   { action: 'suppress'            // recall strategy, close before paint
 *           | 'show'                // leave the popup alone
 *           | 'engage',             // no memory yet: wait for user to deploy
 *     bananerId?,                   // who acts (suppress/engage)
 *     reason }                      // human-readable, shown in the dashboard log
 */
(() => {
  const B = (globalThis.Bananers ??= {});
  if (B.policy) return;

  const DefaultPolicy = {
    id: "default-v1",
    decide(ctx) {
      const override = ctx.settings?.typeOverrides?.[ctx.type];
      if (override?.show) {
        return { action: "show", reason: `user opted to keep seeing ${ctx.type} popups` };
      }
      if (ctx.fingerprint?.strategy) {
        return {
          action: "suppress",
          bananerId: ctx.fingerprint.bananerId,
          reason: `learned strategy '${ctx.fingerprint.strategy.kind}' on record`,
        };
      }
      return { action: "engage", reason: "no memory of this banner yet" };
    },
  };

  let installed = DefaultPolicy;

  B.policy = {
    decide: (ctx) => installed.decide(ctx),
    install(policy) {
      if (policy && typeof policy.decide === "function") installed = policy;
      return installed.id;
    },
    installedId: () => installed.id,
  };
})();
