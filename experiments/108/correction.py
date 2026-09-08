#!/usr/bin/env python3
"""Idea 108 Stage 0 — the SINGLE preregistered diagnostic correction (PREREG §8).

Gate 1 failed on the primary run. All three correction diagnostics flagged
(D_label, D_embed, D_len) -> m = 0.5^3 = 0.125. Recompute the weighted-joint arm
with the w_syn grid scaled by m ({0.00625, 0.03125, 0.125}), re-run its frozen CV,
re-evaluate Gate 1 once. No further corrections permitted after this.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loaders import WORKTREE, load_real_train, load_synthetic  # noqa: E402
from pipeline import (BUDGETS, BUDGET_LABELS, LOW_BUDGETS, M_CLS_GRID,  # noqa: E402
                      RESULTS, SEED, cv_joint, fit_logreg, fit_warm,
                      joint_sample_weight, policy_utility, predict_p)

M_MULT = 0.5 ** 3  # three flags: D_label, D_embed, D_len
W_GRID_CORR = [w * M_MULT for w in (0.05, 0.25, 1.0)]


def main():
    syn = load_synthetic()
    tr = load_real_train()
    z = np.load(os.path.join(RESULTS, "emb_cache.npz"))
    emb_real, emb_syn = z["real"], z["syn"]

    y_all = tr.y.to_numpy()
    wc = tr.weak_correct.to_numpy(float)
    sc = tr.strong_correct.to_numpy(float)
    cw = tr.cost_w.to_numpy(float)
    cs = tr.cost_s.to_numpy(float)

    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(tr))
    n_dev = int(round(0.70 * len(tr)))
    dev_idx, eval_idx = perm[:n_dev], perm[n_dev:]
    unt = tr.untied.to_numpy()
    dev_untied = dev_idx[unt[dev_idx]]
    eval_untied = eval_idx[unt[eval_idx]]

    # budget draws identical to the primary run (frozen permutation head)
    budget_rows = {}
    for b, lab in zip(BUDGETS, BUDGET_LABELS):
        k = int(round(b * len(tr)))
        idx = dev_untied[:k]
        n1 = int(y_all[idx].sum())
        budget_rows[lab] = idx if (n1 >= 10 and (k - n1) >= 10) else None

    ys_syn = syn.y_syn.to_numpy()
    label_syn = syn.label.to_numpy()
    we, st = wc[eval_untied], sc[eval_untied]
    cwe, cse = cw[eval_untied], cs[eval_untied]

    out = {"correction": "PREREG section 8, applied ONCE",
           "m_multiplier": M_MULT, "corrected_w_grid": W_GRID_CORR,
           "budgets": {}}
    wins_pre, wins_joint, wins_low_pre, wins_low_joint = 0, 0, 0, 0
    for lab in BUDGET_LABELS:
        idx = budget_rows[lab]
        if idx is None:
            out["budgets"][lab] = {"valid": False}
            continue
        Xr, yr = emb_real[idx], y_all[idx]
        clf_r = fit_logreg(Xr, yr)
        U_r, q_r, c_r = policy_utility(predict_p(clf_r, emb_real[eval_untied]),
                                       we, st, cwe, cse)
        # corrected joint
        w_sel, m_sel, ll4 = cv_joint(Xr, yr, emb_syn, ys_syn, label_syn,
                                     m_cls_grid=M_CLS_GRID)
        # cv_joint uses the frozen global grid; rescale selected weight by m
        w_corr = w_sel * M_MULT
        sw = joint_sample_weight(len(yr), len(ys_syn), w_corr, m_sel, label_syn)
        clf_j = fit_logreg(np.vstack([Xr, emb_syn]),
                           np.concatenate([yr, ys_syn]), sample_weight=sw)
        U_j, q_j, c_j = policy_utility(predict_p(clf_j, emb_real[eval_untied]),
                                       we, st, cwe, cse)
        # corrected pretrain = same arm 3 (correction touches only the joint arm)
        warm = fit_logreg(emb_syn, ys_syn)
        clf_p = fit_warm(Xr, yr, warm)
        U_p, q_p, c_p = policy_utility(predict_p(clf_p, emb_real[eval_untied]),
                                       we, st, cwe, cse)
        du_p, du_j = U_p - U_r, U_j - U_r
        wins_pre += du_p > 0
        wins_joint += du_j > 0
        low = lab in LOW_BUDGETS
        wins_low_pre += (du_p > 0) and low
        wins_low_joint += (du_j > 0) and low
        out["budgets"][lab] = {
            "valid": True, "w_sel_pre": w_sel, "w_corrected": w_corr,
            "m_cls_sel": m_sel,
            "U_real": U_r, "U_pretrain": U_p, "U_joint_corrected": U_j,
            "dU_pretrain": du_p, "dU_joint_corrected": du_j,
            "q_real": q_r, "q_joint_corrected": q_j,
            "c_real": c_r, "c_joint_corrected": c_j,
        }
        print(lab, json.dumps(out["budgets"][lab]), flush=True)

    out["wins_pretrain"] = int(wins_pre)
    out["wins_joint_corrected"] = int(wins_joint)
    out["wins_low_pretrain"] = int(wins_low_pre)
    out["wins_low_joint_corrected"] = int(wins_low_joint)
    out["gate1_after_correction"] = {
        "wins_best_arm": int(max(wins_pre, wins_joint)),
        "wins_low_best_arm": int(max(wins_low_pre, wins_low_joint)),
        "note": "wins counted over 4 valid budgets (0.5% invalid: 9 negatives < 10)",
    }
    g = json.load(open(os.path.join(RESULTS, "stage0_gate.json")))
    g["gate1"]["correction_applied"] = True
    g["gate1"]["correction_result"] = out
    json.dump(g, open(os.path.join(RESULTS, "stage0_gate.json"), "w"),
              indent=1, default=str)
    print("correction result appended to stage0_gate.json")


if __name__ == "__main__":
    main()
