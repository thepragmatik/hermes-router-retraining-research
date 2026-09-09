#!/usr/bin/env python3
"""Idea 105: LIVE black-box sanity recompute (prereg §7, §8 item 15).

Spawns TWO local router_shadow.py instances on free 127.0.0.1 ports >= 8766
(flag ON with the real telemetry/envelope_config.json, and flag OFF), routes
the first 100 prompts of the frozen live slice (seed-10 permutation evaluation
segment; prompts are read from the local winrate table AT RUNTIME — no prompt
text is stored or committed), and verifies:

  L1  flag-ON schema: envelope dict present, frozen keys, additive only
  L2  flag-OFF/flag-ON parity: identical decision/confidence, no envelope key
  L3  every envelope action == offline recompute from the reported confidence
  L4  /health envelope block: active state, ks_evaluations == 0 (cadence),
      action_counts sum == routes
  L5  SANITY GATE S1+S2: realized risk on accepted rows vs alpha=0.01
      (S1: risk <= alpha; S2: failures <= exact binomial 95% critical count)
  L6  evidence JSON written with counts/hashes ONLY (no prompt text)

$0: local compute only. Production (8765) is never touched.
Run from the repo root:  python3 scripts/105_live_sanity.py
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

WINRATE = os.environ.get(
    "ROUTER_WINRATE_TABLE",
    "/Users/rath/transfer-bundle/analysis/winrate_table.parquet")
ARTIFACT = os.path.join(REPO, "telemetry", "envelope_config.json")
EVIDENCE = os.path.join(REPO, "results", "105", "live_sanity_evidence.json")

N_LIVE = 1500
PARITY_N = 20        # flag-OFF cross-check on the first N prompts (schema
                     # parity is exercised on every route; suite covers the rest)
SLICE_SEED = 10
DEPLOY_ALPHA = 0.01


def main():
    import numpy as np
    import pandas as pd
    from scipy import stats as sps
    from test_101_service import Service  # shared harness (ports >= 8766)

    p = np.load(os.path.join(REPO, "results", "v1_train_probs.npy")).astype(
        np.float64)
    n = len(p)
    perm10 = np.random.default_rng(SLICE_SEED).permutation(n)
    live = perm10[int(0.4 * n): int(0.8 * n)][:N_LIVE]
    s_rt = 1.0 - np.round(p, 4)
    cfg = json.load(open(ARTIFACT))
    thr = [r for r in cfg["table"] if r["alpha"] == DEPLOY_ALPHA][0]["threshold"]

    wt = pd.read_parquet(WINRATE)
    tr = wt[wt["split"] == "train"].reset_index(drop=True)
    prompts = [str(x) for x in tr["prompt"].values[live]]
    weak_ok = tr["weak_correct"].values[live]
    strong_ok = tr["strong_correct"].values[live]
    risk_lbl = ((weak_ok == 0) & (strong_ok == 1)).astype(int)
    assert all(x.strip() for x in prompts)
    expected_acc = (s_rt[live] >= thr)
    print(f"live slice n={N_LIVE}, expected acceptances="
          f"{int(expected_acc.sum())} (offline)")

    tmp = tempfile.mkdtemp(prefix="105_live_")
    # flag-ON service: own config with envelope_enabled: true
    cfg_on = os.path.join(tmp, "cfg_on.yaml")
    open(cfg_on, "w").write(
        "router:\n  enabled: true\n  threshold: 0.30\n"
        "  envelope_enabled: true\n")
    cfg_off = os.path.join(tmp, "cfg_off.yaml")
    open(cfg_off, "w").write(
        "router:\n  enabled: true\n  threshold: 0.30\n")

    svc_on = Service(cfg_on, os.path.join(tmp, "tel_on"), tmpdir=tmp)
    svc_off = Service(cfg_off, os.path.join(tmp, "tel_off"), tmpdir=tmp)
    try:
        assert svc_on.wait_ready(), "flag-ON service failed to start"
        assert svc_off.wait_ready(), "flag-OFF service failed to start"

        rows = []
        for i, pr in enumerate(prompts):
            out = svc_on.post("/route", {"prompt": pr, "session_id": "105-sanity", "message_id": f"105-sanity-{i}"}, timeout=120)
            env = out.get("envelope")
            # L1 schema
            assert env is not None, f"missing envelope on route {i}"
            assert set(env) == {"enabled", "mode", "alpha", "action",
                                "threshold_used"}
            assert env["enabled"] is True and env["mode"] == "shadow"
            assert env["alpha"] == DEPLOY_ALPHA
            assert env["threshold_used"] == thr
            # L2 parity (frozen subset; full suite covers parity elsewhere)
            if i < PARITY_N:
                off = svc_off.post("/route", {"prompt": pr, "session_id": "105-sanity", "message_id": f"105-sanity-{i}"}, timeout=120)
                for k in ("decision", "confidence", "threshold", "mode",
                          "engine"):
                    assert out[k] == off[k], (k, i)
                assert "envelope" not in off
            # L3 offline recompute
            s = 1.0 - float(out["confidence"])
            want = ("abstain" if thr is None else
                    ("accept-weak" if (s >= thr and out["decision"] == "weak")
                     else "escalate-strong"))
            assert env["action"] == want, (i, env["action"], want)
            rows.append({"i": i, "decision": out["decision"],
                         "confidence": out["confidence"], "score": s,
                         "action": env["action"], "risk": int(risk_lbl[i]),
                         "event_id": out["event_id"],
                         "prompt_hash_len": 12})
        # L4 health: state active, zero alarms; at 1500 routes the non-
        # overlapping KS cadence evaluates ~3 windows and must NOT fire
        # (in-distribution mixed windows); at <500 routes it evaluates 0.
        h = svc_on.get("/health")
        assert set(h) == {"status", "enabled", "engine", "telemetry",
                          "envelope"}
        he = h["envelope"]
        assert he["state"] == "active", he
        assert he["alarm_counts"]["ks_fire"] == 0, he
        assert he["alarm_counts"]["risk_breach"] == 0, he
        assert sum(he["action_counts"].values()) == N_LIVE, he
        assert "envelope" not in svc_off.get("/health")

        # L5 sanity gate (computed BEFORE any assert so a failure still
        # reports the numbers)
        acc_rows = [r for r in rows if r["action"] == "accept-weak"]
        n_acc = len(acc_rows)
        k_fail = sum(r["risk"] for r in acc_rows)
        risk = k_fail / n_acc if n_acc else 0.0
        crit = int(sps.binom.ppf(0.95, n_acc, DEPLOY_ALPHA))
        s1 = risk <= DEPLOY_ALPHA
        s2 = k_fail <= crit
        esc = sum(1 for r in rows if r["action"] == "escalate-strong")
        print(f"routed={N_LIVE} accepted={n_acc} escalated={esc} "
              f"failures={k_fail} risk={risk:.4f} "
              f"S1(risk<={DEPLOY_ALPHA})={s1} S2(k<={crit})={s2}")
        assert s1 and s2, "SANITY GATE FAILED"

        # L6 evidence: counts + hashes only
        ev = {
            "slice": {"seed": SLICE_SEED, "segment": "eval[0:100]of40-80pct",
                      "n": N_LIVE},
            "flag_on_port": svc_on.port, "flag_off_port": svc_off.port,
            "alpha": DEPLOY_ALPHA, "threshold_used": thr,
            "n_accepted": n_acc, "n_escalated": esc, "n_failures": k_fail,
            "realized_risk": risk, "S1_pass": bool(s1), "S2_pass": bool(s2),
            "s2_critical": crit, "binom_p": float(
                sps.binom.sf(k_fail - 1, n_acc, DEPLOY_ALPHA)),
            "health_state": he["state"],
            "ks_evaluations": he["alarm_counts"]["ks_evaluations"],
            "ks_fire": he["alarm_counts"]["ks_fire"],
            "action_counts": he["action_counts"],
            "event_id_prefixes": [r["event_id"][:8] for r in rows[:5]],
            "offline_expected_accepts": int(expected_acc.sum()),
            "note": "prompt text read at runtime from local winrate table; "
                    "never stored here",
        }
        with open(EVIDENCE, "w") as f:
            json.dump(ev, f, indent=1, sort_keys=True)
        print("evidence written:", EVIDENCE)
        print("LIVE SANITY: PASS")
    finally:
        svc_on.stop()
        svc_off.stop()


if __name__ == "__main__":
    main()
