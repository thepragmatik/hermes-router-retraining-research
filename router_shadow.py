#!/usr/bin/env python3
"""Tiny localhost-only shadow router service.

GET /health  -> {"status": "ok", "enabled": bool}
POST /route  {"prompt": "..."}  -> same JSON shape as router_v1_cli.py

Listens on 127.0.0.1:8765 ONLY (never 0.0.0.0). Same kill switch and frozen
threshold guard as the CLI. Run: python3 router_shadow.py [--port 8765]

NOTE (ops): `hermes update` restarts launchd gateway services but does NOT
know about this service. If this daemon is running across an update, it
survives (its deps are in the research repo / host python, not the Hermes
venv) — but re-run `curl http://127.0.0.1:8765/health` after any update to
confirm. To make it update-proof end-to-end, run it under its own launchd
plist (future work, only if the shadow period lasts >1 week).
"""
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router_v1_cli import load_config, FROZEN_THRESHOLD, ENGINE  # reuse, DRY


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send({"status": "ok", "enabled": load_config()["enabled"],
                        "engine": ENGINE})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/route":
            return self._send({"error": "not found"}, 404)
        cfg = load_config()
        base = {"mode": "shadow", "engine": ENGINE,
                "ts": datetime.now(timezone.utc).isoformat()}
        if not cfg["enabled"]:
            return self._send({"decision": "disabled", "confidence": 0.0, **base})
        thr = float(cfg.get("threshold", FROZEN_THRESHOLD))
        if abs(thr - FROZEN_THRESHOLD) > 1e-9:
            return self._send({"error": "threshold drift"}, 500)
        n = int(self.headers.get("Content-Length", 0))
        prompt = json.loads(self.rfile.read(n) or b"{}").get("prompt", "")
        from router_v1.route import route
        decision, conf = route(prompt)
        self._send({"decision": decision, "confidence": conf, "threshold": thr, **base})

    def log_message(self, *a):  # silence default stderr spam
        pass


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
