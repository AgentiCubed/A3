#!/usr/bin/env python3
"""Local server for the Devin control dashboard.

Serves index.html and proxies API calls so keys stay server-side and the
browser never hits CORS issues.

Usage:
    export DEVIN_API_KEY=...        # required to dispatch/list Devin sessions
    export GITHUB_TOKEN=...         # optional; raises GitHub rate limits / private repos
    python3 serve.py [--port 8321] [--repo AgentiCubed/A3]
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEVIN_API = "https://api.devin.ai/v1"
GITHUB_API = "https://api.github.com"

HERE = Path(__file__).resolve().parent


def _forward(url: str, headers: dict, method: str = "GET", body: bytes | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError as e:
        return 502, json.dumps({"error": str(e.reason)}).encode()


class Handler(BaseHTTPRequestHandler):
    repo = "AgentiCubed/A3"

    def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _devin_headers(self) -> dict | None:
        key = os.environ.get("DEVIN_API_KEY")
        if not key:
            return None
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _github_headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "devin-dashboard"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._send(200, json.dumps({
                "repo": self.repo,
                "devin_key_set": bool(os.environ.get("DEVIN_API_KEY")),
                "github_token_set": bool(os.environ.get("GITHUB_TOKEN")),
            }).encode())
        elif self.path.startswith("/api/github/"):
            status, body = _forward(f"{GITHUB_API}/{self.path[len('/api/github/'):]}", self._github_headers())
            self._send(status, body)
        elif self.path.startswith("/api/devin/"):
            headers = self._devin_headers()
            if headers is None:
                self._send(401, b'{"error": "DEVIN_API_KEY not set on the server"}')
                return
            status, body = _forward(f"{DEVIN_API}/{self.path[len('/api/devin/'):]}", headers)
            self._send(status, body)
        else:
            self._send(404, b'{"error": "not found"}')

    def do_POST(self) -> None:  # noqa: N802
        if not self.path.startswith("/api/devin/"):
            self._send(404, b'{"error": "not found"}')
            return
        headers = self._devin_headers()
        if headers is None:
            self._send(401, b'{"error": "DEVIN_API_KEY not set on the server"}')
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        status, resp = _forward(f"{DEVIN_API}/{self.path[len('/api/devin/'):]}", headers, "POST", body)
        self._send(status, resp)

    def log_message(self, fmt: str, *args) -> None:  # quieter logs
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8321)
    parser.add_argument("--repo", default="AgentiCubed/A3")
    args = parser.parse_args()
    Handler.repo = args.repo
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Devin control dashboard: http://127.0.0.1:{args.port}  (repo: {args.repo})")
    if not os.environ.get("DEVIN_API_KEY"):
        print("WARNING: DEVIN_API_KEY is not set - dispatching sessions will fail until you set it.")
    server.serve_forever()


if __name__ == "__main__":
    main()
