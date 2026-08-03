/* Bananers e2e suite.
 * Loads the real extension into the preinstalled Playwright Chromium
 * (channel "chromium" = full build, new headless — extensions supported),
 * drives it against synthetic banner pages, and asserts the core spec
 * behaviors: learn → dismiss → remember → suppress-before-paint, one-time
 * micro-prompt, per-type opt-in override, and the never-click-Accept rule.
 *
 * The production manifest requests NO host permissions (opt-in per site via
 * the popup). Tests can't click a native permission prompt, so the harness
 * builds a patched copy of the extension with a static 127.0.0.1 grant +
 * static content_scripts — exactly the state a user is in after opting in.
 *
 * Run: node bananers/test/run-tests.mjs
 */
import { createRequire } from "module";
import { execSync } from "child_process";
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { startServer } from "./serve.mjs";

const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require("playwright");
} catch {
  playwright = require(join(execSync("npm root -g").toString().trim(), "playwright"));
}

const here = dirname(fileURLToPath(import.meta.url));
const extSrc = join(here, "..", "extension");
const scratch = join(here, ".scratch");
const extDir = join(scratch, "ext");
const profileDir = join(scratch, "profile");
const PORT = 8907;
const BASE = `http://127.0.0.1:${PORT}`;

/* ---------- tiny assertion kit ---------- */
let passed = 0;
let failed = 0;
const failures = [];
function check(name, cond, detail = "") {
  if (cond) { passed += 1; console.log(`  ✓ ${name}`); }
  else {
    failed += 1;
    failures.push(name);
    console.log(`  ✗ ${name}${detail ? ` — ${JSON.stringify(detail)}` : ""}`);
  }
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function until(fn, ms = 8000, step = 120) {
  const t0 = Date.now();
  let last;
  while (Date.now() - t0 < ms) {
    last = await fn();
    if (last) return last;
    await wait(step);
  }
  return last;
}

/* ---------- build the opted-in test copy of the extension ---------- */
function buildTestExtension() {
  rmSync(scratch, { recursive: true, force: true });
  mkdirSync(scratch, { recursive: true });
  cpSync(extSrc, extDir, { recursive: true });

  const swSource = readFileSync(join(extDir, "background", "service-worker.js"), "utf8");
  const filesMatch = swSource.match(/const CONTENT_FILES = \[([^\]]+)\]/);
  const contentFiles = filesMatch[1].match(/"[^"]+"/g).map((s) => JSON.parse(s));

  const manifest = JSON.parse(readFileSync(join(extDir, "manifest.json"), "utf8"));
  // Match patterns cannot carry ports; http://127.0.0.1/* covers :8907.
  manifest.host_permissions = ["http://127.0.0.1/*"];
  manifest.content_scripts = [
    {
      matches: ["http://127.0.0.1/*"],
      js: contentFiles,
      run_at: "document_start",
      world: "ISOLATED",
    },
    {
      matches: ["http://127.0.0.1/*"],
      js: ["content/main-world-probe.js"],
      run_at: "document_start",
      world: "MAIN",
    },
  ];
  writeFileSync(join(extDir, "manifest.json"), JSON.stringify(manifest, null, 2));
}

/* ---------- service-worker helpers ---------- */
async function getSW(context) {
  let [sw] = context.serviceWorkers();
  if (!sw) sw = await context.waitForEvent("serviceworker", { timeout: 15000 });
  return sw;
}

const deployVia = (sw, url, bananerId) =>
  sw.evaluate(async ({ url, bananerId }) => {
    const [tab] = await chrome.tabs.query({ url: `${url}*` });
    if (!tab) return { ok: false, error: "tab-not-found" };
    return chrome.tabs.sendMessage(tab.id, { type: "bananers:deploy", bananerId });
  }, { url, bananerId });

const readStore = (sw) => sw.evaluate(() => chrome.storage.local.get(null));

const setTypeOverride = (sw, type, show) =>
  sw.evaluate(async ({ type, show }) => {
    const raw = await chrome.storage.local.get("settings");
    const settings = raw.settings || {};
    settings.typeOverrides = settings.typeOverrides || {};
    settings.typeOverrides[type] = { show };
    await chrome.storage.local.set({ settings });
  }, { type, show });

/* ---------- suite ---------- */
async function main() {
  buildTestExtension();
  const server = await startServer(PORT);

  const context = await playwright.chromium.launchPersistentContext(profileDir, {
    channel: "chromium",
    headless: true,
    args: [
      `--disable-extensions-except=${extDir}`,
      `--load-extension=${extDir}`,
    ],
  });

  try {
    const sw = await getSW(context);
    await wait(600); // let onInstalled finish (registration + onboarding tab)
    for (const p of context.pages().slice(1)) await p.close().catch(() => {});
    const page = context.pages()[0] || (await context.newPage());
    const extId = new URL(sw.url()).host;

    /* ---- T1: learn & dismiss a cookie banner (Peel Noir) ---- */
    console.log("\nT1 · first encounter: cookie consent (Peel Noir)");
    await page.goto(`${BASE}/cookie-banner.html`);
    await page.locator("#cmp-root").waitFor({ state: "visible", timeout: 5000 });

    const r1 = await deployVia(sw, `${BASE}/cookie-banner.html`, "peel-noir");
    check("deploy responds ok", r1?.ok === true, r1);
    check("Peel Noir uses precise click (distinct from Bruce)", r1?.kind === "click-precise", r1);
    check("classified as cookie-consent", r1?.type === "cookie-consent", r1);

    await page.locator("#cmp-root").waitFor({ state: "detached", timeout: 5000 }).catch(() => {});
    check("banner removed from DOM", await page.locator("#cmp-root").count() === 0);
    check("REJECT was clicked, not accept",
      await page.evaluate(() => window.__rejected === true && window.__accepted === false));
    check("site recorded rejected consent",
      (await page.evaluate(() => localStorage.getItem("consent"))) === "rejected");

    let store = await readStore(sw);
    const fps1 = Object.values(store.fingerprints || {});
    check("one fingerprint learned", fps1.length === 1, fps1.length);
    check("fingerprint strategy has click selector",
      fps1[0]?.strategy?.clickSelector === "#cmp-reject", fps1[0]?.strategy);
    check("replay steps recorded", (fps1[0]?.replay?.length || 0) >= 3);

    /* ---- micro-prompt: one-time, then never ---- */
    console.log("\nT1b · one-time micro-prompt");
    const card = page.locator("[data-bananers-ui] .card");
    await card.waitFor({ state: "visible", timeout: 4000 }).catch(() => {});
    check("micro-prompt shown after first dismissal of type", await card.count() === 1);
    await card.locator("button.primary").click().catch(() => {});
    store = await readStore(sw);
    check("micro-prompt marked shown for cookie-consent",
      store.microPrompt?.shownForType?.["cookie-consent"] === true, store.microPrompt);
    check("choice recorded as vanish (show=false)",
      store.settings?.typeOverrides?.["cookie-consent"]?.show === false,
      store.settings?.typeOverrides);

    /* ---- T2: revisit → suppressed before user perceives it ---- */
    console.log("\nT2 · revisit: preemptive suppression");
    await page.reload();
    const insertState = await until(() =>
      page.evaluate(() => window.__visibleAtInsert !== null ? {
        visibleAtInsert: window.__visibleAtInsert,
        everVisibleMs: window.__everVisibleMs,
      } : null), 6000);
    check("banner NOT visible at insertion (cloaked pre-paint)",
      insertState && insertState.visibleAtInsert === false, insertState);
    check("pre-paint cloak style present in document",
      await page.evaluate(() => !!document.querySelector("style[data-bananers-cloak]")));
    const rejectedAgain = await until(() => page.evaluate(() => window.__rejected), 6000);
    check("stored strategy replayed (reject clicked silently)", rejectedAgain === true);
    check("banner gone after recall",
      await until(async () => (await page.locator("#cmp-root").count()) === 0, 4000));
    check("micro-prompt NOT shown again", await card.count() === 0);
    store = await readStore(sw);
    check("dismiss count incremented",
      Object.values(store.fingerprints)[0]?.timesDismissed >= 2,
      Object.values(store.fingerprints)[0]?.timesDismissed);

    /* ---- T3: per-type opt-in override keeps the show ---- */
    console.log("\nT3 · per-type override: keep showing cookie popups");
    await setTypeOverride(sw, "cookie-consent", true);
    await page.reload();
    await page.locator("#cmp-root").waitFor({ state: "visible", timeout: 5000 }).catch(() => {});
    await wait(1500);
    check("banner stays visible when type override says show",
      (await page.locator("#cmp-root").count()) === 1 &&
      (await page.evaluate(() => getComputedStyle(document.getElementById("cmp-root")).display)) !== "none");
    await setTypeOverride(sw, "cookie-consent", false);

    /* ---- T4: newsletter modal (Splitsu) + opt-in via prompt ---- */
    console.log("\nT4 · newsletter interstitial (Splitsu)");
    await page.goto(`${BASE}/newsletter.html`);
    await page.locator("#nl-modal").waitFor({ state: "visible", timeout: 5000 });
    const r4 = await deployVia(sw, `${BASE}/newsletter.html`, "splitsu");
    check("newsletter deploy ok", r4?.ok === true, r4);
    check("classified as newsletter", r4?.type === "newsletter", r4);
    check("modal sliced away",
      await until(async () => (await page.locator("#nl-modal").count()) === 0, 5000));
    check("backdrop sliced away too",
      await until(async () => (await page.locator("#nl-overlay").count()) === 0, 3000));
    check("never subscribed", await page.evaluate(() => window.__subscribed === false));

    const card4 = page.locator("[data-bananers-ui] .card");
    await card4.waitFor({ state: "visible", timeout: 4000 }).catch(() => {});
    check("micro-prompt shown for new type (newsletter)", await card4.count() === 1);
    // This time the user enjoys the show: keep showing them.
    await card4.locator("button", { hasText: "Keep showing them" }).click().catch(() => {});
    store = await readStore(sw);
    check("newsletter override set to show",
      store.settings?.typeOverrides?.newsletter?.show === true, store.settings?.typeOverrides);

    await page.reload();
    await page.locator("#nl-modal").waitFor({ state: "visible", timeout: 5000 }).catch(() => {});
    await wait(800);
    check("opted-in type still shows on revisit", (await page.locator("#nl-modal").count()) === 1);

    /* ---- T5: ad takeover (Frost Peel, css-kill) ---- */
    console.log("\nT5 · ad interstitial (Frost Peel)");
    await page.goto(`${BASE}/ad-interstitial.html`);
    await page.locator("#ad-takeover").waitFor({ state: "visible", timeout: 5000 });
    const r5 = await deployVia(sw, `${BASE}/ad-interstitial.html`, "frost-peel");
    check("ad deploy ok", r5?.ok === true, r5);
    check("frozen via css-kill", r5?.kind === "css-kill", r5);
    check("takeover computed display:none",
      await until(() => page.evaluate(() => {
        const el = document.getElementById("ad-takeover");
        return el && getComputedStyle(el).display === "none";
      }), 4000));
    check("scroll unlocked after freeze",
      await page.evaluate(() => getComputedStyle(document.body).overflow !== "hidden"));

    await page.reload();
    check("ad suppressed on revisit",
      await until(() => page.evaluate(() => {
        const el = document.getElementById("ad-takeover");
        return el ? getComputedStyle(el).display === "none" : null;
      }), 6000));

    /* ---- T7: localized labels — never click accept OR reject we can't read --- */
    console.log("\nT7 · localized (German) consent: safety fall-through");
    await page.goto(`${BASE}/localized-consent.html`);
    await page.locator("#loc-root").waitFor({ state: "visible", timeout: 5000 });
    const r7 = await deployVia(sw, `${BASE}/localized-consent.html`, "peel-noir");
    check("localized deploy contained the banner", r7?.ok === true, r7);
    check("used containment, not a click (slice/css)",
      r7?.kind === "slice-remove" || r7?.kind === "css-kill", r7);
    check("neither localized Accept NOR Reject was clicked",
      await page.evaluate(() => window.__locAccepted === false && window.__locRejected === false));
    check("localized banner gone",
      await until(async () => (await page.locator("#loc-root").count()) === 0, 4000));

    /* ---- T8: sticky navbar is not a popup ---- */
    console.log("\nT8 · sticky navbar is not mistaken for a popup");
    await page.goto(`${BASE}/navbar.html`);
    await page.locator("#site-nav").waitFor({ state: "visible", timeout: 5000 });
    const r8 = await deployVia(sw, `${BASE}/navbar.html`, "splitsu");
    check("bananer stands down on a nav-only page", r8?.ok === false && r8?.error === "no-popups-found", r8);
    check("navbar left intact", (await page.locator("#site-nav").count()) === 1);
    check("nav links not clicked (still on navbar page)",
      (await page.evaluate(() => location.pathname)).endsWith("navbar.html"));

    /* ---- T9: positional selector never hides/removes first-party content ---- */
    console.log("\nT9 · positional-selector safety");
    await page.goto(`${BASE}/positional.html`);
    await page.locator("#app-content").waitFor({ timeout: 5000 });
    await page.waitForFunction(() => !!document.querySelector("body > div:nth-of-type(2)"), null, { timeout: 5000 })
      .catch(() => {});
    const r9 = await deployVia(sw, `${BASE}/positional.html`, "splitsu");
    check("positional-banner deploy ok", r9?.ok === true, r9);
    const posStore = await readStore(sw);
    const posRec = Object.values(posStore.fingerprints).find((f) => f.host === "127.0.0.1" && f.origin.includes("127.0.0.1") && f.type === "newsletter" && f.signature.selector.includes(":nth-of-type("));
    check("banner learned with a positional selector (forces the hazard path)", !!posRec, posRec?.signature?.selector);

    await page.reload(); // visit 2 — a leading sibling shifts DOM order
    check("first-party #app-content still present after revisit",
      await until(async () => (await page.locator("#app-content").count()) === 1, 3000));
    check("first-party #app-content still visible (not cloaked by positional sel)",
      await page.evaluate(() => {
        const el = document.getElementById("app-content");
        return !!el && getComputedStyle(el).display !== "none";
      }));
    check("no cloak rule targets a positional selector",
      await page.evaluate(() => {
        const s = document.querySelector("style[data-bananers-cloak]");
        return !s || !s.textContent.includes(":nth-of-type(");
      }));
    check("drifted banner still suppressed via verified/fuzzy path",
      await until(async () => {
        const shown = await page.evaluate(() => {
          const veils = [...document.querySelectorAll("div")].filter((d) => {
            const cs = getComputedStyle(d);
            return cs.position === "fixed" && cs.display !== "none" && d.offsetWidth > 300 && d.offsetHeight > 200;
          });
          return veils.length;
        });
        return shown === 0;
      }, 6000));

    /* ---- T6: extension pages render ---- */
    console.log("\nT6 · popup + Learn dashboard smoke");
    const popup = await context.newPage();
    await popup.goto(`chrome-extension://${extId}/popup/popup.html`);
    await popup.locator(".chip").first().waitFor({ timeout: 5000 });
    check("popup renders full roster", (await popup.locator(".chip").count()) === 5);

    const dash = await context.newPage();
    await dash.goto(`chrome-extension://${extId}/options/options.html#memory`);
    await dash.locator("#memory-list table").waitFor({ timeout: 5000 });
    check("dashboard memory shows learned banners",
      (await dash.locator("#memory-list tbody tr").count()) >= 3);
    check("dashboard renders roster cards",
      (await dash.locator("#roster-cards .char-card").count()) === 5);
    await dash.goto(`chrome-extension://${extId}/options/options.html#replays`);
    check("dashboard lists replay events",
      (await until(() => dash.locator(".event").count(), 3000)) >= 3);

    /* ---- summary ---- */
    store = await readStore(sw);
    console.log(`\nevent log entries: ${store.eventLog?.length}, fingerprints: ${Object.keys(store.fingerprints || {}).length}`);
  } finally {
    await context.close().catch(() => {});
    server.close();
  }

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed) {
    console.log("failures:", failures);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("harness error:", err);
  process.exit(1);
});
