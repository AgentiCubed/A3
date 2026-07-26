"""Hermetic contract test for scripts/prod_smoke.sh."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "prod_smoke.sh"


class _Handler(BaseHTTPRequestHandler):
    ready = True

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self.path == "/healthz":
            self._json({"status": "ok", "version": "test"})
            return
        if self.path == "/readyz":
            redis = "ok" if self.ready else "error: ConnectionError"
            self._json(
                {
                    "status": "ok" if self.ready else "degraded",
                    "checks": {"database": "ok", "redis": redis},
                }
            )
            return
        if self.path == "/login":
            body = b"<html><body><h1>Sign in</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def _json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class ProductionSmokeTest(unittest.TestCase):
    def run_smoke(
        self, *, ready: bool, allow_http: bool = True
    ) -> subprocess.CompletedProcess[str]:
        _Handler.ready = ready
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = os.environ.copy()
            if allow_http:
                env["A3_ALLOW_HTTP"] = "1"
            return subprocess.run(
                ["bash", str(SMOKE), f"http://127.0.0.1:{server.server_port}"],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_healthy_stack_passes(self) -> None:
        result = self.run_smoke(ready=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("production smoke: PASS", result.stdout)

    def test_degraded_dependency_fails(self) -> None:
        result = self.run_smoke(ready=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("readiness is degraded", result.stderr)

    def test_plain_http_requires_explicit_local_override(self) -> None:
        result = self.run_smoke(ready=True, allow_http=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing a non-TLS URL", result.stderr)


if __name__ == "__main__":
    unittest.main()
