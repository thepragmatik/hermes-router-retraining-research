#!/usr/bin/env python3
"""Phase B1 — reproduce the historical router baselines from stored labels.

Reproduces (val split, frozen numbers from deployment_threshold.md / phase0):
  weak acc 0.2289, strong acc 0.6448, always-strong APGR 0.6459,
  router v1 (tag router-v1-frozen) at threshold 0.30: routed acc 0.6395,
  frac_strong 0.7686, PGR 0.9874.

APGR/PGR definitions (same as eval_apgr.py in the source bundle):
  PGR   = (routed_acc - weak_acc) / (strong_acc - weak_acc)
  APGR  = area under the threshold sweep of PGR (201 points, 0.00..1.00)

Data: ~/transfer-bundle/analysis/mf_val_frame.parquet + mf_val_probs.npy
(validation split ONLY; test split never loaded). $0 spend.

Run: python3 experiments/b1_baseline_repro.py > results/B1_BASELINE_REPRO_raw.txt
"""
import os

import numpy as np
import pandas as pd

THRESHOLDS = np.linspace(0.0, 1.0, 201)
V1_THRESHOLD = 0.30

TOL = {
    "weak_acc": 0.005,      # recorded 0.2289
    "strong_acc": 0.005,    # recorded 0.6448
    "always_strong_apgr": 0.02,   # recorded 0.6459
    "v1_routed_acc": 0.02,        # recorded 0.6395
    "v1_frac_strong": 0.02,       # recorded 0.7686
    "v1_pgr": 0.02,               # recorded 0.9874
}


def main():
    frame = pd.read_parquet(
        os.path.expanduser("~/transfer-bundle/analysis/mf_val_frame.parquet"))
    probs = np.load(
        os.path.expanduser("~/transfer-bundle/analysis/mf_val_probs.npy"))
    assert len(frame) == len(probs), "frame/probs length mismatch"
    assert "strong_correct" in frame and "weak_correct" in frame

    weak = frame.weak_correct.to_numpy(float)
    strong = frame.strong_correct.to_numpy(float)
    weak_acc, strong_acc = weak.mean(), strong.mean()
    gap = strong_acc - weak_acc

    # APGR per eval_apgr.py: trapezoid of PGR over the CALL-FRACTION axis
    # (ascending), not over the threshold axis — threshold order is not
    # monotone in call fraction.
    pgrs, calls = [], []
    for a in THRESHOLDS:
        use = probs >= a
        routed = np.where(use, strong, weak)
        pgrs.append((routed.mean() - weak_acc) / gap)
        calls.append(float(use.mean()))
    order = np.argsort(calls)
    always_strong_apgr = float(np.trapezoid(
        np.array(pgrs)[order], np.array(calls)[order]))

    v1_mask = probs >= V1_THRESHOLD
    v1_routed = np.where(v1_mask, strong, weak)
    v1_routed_acc = float(v1_routed.mean())
    v1_frac_strong = float(v1_mask.mean())
    v1_pgr = (v1_routed_acc - weak_acc) / gap

    recorded = {
        "weak_acc": 0.2289, "strong_acc": 0.6448,
        "always_strong_apgr": 0.6459, "v1_routed_acc": 0.6395,
        "v1_frac_strong": 0.7686, "v1_pgr": 0.9874,
    }
    measured = {
        "weak_acc": float(weak_acc), "strong_acc": float(strong_acc),
        "always_strong_apgr": always_strong_apgr,
        "v1_routed_acc": v1_routed_acc, "v1_frac_strong": v1_frac_strong,
        "v1_pgr": float(v1_pgr),
    }

    print(f"n_val = {len(frame)}")
    print(f"{'metric':24s} {'recorded':>9s} {'measured':>9s} {'abs_diff':>9s}  verdict")
    all_ok = True
    for k in recorded:
        diff = abs(measured[k] - recorded[k])
        ok = diff <= TOL[k]
        all_ok &= ok
        print(f"{k:24s} {recorded[k]:9.4f} {measured[k]:9.4f} {diff:9.4f}  "
              f"{'OK' if ok else 'FAIL'}")
    print("BASELINE_REPRO:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
