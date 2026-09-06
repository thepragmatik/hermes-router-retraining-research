"""Shadow A/B replay: router-on vs router-off on the 3626-row val frame using
RECORDED outcomes — zero API spend. NEVER touches mf_test_frame.parquet (sealed).
Arms: v1@0.30 | always_strong | always_weak | random@cost-parity | oracle.
Writes evidence/ab/shadow_ab_results.json. --sweep also writes
evidence/ab/threshold_sweep.csv (analysis only; deployed threshold stays 0.30).

First run computes the decision cache (~8 min, model load + 3626 route() calls);
all later runs are instant. Run long first pass with: background=true, notify=true.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
VAL = Path.home() / "transfer-bundle/analysis/mf_val_frame.parquet"
OUT = REPO / "evidence/ab"
CACHE = OUT / "val_decisions.npz"
FROZEN = 0.30
N_BOOT, SEED = 10000, 42


def load_outcomes():
    df = pd.read_parquet(VAL)
    assert len(df) == 3626, f"expected 3626 val rows, got {len(df)}"
    return df


def strong_weak_cost(df):
    s = (df["strong_correct"].fillna(0).astype(int) == 1).to_numpy()
    w = (df["weak_correct"].fillna(0).astype(int) == 1).to_numpy()
    return s, w, df["cost_s"].to_numpy(float), df["cost_w"].to_numpy(float)


def decisions_with_conf(df, cache=CACHE):
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return z["decisions"], z["confs"]
    from router_v1.route import route  # deferred import: model load only when needed
    dec, con = [], []
    for p in df["prompt"]:
        d, c = route(p)
        dec.append(d)
        con.append(c)
    dec, con = np.array(dec), np.array(con, dtype=float)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, decisions=dec, confs=con)
    return dec, con


def simulate(df, decisions):
    decisions = np.asarray(decisions)
    s, w, cs, cw = strong_weak_cost(df)
    is_strong = decisions == "strong"
    correct = np.where(is_strong, s, w)
    cost = np.where(is_strong, cs, cw)
    return {"acc": float(correct.mean()), "frac_strong": float(is_strong.mean()),
            "cost_mean": float(cost.mean()), "n": int(len(df))}


def oracle_acc(df):
    s, w, _, _ = strong_weak_cost(df)
    return float(np.maximum(s, w).mean())


def random_decisions(df, frac, seed):
    rng = np.random.default_rng(seed)
    d = np.array(["weak"] * len(df), dtype=object)
    d[rng.choice(len(df), size=int(round(frac * len(df))), replace=False)] = "strong"
    return d


def cost_parity_frac(cost_s_mean, cost_w_mean, target_cost_mean):
    return (target_cost_mean - cost_w_mean) / (cost_s_mean - cost_w_mean)


def paired_bootstrap_delta(df, dec_a, dec_b, n_boot=N_BOOT, seed=SEED):
    s, w, _, _ = strong_weak_cost(df)
    ca = np.where(np.asarray(dec_a) == "strong", s, w).astype(float)
    cb = np.where(np.asarray(dec_b) == "strong", s, w).astype(float)
    delta = ca - cb
    rng = np.random.default_rng(seed)
    boots = np.array([delta[rng.integers(0, len(delta), len(delta))].mean()
                      for _ in range(n_boot)])
    return [round(float(np.percentile(boots, 2.5)), 4),
            round(float(np.percentile(boots, 97.5)), 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_outcomes()
    dec, conf = decisions_with_conf(df)
    frozen_dec = np.where(conf >= FROZEN, "strong", "weak")
    if not (frozen_dec == dec).all():
        print("WARNING: route() decisions differ from conf>=0.30 rule; using route() "
              "output for arm A and recording the mismatch in the memo", file=sys.stderr)
    weak = np.array(["weak"] * len(df))
    strong = np.array(["strong"] * len(df))
    a = simulate(df, dec)
    parity = cost_parity_frac(df["cost_s"].mean(), df["cost_w"].mean(), a["cost_mean"])
    rand = random_decisions(df, parity, SEED)
    results = {
        "n": len(df),
        "router_v1_030": a,
        "always_strong": simulate(df, strong),
        "always_weak": simulate(df, weak),
        "random_at_cost_parity": {"frac_strong_target": round(float(parity), 4),
                                  **simulate(df, rand)},
        "oracle_acc": oracle_acc(df),
        "bootstrap_ci_router_vs_always_weak": paired_bootstrap_delta(df, dec, weak),
        "bootstrap_ci_router_vs_random_parity": paired_bootstrap_delta(df, dec, rand),
        "bootstrap_ci_router_vs_always_strong": paired_bootstrap_delta(df, dec, strong),
    }
    results["acceptance"] = {
        "A1_replay_matches_frozen": (abs(a["acc"] - 0.6395) <= 0.0002
                                     and abs(a["frac_strong"] - 0.7686) <= 0.0002),
        "A2_ci_low_vs_always_weak_gt0": results["bootstrap_ci_router_vs_always_weak"][0] > 0,
        "A3_ci_low_vs_random_parity_gt0": results["bootstrap_ci_router_vs_random_parity"][0] > 0,
        "A4_headroom_oracle_minus_router": round(results["oracle_acc"] - a["acc"], 4),
        # A5-A7 live outside this script (latency bench, chaos checks, sha check)
    }
    (OUT / "shadow_ab_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if args.sweep:
        rows = []
        for t in np.arange(0.05, 0.96, 0.05):
            t = round(float(t), 2)
            rows.append({"threshold": t, **simulate(df, np.where(conf >= t, "strong", "weak"))})
        pd.DataFrame(rows).to_csv(OUT / "threshold_sweep.csv", index=False)
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
