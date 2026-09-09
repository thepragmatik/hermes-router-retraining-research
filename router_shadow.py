#!/usr/bin/env python3
"""Tiny localhost-only shadow router service.

GET /health  -> {"status": "ok", "enabled": bool, "telemetry": {...}}
POST /route  {"prompt": "...", "session_id"?, "message_id"?, "traffic_stratum"?}
             -> same JSON shape as router_v1_cli.py plus "event_id".

Listens on 127.0.0.1 ONLY (never 0.0.0.0). Default port 8765 (the production
launchd service port); tests ALWAYS pass --port >= 8766 or set
ROUTER_SHADOW_PORT. Same kill switch and frozen threshold guard as the CLI.

Idea-101 telemetry (T040-T042): every /route decision is logged through the
SAME shared logger as the CLI (G2 service-side parity). Logging is
best-effort — a logging failure increments the visible error counter (surfaced
on /health) but never fails the route.
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router_v1_cli import load_config, FROZEN_THRESHOLD, ENGINE  # reuse, DRY
from telemetry.wiring import get_logger  # shared logger, G2 parity

# Concurrent cold-start guard: model load (torch + sentence_transformers) must
# happen ONCE, single-threaded, before serving. Without this, simultaneous
# first /route requests race the module import inside router_v1.route and some
# handler threads die mid-import (observed: RemoteDisconnected bursts).
ROUTE_LOCK = threading.Lock()

# ---------------- Idea-105 conformal safety envelope (feature-flagged) --------
# Flag: router_config.yaml -> router.envelope_enabled (default OFF). Read per
# request; the Envelope instance (calibration load + alarm state) is built ONCE
# on the first flagged request and lives for the process lifetime (restart
# resets alarms). Flag OFF => telemetry.envelope is never imported and no
# "envelope" key appears in ANY response (byte-identical to pre-105 service).
_ENVELOPE = None
_ENVELOPE_LOCK = threading.Lock()


def _envelope_flag(cfg_path=None):
    """Read router.envelope_enabled from the router config (default False)."""
    try:
        import yaml
        path = cfg_path or os.environ.get(
            "ROUTER_CONFIG", os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "router_config.yaml"))
        if not os.path.exists(path):
            return False
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return bool((raw.get("router") or {}).get("envelope_enabled", False))
    except Exception:
        return False  # any config trouble keeps the envelope OFF


def _get_envelope():
    """Lazily build the process-wide Envelope on first flagged request."""
    global _ENVELOPE
    if _ENVELOPE is not None:
        return _ENVELOPE
    with _ENVELOPE_LOCK:
        if _ENVELOPE is None:
            from telemetry.envelope import Envelope, load_envelope_config
            cfg = load_envelope_config()  # None -> fail-closed disabled frames
            _ENVELOPE = Envelope(cfg, flag_on=True)
    return _ENVELOPE


def _envelope_frame(decision, confidence):
    """Record-only envelope verdict for one route; None when flag OFF."""
    if not _envelope_flag():
        return None
    env = _get_envelope()
    try:
        return env.evaluate(score=1.0 - float(confidence), decision=decision)
    except Exception:  # belt & braces: evaluate() already never raises
        return {"enabled": False, "mode": "shadow", "alpha": None,
                "action": "disabled", "threshold_used": None}


def _envelope_health():
    if not _envelope_flag():
        return None
    return _get_envelope().health()


def _warmup_model():
    try:
        t0 = time.time()
        from router_v1.route import route
        route("telemetry warmup synthetic prompt")  # loads encoder + head once
        print(f"[router_shadow] model warmup done in {time.time()-t0:.1f}s",
              file=sys.stderr, flush=True)
        return True
    except Exception as e:  # noqa: BLE001 — service must still start for /health
        print(f"[router_shadow] WARNING: model warmup failed: {e}",
              file=sys.stderr, flush=True)
        return False


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            h = {"status": "ok", "enabled": load_config()["enabled"],
                 "engine": ENGINE,
                 "telemetry": get_logger().health()}
            env_h = _envelope_health()  # None when the envelope flag is OFF
            if env_h is not None:
                h["envelope"] = env_h
            self._send(h)
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/route":
            return self._send({"error": "not found"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            payload = {}
        # Input validation (frozen: results/101/EDGE_REJECTION_PREREG.md).
        # Precedes config/kill-switch/threshold checks: request validity is a
        # property of the request, not of service state, so it must not be
        # shadowed by (nor shadow) the disabled path or threshold-drift 500.
        # Rejects missing/null/non-string/empty/whitespace-only prompts with
        # NO model call and NO ledger write.
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return self._send({"error": "empty or missing prompt"}, 400)
        cfg = load_config()
        base = {"mode": "shadow", "engine": ENGINE,
                "ts": datetime.now(timezone.utc).isoformat()}
        if not cfg["enabled"]:
            return self._send({"decision": "disabled", "confidence": 0.0, **base})
        thr = float(cfg.get("threshold", FROZEN_THRESHOLD))
        if abs(thr - FROZEN_THRESHOLD) > 1e-9:
            return self._send({"error": "threshold drift"}, 500)
        # Caller-supplied join identity (idea 101 / gap G1). Only hashes are
        # persisted; the raw values never enter any ledger.
        session_id = payload.get("session_id")
        message_id = payload.get("message_id")
        traffic_stratum = payload.get("traffic_stratum") or "unknown"
        with ROUTE_LOCK:  # serialize model access (lazy load safety)
            from router_v1.route import route
            decision, conf = route(prompt)
        # Shared-logger decision event (best-effort; errors visible on /health)
        event_id = None
        try:
            from telemetry.wiring import record_route_decision
            ev = record_route_decision(
                prompt=prompt, decision=decision, confidence=conf,
                threshold=thr, session_id=session_id, message_id=message_id,
                traffic_stratum=traffic_stratum)
            if ev is not None:
                event_id = ev["event_id"]
        except Exception:
            event_id = None  # telemetry must never break routing
        out = {"decision": decision, "confidence": conf, "threshold": thr, **base}
        if event_id is not None:
            out["event_id"] = event_id
        # Idea-105 envelope verdict (record-only). Added strictly AFTER the raw
        # V1 decision is fixed and telemetry has run: the envelope can only ADD
        # this key — it never alters decision/confidence/threshold, the ledger
        # event, or any protected path (kill switch / drift 500 / edge 400).
        env_frame = _envelope_frame(decision, conf)
        if env_frame is not None:
            out["envelope"] = env_frame
        self._send(out)

    def log_message(self, *a):  # silence default stderr spam
        pass


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--port" in args:
        port = int(args[args.index("--port") + 1])
    else:
        port = int(os.environ.get("ROUTER_SHADOW_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    # Warm the model BEFORE accepting traffic (concurrent cold-start guard).
    _warmup_model()
    print(f"[router_shadow] serving on 127.0.0.1:{port}", file=sys.stderr, flush=True)
    server.serve_forever()
