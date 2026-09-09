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


# ---------------- Idea-101 outcome capture + edge/missing-id counters -------
# In-memory per-process counters (reset on restart; frozen semantics,
# OUTCOME_CAPTURE_PREREG). Additive-only on /health.
_EDGE_REJECTION_SHAPES = ("empty_prompt", "missing_prompt", "whitespace_prompt",
                          "non_string_prompt", "malformed_json")
_EDGE_COUNTERS = {k: 0 for k in _EDGE_REJECTION_SHAPES}
_EDGE_COUNTERS_LOCK = threading.Lock()
_MISSING_IDS_LOGGED = [0]  # boxed int guarded by the same lock
_EDGE_DECISIONS_SEEN = 0   # decisions logged this process (for missing-ids rate)

_OUTCOME_WRITER = None
_OUTCOME_WRITER_LOCK = threading.Lock()


def _classify_edge_rejection(malformed, payload):
    """Frozen shape precedence for the 400-edge counters (prereg section 0).
    malformed_json wins (body never parsed); then non-string; then missing;
    then whitespace; then empty."""
    if malformed:
        return "malformed_json"
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    if "prompt" not in (payload if isinstance(payload, dict) else {}):
        return "missing_prompt"
    if not isinstance(prompt, str):
        return "non_string_prompt"
    if prompt == "":
        return "empty_prompt"
    if not prompt.strip():
        return "whitespace_prompt"
    return None


def validate_outcome_request_wrapped(payload):
    from telemetry.service_outcome_log import validate_outcome_request
    return validate_outcome_request(payload)


def _bump_edge(shape):
    with _EDGE_COUNTERS_LOCK:
        _EDGE_COUNTERS[shape] += 1


def _get_outcome_writer():
    global _OUTCOME_WRITER
    if _OUTCOME_WRITER is not None:
        return _OUTCOME_WRITER
    with _OUTCOME_WRITER_LOCK:
        if _OUTCOME_WRITER is None:
            from telemetry.service_outcome_log import ServiceOutcomeWriter
            d = os.environ.get("ROUTER_TELEMETRY_DIR")
            if not d:
                d = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "evidence", "telemetry")
            _OUTCOME_WRITER = ServiceOutcomeWriter(log_dir=d)
    return _OUTCOME_WRITER


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
            # Idea-101 outcome capture: additive-only health keys (frozen
            # OUTCOME_CAPTURE_PREREG). edge_rejections/missing_ids_logged are
            # in-memory per-process counters, reset on restart.
            with _EDGE_COUNTERS_LOCK:
                h["edge_rejections"] = dict(_EDGE_COUNTERS)
                h["missing_ids_logged"] = _MISSING_IDS_LOGGED[0]
            h["outcomes"] = _get_outcome_writer().health()
            env_h = _envelope_health()  # None when the envelope flag is OFF
            if env_h is not None:
                h["envelope"] = env_h
            self._send(h)
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/outcome":
            return self._do_outcome()
        if self.path != "/route":
            return self._send({"error": "not found"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        malformed = False
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            payload = {}
            malformed = True
        # Input validation (frozen: results/101/EDGE_REJECTION_PREREG.md).
        # Precedes config/kill-switch/threshold checks: request validity is a
        # property of the request, not of service state, so it must not be
        # shadowed by (nor shadow) the disabled path or threshold-drift 500.
        # Rejects missing/null/non-string/empty/whitespace-only prompts with
        # NO model call and NO ledger write. The response body is UNCHANGED;
        # only the per-shape edge_rejections counters are new (frozen
        # OUTCOME_CAPTURE_PREREG, in-memory, reset on restart).
        shape = _classify_edge_rejection(malformed, payload)
        if shape is not None:
            _bump_edge(shape)
            return self._send({"error": "empty or missing prompt"}, 400)
        prompt = payload.get("prompt")
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
                # missing_ids_logged (frozen OUTCOME_CAPTURE_PREREG): count
                # THIS process's logged decisions with a null id hash.
                if ev.get("session_id_hash") is None or \
                        ev.get("message_id_hash") is None:
                    with _EDGE_COUNTERS_LOCK:
                        _MISSING_IDS_LOGGED[0] += 1
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

    def _do_outcome(self):
        """POST /outcome (frozen OUTCOME_CAPTURE_PREREG). No model call; no
        decisions.jsonl touch; request-validity 4xxs bump NOTHING."""
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"")
        except (ValueError, UnicodeDecodeError):
            payload = None
        from telemetry.service_outcome_log import (
            OutcomeRequestError, load_decisions_index)
        try:
            eid, outcome, cost, latency_ms, note = \
                validate_outcome_request_wrapped(payload)
        except OutcomeRequestError as e:
            return self._send({"error": e.message}, e.code)
        writer = _get_outcome_writer()
        ddir = writer.log_dir
        decisions_path = os.path.join(ddir, "decisions.jsonl")
        index = load_decisions_index(decisions_path)
        if len(eid) < 32:
            matches = [k for k in index if k.startswith(eid)]
            if not matches:
                return self._send({"error": "unknown event_id"}, 404)
            if len(matches) > 1:
                return self._send({"error": "ambiguous event_id prefix"}, 409)
            eid = matches[0]
        elif eid not in index:
            return self._send({"error": "unknown event_id"}, 404)
        dec = index[eid]
        pairs = writer.load_existing_pairs()
        if (eid, outcome) in pairs:
            return self._send({"error": "duplicate outcome"}, 409)
        row = writer.append(
            event_id=eid, outcome=outcome, cost=cost, latency_ms=latency_ms,
            note=note,
            joined_session_id_hash=dec.get("session_id_hash"),
            joined_message_id_hash=dec.get("message_id_hash"))
        if row is None:
            return self._send({"error": "outcome write failed"}, 500)
        self._send({"outcome_id": row["outcome_id"], "event_id": eid,
                    "status": "logged"}, 202)

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
