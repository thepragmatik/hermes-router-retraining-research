#!/usr/bin/env python3
"""Shadow CLI for the frozen V1 router.

Reads a single prompt (argv or stdin) and prints ONE JSON object:
  enabled:  {"prompt_id": int, "decision": "weak"|"strong", "confidence": float,
             "mode": "shadow", "engine": {"name": "v1_mf_router", "version": "router-v1-frozen", "mode": "learned"},
             "threshold": 0.30, "ts": "<iso8601>"}
  disabled: {"prompt_id": 0, "decision": "disabled", "confidence": 0.0, "mode": "shadow",
             "engine": {...same...}, "reason": "router disabled by config"}

Kill switch: env ROUTER_CONFIG (default: ./router_config.yaml).
  - file missing  -> disabled (fail closed)
  - enabled: false -> disabled
Never edits router_v1/ ; imports route() read-only. Threshold comes from
config but is validated == 0.30 (the frozen prereg value) or the CLI exits 2.
"""
import json
import os
import sys
from datetime import datetime, timezone

import yaml

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

FROZEN_THRESHOLD = 0.30
ENGINE = {"name": "v1_mf_router", "version": "router-v1-frozen", "mode": "learned"}


def load_config():
    path = os.environ.get("ROUTER_CONFIG", os.path.join(REPO, "router_config.yaml"))
    if not os.path.exists(path):
        return {"enabled": False, "reason": f"config not found: {path}"}
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    r = cfg.get("router", {})
    return {"enabled": bool(r.get("enabled", False)),
            "threshold": r.get("threshold", FROZEN_THRESHOLD)}


def main():
    args = sys.argv[1:]
    prompt = None
    if "--prompt" in args:
        prompt = args[args.index("--prompt") + 1]
    else:
        prompt = sys.stdin.read().strip() or " ".join(args).strip()
    if not prompt:
        print(json.dumps({"error": "empty prompt"}))
        sys.exit(1)

    cfg = load_config()
    base = {"mode": "shadow", "engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat()}
    if not cfg["enabled"]:
        out = {"prompt_id": 0, "decision": "disabled", "confidence": 0.0,
               "reason": cfg.get("reason", "router disabled by config"), **base}
        print(json.dumps(out))
        return

    thr = float(cfg.get("threshold", FROZEN_THRESHOLD))
    if abs(thr - FROZEN_THRESHOLD) > 1e-9:
        # Frozen threshold is not rebalanceable outside a new prereg — fail loud.
        print(json.dumps({"error": f"threshold {thr} != frozen 0.30"}))
        sys.exit(2)

    from router_v1.route import route  # read-only import of the tagged artifact
    decision, conf = route(prompt)
    out = {"prompt_id": 0, "decision": decision, "confidence": conf,
           "threshold": thr, **base}
    print(json.dumps(out))
    # Append-only shadow evidence (best effort; logging failure must not break the call)
    try:
        logdir = os.path.join(REPO, "evidence", "shadow")
        os.makedirs(logdir, exist_ok=True)
        with open(os.path.join(logdir, "shadow_log.jsonl"), "a") as f:
            f.write(json.dumps(out) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
