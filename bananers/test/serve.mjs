/* Tiny static server for the synthetic banner test pages.
 * Usable standalone (node test/serve.mjs [port]) or imported by run-tests. */
import http from "http";
import { readFile } from "fs/promises";
import { extname, join, normalize } from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";

const PAGES = join(dirname(fileURLToPath(import.meta.url)), "pages");
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".png": "image/png",
};

export function startServer(port) {
  const server = http.createServer(async (req, res) => {
    try {
      const path = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname));
      const file = join(PAGES, path === "/" ? "cookie-banner.html" : path);
      if (!file.startsWith(PAGES)) throw new Error("forbidden");
      const body = await readFile(file);
      res.writeHead(200, {
        "content-type": MIME[extname(file)] || "application/octet-stream",
        "cache-control": "no-store",
      });
      res.end(body);
    } catch {
      res.writeHead(404).end("not found");
    }
  });
  return new Promise((resolve) => server.listen(port, "127.0.0.1", () => resolve(server)));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number(process.argv[2]) || 8907;
  await startServer(port);
  console.log(`serving test pages on http://127.0.0.1:${port}/`);
}
