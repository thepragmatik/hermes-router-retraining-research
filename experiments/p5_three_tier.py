#!/usr/bin/env python3
"""Phase F — P5 three-tier / specialist cascade ($0).

Preregistration: experiments/PREREG_P5.md (frozen f3837b8, before scoring).
Protocol: experiments/PIVOT_PROTOCOL.md (dev-fit first; pivot holdout scored
ONCE only if an arm passes the frozen gate dev-side; test SEALED).

Arms (all on the v1-WEAK stratum; cascade can only act where v1 routes weak):
  C1 two-tier baseline  == v1 itself (weak on v1-weak rows, strong elsewhere)
  C2a three-tier, oracle-arbiter: v1-weak -> Yi; strong call only when Yi
      correct (perfect mid-tier arbiter upper bound)
  C2b three-tier, deployable: v1-weak -> Yi always; strong never (no live
      trigger exists per P4; escalation-to-strong trigger would have to be a
      dead P4 layer)
  C3  always-three-tier, oracle-arbiter: weak+Yi on every row; strong only
      when both wrong
Keep gate vs C1 (frozen): G1 cost arm (cost <= C1-0.0002, acc >= C1-0.002)
  or G2 quality arm (acc >= C1+0.020, cost <= C1+0.0002).

Run: python3 experiments/p5_three_tier.py > results/P5_raw.txt 2>&1
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from p3_internal_confidence import (  # noqa: E402
    WEAK, STRONG, load_train, binarize, md5_bucket,
)
from p1_p2_sampling_verifiers import MID  # noqa: E402

BOOT_N, BOOT_SEED = 1000, 42


def paired_ci(pol, base, seed=BOOT_SEED, n=BOOT_N):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(pol), size=(n, len(pol)))
    d = pol[idx].mean(axis=1) - base[idx].mean(axis=1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    tr = load_train()
    n = len(tr)
    bucket = tr["prompt"].map(lambda p: md5_bucket(p, 42)).to_numpy()
    holdout = bucket < 1500
    dev = ~holdout
    print(f"SECTION 0: train {n} | dev-fit {int(dev.sum())} | "
          f"pivot-holdout {int(holdout.sum())} | test rows loaded: 0 (sealed)")

    y_weak = binarize(tr[WEAK])
    y_mid = binarize(tr[MID])
    y_strong = binarize(tr[STRONG])
    c_w = float(tr[f"{WEAK}|total_cost"].mean())
    c_m = float(tr[f"{MID}|total_cost"].mean())
    c_s = float(tr[f"{STRONG}|total_cost"].mean())
    print(f"stored cost/call: weak ${c_w:.7f} mid ${c_m:.7f} strong ${c_s:.7f}")

    v1m = np.load("results/v1_train_probs.npy") >= 0.30
    assert len(v1m) == n
    v1m = np.asarray(v1m, dtype=bool)

    # C1 = v1 exactly (quality verified in Phase E structural control)
    c1_acc = np.where(v1m, y_strong, y_weak).astype(float)
    c1_cost = c_w + v1m.astype(float) * c_s

    # C2a oracle-arbiter three-tier: on v1-weak rows call Yi; call strong
    # only if Yi correct (perfect arbiter); else weak alone
    y_mid_after_weak = np.where(v1m, y_mid, y_weak)
    c2a_strong = v1m & (y_mid == 1)          # strong replaces Yi when Yi right
    c2a_acc = np.where(c2a_strong,
                       y_strong, y_mid_after_weak).astype(float)
    c2a_cost = c_w + (c_w + c_m) * v1m + c_s * c2a_strong

    # C2b deployable: Yi call added on all v1-weak rows, no strong escalation
    c2b_acc = y_mid_after_weak.astype(float)
    c2b_cost = c_w + (c_w + c_m) * v1m

    # C3 always-three-tier oracle: weak+Yi everywhere; strong iff both wrong
    both_wrong = (y_weak == 0) & (y_mid == 0)
    c3_strong = both_wrong
    c3_acc = np.where(c3_strong, y_strong, np.maximum(y_weak, y_mid)).astype(float)
    c3_cost = (c_w + c_m) + c_s * c3_strong

    def rep(name, acc, cost, mask_slice, note=""):
        pass

    print("\nSECTION 1: dev-fit arms vs C1 (v1)")
    print(f"  C1 v1: acc {float(c1_acc[dev].mean()):.4f} "
          f"cost {float(c1_cost[dev].mean()):.7f}")
    arms = {
        "C2a_oracle_arbiter": (c2a_acc, c2a_cost),
        "C2b_yi_only": (c2b_acc, c2b_cost),
        "C3_always3_oracle": (c3_acc, c3_cost),
    }
    passing = []
    for name, (acc, cost) in arms.items():
        d_a = float(acc[dev].mean()) - float(c1_acc[dev].mean())
        d_c = float(cost[dev].mean()) - float(c1_cost[dev].mean())
        lo_a, hi_a = paired_ci(acc[dev].astype(float), c1_acc[dev])
        lo_c, hi_c = paired_ci(cost[dev].astype(float), c1_cost[dev])
        g1 = (d_c <= -0.0002) and (d_a >= -0.002)
        g2 = (d_a >= 0.020) and (d_c <= 0.0002)
        print(f"  {name:20s} acc {float(acc[dev].mean()):.4f} (d {d_a:+.4f} "
              f"[{lo_a:+.4f},{hi_a:+.4f}]) cost {float(cost[dev].mean()):.7f} "
              f"(d {d_c:+.7f} [{lo_c:+.7f},{hi_c:+.7f}]) "
              f"G1={'PASS' if g1 else 'fail'} G2={'PASS' if g2 else 'fail'}")
        if g1 or g2:
            passing.append(name)
    print(f"  dev-side passing arms: {passing or 'NONE'}")

    if not passing:
        print("\nVERDICT: NO-GO (frozen prereg: no dev-side pass -> no holdout "
              "spend) -> mid tier NOT justified; v1 remains the only layer")
        return 0

    print("\nSECTION 2: PIVOT-HOLDOUT single pass (dev-passing arms only)")
    for name in passing:
        acc, cost = arms[name]
        d_a = float(acc[holdout].mean()) - float(c1_acc[holdout].mean())
        d_c = float(cost[holdout].mean()) - float(c1_cost[holdout].mean())
        lo_a, hi_a = paired_ci(acc[holdout].astype(float), c1_acc[holdout])
        lo_c, hi_c = paired_ci(cost[holdout].astype(float), c1_cost[holdout])
        g1 = (d_c <= -0.0002) and (d_a >= -0.002)
        g2 = (d_a >= 0.020) and (d_c <= 0.0002)
        print(f"  {name:20s} acc {float(acc[holdout].mean()):.4f} "
              f"(d {d_a:+.4f} [{lo_a:+.4f},{hi_a:+.4f}]) cost "
              f"{float(cost[holdout].mean()):.7f} (d {d_c:+.7f} "
              f"[{lo_c:+.7f},{hi_c:+.7f}]) G1={'PASS' if g1 else 'fail'} "
              f"G2={'PASS' if g2 else 'fail'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
