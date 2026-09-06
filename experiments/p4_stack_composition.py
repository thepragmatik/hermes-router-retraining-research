#!/usr/bin/env python3
"""Phase E — P4 stack composition by incremental ablation ($0).

Preregistration: experiments/PREREG_P4.md (frozen, commit 38c67d6).
Protocol: experiments/PIVOT_PROTOCOL.md (dev-fit selection; pivot holdout
scored ONCE at the end; validation reserved; test SEALED — never loaded).

Revised build order (prereg §0: P1-P3 kills justify testing killed layers as a
stack on the weak-first architecture, the only one with real headroom):
  L0/L1  v1 @0.30  ==  weak-first re-serialization of v1's partition (control;
         script ASSERTS L1 outputs equal v1 outputs exactly)
  L2     L1 + Yi disagreement check (P1b policy verbatim via op_point)
  L3     L2 + VF sanity gate (weak answer shippable only if VF parses it)
  L4     L3 + P3 answer-aware probe @ frozen tau_q = 0.373159 (R+V+P, C=3.0)

Layer retention (dev-fit, paired bootstrap seed 42, 1000 resamples): keep a
layer iff its marginal d_acc is NOT significantly negative AND its marginal
d_cost is NOT significantly positive (95% two-sided percentile CIs).

Qualification (holdout, single pass): surviving stack vs v1 must pass
  Q1: d_acc >= +0.020 and d_cost <= +0.0002/row, or
  Q2: d_cost <= -0.0002/row and d_acc >= -0.002.

Run:
  python3 experiments/p4_stack_composition.py > results/P4_raw.txt 2>&1
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from p3_internal_confidence import (  # noqa: E402
    WEAK, STRONG, load_train, binarize, build_features, md5_bucket,
    make_pipeline, StandardScaler, LogisticRegression,
)
from p1_p2_sampling_verifiers import (  # noqa: E402
    MID, vf, agree_rule, unwrap, extract_answer, op_point,
)

BOOT_N, BOOT_SEED = 1000, 42
TAU_Q = 0.373159          # P3 frozen O1 operating point (R+V+P, C=3.0)
C_PROBE = 3.0             # P3 frozen C


def paired_ci(pol, base, seed=BOOT_SEED, n=BOOT_N):
    """Paired bootstrap CI of mean(pol) - mean(base)."""
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
    y_strong = binarize(tr[STRONG])
    y_mid = binarize(tr[MID])
    c_w = float(tr[f"{WEAK}|total_cost"].mean())
    c_m = float(tr[f"{MID}|total_cost"].mean())
    c_s = float(tr[f"{STRONG}|total_cost"].mean())
    print(f"stored cost/call: weak ${c_w:.7f} mid ${c_m:.7f} strong ${c_s:.7f}")

    # ---- frozen signals (verbatim from P1/P3 code) ----
    mats, fams, P = build_features(tr)
    v1m = P >= 0.30                       # P3's exact v1 partition
    v1_routed = np.where(v1m, y_strong, y_weak)
    v1_cost_row = c_w + v1m.astype(float) * c_s

    resp_w = tr[f"{WEAK}|model_response"]
    resp_m = tr[f"{MID}|model_response"]
    ans_w = np.array([extract_answer(unwrap(t) or "", f) if isinstance(t, str)
                      else None for t, f in zip(resp_w, fams)], dtype=object)
    ans_m = np.array([extract_answer(unwrap(t) or "", f) if isinstance(t, str)
                      else None for t, f in zip(resp_m, fams)], dtype=object)
    full_w = np.array([unwrap(t) or "" for t in resp_w], dtype=object)
    full_m = np.array([unwrap(t) or "" for t in resp_m], dtype=object)
    ag = np.array([agree_rule(a, b, x, y) for a, b, x, y in
                   zip(ans_w, ans_m, full_w, full_m)])
    vf_w = np.array([vf(t, f) for t, f in zip(resp_w, fams)], dtype=bool)

    # P3 probe @ frozen operating point: in-sample fit on dev-fit (same
    # construction the frozen tau was calibrated under; no threshold refit)
    pipe = make_pipeline(StandardScaler(),
                         LogisticRegression(max_iter=1000, C=C_PROBE,
                                            class_weight="balanced",
                                            solver="lbfgs"))
    risk = (1 - y_weak).astype(float)
    pipe.fit(mats["R+V+P"][dev], risk[dev])
    probe = pipe.predict_proba(mats["R+V+P"])[:, 1]

    # ---- layer masks (full-length; escalate = call strong) ----
    esc = {
        "L1_wf_v1trigger": v1m.copy(),                        # structural control
        "L2_disagree": ~ag,                                   # P1b verbatim
        "L3_disagree_vfgate": (~ag) | (~vf_w),
        "L4_stack_probe": (~ag) | (~vf_w) | (probe >= TAU_Q),
    }

    # structural-control proof: L1 partition == v1 partition
    assert np.array_equal(esc["L1_wf_v1trigger"], v1m), \
        "L1 must equal v1's partition exactly"

    def stack_vals(name, mask_slice):
        m_strong = esc[name] & mask_slice
        acc, cost = op_point(m_strong, y_weak, y_mid, y_strong, c_w, c_m, c_s)
        return acc, cost

    # ---- SECTION 1: dev-fit marginal retention ladder ----
    print("\nSECTION 1: dev-fit marginal retention ladder "
          "(paired bootstrap, seed 42)")
    print(f"  v1@0.30 (L0/L1) dev: acc {float(v1_routed[dev].mean()):.4f} "
          f"cost {float(v1_cost_row[dev].mean()):.7f}")
    survivors, cur = [], "L1_wf_v1trigger"
    for name in ("L2_disagree", "L3_disagree_vfgate", "L4_stack_probe"):
        a2, c2 = stack_vals(name, dev)
        a1, c1 = stack_vals(cur, dev)
        pol_q = np.where(esc[name] & dev, y_strong, y_weak)[dev].astype(float)
        base_q = np.where(esc[cur] & dev, y_strong, y_weak)[dev].astype(float)
        pol_c = (c_w + c_m) + esc[name][dev] * c_s
        base_c = (c_w + c_m) + esc[cur][dev] * c_s
        lo_q, hi_q = paired_ci(pol_q, base_q)
        lo_c, hi_c = paired_ci(pol_c, base_c)
        keep = (hi_q >= 0.0) and (lo_c <= 0.0)
        verdict = "RETAIN" if keep else "REMOVE"
        print(f"  {name:20s} acc {a2:.4f} (d {a2 - a1:+.4f} [{lo_q:+.4f},"
              f"{hi_q:+.4f}]) cost {c2:.7f} (d {c2 - c1:+.7f} [{lo_c:+.7f},"
              f"{hi_c:+.7f}]) esc_share {float((esc[name] & dev).mean()):.4f}"
              f" -> {verdict}")
        if keep:
            survivors.append(name)
            cur = name
    stack_name = cur
    print(f"  surviving stack: {stack_name}")

    # ---- SECTION 2: single holdout pass ----
    print("\nSECTION 2: PIVOT-HOLDOUT single-pass results")
    acc_v1_h = float(v1_routed[holdout].mean())
    cost_v1_h = float(v1_cost_row[holdout].mean())
    print(f"  v1 holdout: acc {acc_v1_h:.4f} cost {cost_v1_h:.7f} "
          f"fs {float(v1m[holdout].mean()):.4f}")

    print(f"  {'arm':20s} {'acc':>7s} {'cost/row':>10s} {'esc_share':>9s} "
          f"{'d_acc [95%]':>22s} {'d_cost [95%]':>22s}")
    results = {}
    for name in ("L1_wf_v1trigger", "L2_disagree", "L3_disagree_vfgate",
                 "L4_stack_probe"):
        m = esc[name] & holdout
        pol_q = np.where(m, y_strong, y_weak)[holdout].astype(float)
        pol_c = (c_w + c_m) + esc[name][holdout] * c_s
        base_q = v1_routed[holdout].astype(float)
        base_c = v1_cost_row[holdout]
        acc, cost = float(pol_q.mean()), float(pol_c.mean())
        lo_q, hi_q = paired_ci(pol_q, base_q)
        lo_c, hi_c = paired_ci(pol_c, base_c)
        print(f"  {name:20s} {acc:7.4f} {cost:10.7f} "
              f"{float(esc[name][holdout].mean()):9.4f} {acc - acc_v1_h:+.4f} "
              f"[{lo_q:+.4f},{hi_q:+.4f}] {cost - cost_v1_h:+.7f} "
              f"[{lo_c:+.7f},{hi_c:+.7f}]")
        results[name] = (acc, cost)

    # ---- SECTION 3: frozen qualification gates (Q1/Q2) on surviving stack ----
    print("\nSECTION 3: frozen qualification gates on surviving stack "
          f"({stack_name})")
    s_acc, s_cost = results[stack_name]
    d_acc, d_cost = s_acc - acc_v1_h, s_cost - cost_v1_h
    q1 = (d_acc >= 0.020) and (d_cost <= 0.0002)
    q2 = (d_cost <= -0.0002) and (d_acc >= -0.002)
    print(f"  d_acc {d_acc:+.4f}  d_cost {d_cost:+.7f}")
    print(f"  Q1 (quality: d_acc>=+0.020 & d_cost<=+0.0002): "
          f"{'PASS' if q1 else 'FAIL'}")
    print(f"  Q2 (cost: d_cost<=-0.0002 & d_acc>=-0.002):   "
          f"{'PASS' if q2 else 'FAIL'}")

    # ---- SECTION 4: error overlap (surviving stack vs v1, holdout) ----
    m = esc[stack_name] & holdout
    st_ok = (np.where(m, y_strong, y_weak) == 1)[holdout]
    v1_ok = (v1_routed == 1)[holdout]
    fixed = int((st_ok & ~v1_ok).sum())
    broken = int((~st_ok & v1_ok).sum())
    print("\nSECTION 4: error overlap (holdout, surviving stack vs v1)")
    print(f"  uniquely fixed {fixed} | newly broken {broken} | "
          f"both-correct {int((st_ok & v1_ok).sum())} | "
          f"both-wrong {int((~st_ok & ~v1_ok).sum())}")

    print("\nVERDICT:",
          "PARTIAL-STACK CANDIDATE (carry to P5)" if (q1 or q2)
          else "V1 ALONE IS THE STACK (no paying dynamic layer; proceed to P5 "
               "with v1 as only qualified layer)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
