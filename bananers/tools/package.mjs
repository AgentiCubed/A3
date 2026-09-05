/* Package the Bananers extension into a Chrome Web Store-ready ZIP.
 *
 *   node bananers/tools/package.mjs
 *
 * Produces bananers/dist/bananers-<version>.zip with manifest.json at the
 * archive root (what the Web Store expects), after validating:
 *  - manifest.json parses and has the required MV3 fields;
 *  - the store "description" fits the 132-character limit;
 *  - every file the manifest references actually exists;
 *  - the shipped manifest is permissionless (no baked-in host_permissions or
 *    content_scripts — those are the e2e harness's, never the product's).
 */
import { execFileSync } from "child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, statSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const here = dirname(fileURLToPath(import.meta.url));
const extDir = join(here, "..", "extension");
const distDir = join(here, "..", "dist");

const fail = (m) => { console.error(`✗ ${m}`); process.exitCode = 1; };
const ok = (m) => console.log(`✓ ${m}`);

const manifest = JSON.parse(readFileSync(join(extDir, "manifest.json"), "utf8"));

// --- required fields ---
if (manifest.manifest_version !== 3) fail(`manifest_version must be 3 (got ${manifest.manifest_version})`);
else ok("manifest_version 3");
for (const f of ["name", "version", "description", "icons"]) {
  if (!manifest[f]) fail(`missing required field: ${f}`);
}
if (manifest.name && manifest.version) ok(`${manifest.name} v${manifest.version}`);

// --- Web Store limits ---
if (manifest.name && manifest.name.length > 75) fail(`name too long (${manifest.name.length} > 75)`);
if (manifest.description) {
  const n = [...manifest.description].length; // code points, matches CWS counting
  if (n > 132) fail(`description too long for the Web Store (${n} > 132 chars)`);
  else ok(`description ${n}/132 chars`);
}

// --- permissionless production manifest ---
if (manifest.content_scripts) fail("shipped manifest must not declare static content_scripts (opt-in only)");
else ok("no static content_scripts (opt-in registration)");
if (manifest.host_permissions) fail("shipped manifest must not declare host_permissions (use optional_host_permissions)");
else ok("no up-front host_permissions");
ok(`permissions: [${(manifest.permissions || []).join(", ")}]`);
ok(`optional_host_permissions: [${(manifest.optional_host_permissions || []).join(", ")}]`);

// --- every referenced file exists ---
const refs = new Set();
const add = (p) => p && refs.add(p);
Object.values(manifest.icons || {}).forEach(add);
Object.values(manifest.action?.default_icon || {}).forEach(add);
add(manifest.action?.default_popup);
add(manifest.options_page);
add(manifest.background?.service_worker);

// files the service worker injects (content scripts + probe) must ship too
const sw = readFileSync(join(extDir, manifest.background.service_worker), "utf8");
const listMatch = sw.match(/const CONTENT_FILES = \[([\s\S]*?)\]/);
if (listMatch) listMatch[1].match(/"[^"]+"/g)?.forEach((s) => add(JSON.parse(s)));
(sw.match(/const PROBE_FILE = "([^"]+)"/) || []).slice(1).forEach(add);

let missing = 0;
for (const r of refs) {
  if (!existsSync(join(extDir, r))) { fail(`referenced file missing: ${r}`); missing += 1; }
}
if (!missing) ok(`all ${refs.size} referenced files present`);

if (process.exitCode) {
  console.error("\nValidation failed — not packaging.");
  process.exit(1);
}

// --- build the ZIP (manifest at archive root) ---
mkdirSync(distDir, { recursive: true });
const zipPath = join(distDir, `bananers-${manifest.version}.zip`);
rmSync(zipPath, { force: true });
execFileSync(
  "zip",
  ["-r", "-X", "-q", zipPath, ".",
   "-x", "*.DS_Store", "-x", "__MACOSX*", "-x", "*.map"],
  { cwd: extDir }
);

const bytes = statSync(zipPath).size;
const mb = (bytes / 1048576).toFixed(2);
console.log(`\n📦 ${zipPath}`);
console.log(`   ${bytes.toLocaleString()} bytes (${mb} MB)` + (bytes < 10 * 1048576 ? " — under the 10 MB limit ✓" : " — OVER 10 MB ✗"));
console.log("   contents:");
console.log(execFileSync("unzip", ["-l", zipPath]).toString().split("\n").slice(3, -3).map((l) => "   " + l.trim()).join("\n"));
