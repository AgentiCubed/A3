/* Renders the Bananers toolbar icon PNGs (16/32/48/128) from an inline SVG
 * using the preinstalled Playwright Chromium. Run: node tools/make-icons.mjs */
import { createRequire } from "module";
import { execSync } from "child_process";
import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require("playwright");
} catch {
  const globalRoot = execSync("npm root -g").toString().trim();
  playwright = require(join(globalRoot, "playwright"));
}

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "..", "extension", "icons");
mkdirSync(outDir, { recursive: true });

const SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <circle cx="64" cy="64" r="60" fill="#1f2430"/>
  <path d="M 34 98 C 16 86 12 60 26 40 C 30 34 34 36 35 42 C 38 64 50 80 72 88
           C 88 94 100 90 106 82 C 110 76 116 80 112 88 C 102 106 60 114 34 98 Z"
        fill="#f7d154" stroke="#8a6d1a" stroke-width="4" stroke-linejoin="round"/>
  <path d="M 28 42 C 26 36 28 32 32 30 L 36 28 C 38 32 37 38 35 42 Z" fill="#7c5f16"/>
  <circle cx="52" cy="60" r="3.2" fill="#3d2f08"/>
  <circle cx="68" cy="66" r="3.2" fill="#3d2f08"/>
  <path d="M 54 72 q 6 6 13 2" stroke="#3d2f08" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M 88 30 l 6 12 13 2 -9 9 2 13 -12 -6 -12 6 2 -13 -9 -9 13 -2 z"
        fill="#f7d154" opacity="0.9" transform="scale(0.55) translate(75 8)"/>
</svg>`;

const browser = await playwright.chromium.launch();
const page = await browser.newPage();

for (const size of [16, 32, 48, 128]) {
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(
    `<style>*{margin:0}body{background:transparent}svg{width:${size}px;height:${size}px;display:block}</style>${SVG}`
  );
  const buf = await page.screenshot({ omitBackground: true });
  writeFileSync(join(outDir, `icon${size}.png`), buf);
  console.log(`wrote icons/icon${size}.png`);
}

await browser.close();
