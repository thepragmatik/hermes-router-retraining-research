"""Idea 102 Stage 0: policy construction, lambda sweep, support/fallback (T014,
T015). Margin = 0 (prereg); unsupported rows fall back to the frozen V1
decision (FR-008). Policies emit the FR-007 fields.
"""
import numpy as np

from data import ESS_MIN_FRAC, LAMBDA_GRID, OVERLAP_MIN, V1_THRESHOLD
from simulate import deciles


def v1_decision(p):
    return p >= V1_THRESHOLD


def policy_support(p_eval, dec_eval, strong_fit_by_decile, e_min_eval):
    """Per-row support flags (frozen thresholds): overlap < 0.09, stratum
    ESS/n < 0.05, decile with < 100 fit-side logged strong samples."""
    ess_frac_by_dec = np.zeros(len(strong_fit_by_decile))
    n_by_dec = np.array([(dec_eval == k).sum() for k in range(len(strong_fit_by_decile))])
    ess_frac_by_dec = strong_fit_by_decile / np.maximum(n_by_dec, 1)
    low_ess_dec = ess_frac_by_dec < ESS_MIN_FRAC
    low_cnt_dec = strong_fit_by_decile < 100
    low_ess = low_ess_dec[dec_eval]
    low_cnt = low_cnt_dec[dec_eval]
    low_overlap = e_min_eval < OVERLAP_MIN
    unsupported = low_overlap | low_ess | low_cnt
    return unsupported, {"overlap_fail": int(low_overlap.sum()),
                         "ess_fail": int(low_ess.sum()),
                         "count_fail": int(low_cnt.sum()),
                         "ess_frac_by_decile": ess_frac_by_dec.tolist()}


def route_from_score(score_strong, lam, dcost, fallback_mask, v1_mask_eval,
                     eval_mask=None):
    """route_strong = tau_hat - lam*dcost > 0 (margin 0); unsupported rows take
    the V1 decision. `dcost` may be full-length (indexed via eval_mask) or
    already eval-length. Returns (route_strong, utility) with FR-007 fields."""
    dcost = np.asarray(dcost, float)
    if eval_mask is not None and dcost.shape != np.asarray(score_strong).shape:
        dcost = dcost[eval_mask]
    route = (score_strong - lam * dcost) > 0
    route = np.where(fallback_mask, v1_mask_eval, route)
    utility = score_strong - lam * dcost
    return route.astype(bool), utility


def policy_metrics(route, d, eval_mask):
    """route is eval-length; q/c columns are full-length and indexed here so
    every reported metric is a within-eval mean (never a surface-share-weighted
    total)."""
    q_weak, q_strong = d["q_weak"][eval_mask], d["q_strong"][eval_mask]
    c_weak, c_strong = d["c_weak"][eval_mask], d["c_strong"][eval_mask]
    route = np.asarray(route, bool)
    q = np.where(route, q_strong, q_weak)
    c = np.where(route, c_strong, c_weak)
    n = int(eval_mask.sum())
    assert len(route) == n, (len(route), n)
    return {"Q": float(q.mean()),
            "C": float(c.mean()),
            "frac_strong": float(route.mean()),
            "n": n}


def lambda_sweep(score_strong, d, eval_mask, dcost, fallback_mask,
                 v1_mask_eval, lam_grid=LAMBDA_GRID):
    rows = []
    for lam in lam_grid:
        route, _ = route_from_score(score_strong, lam, dcost,
                                    fallback_mask, v1_mask_eval,
                                    eval_mask=eval_mask)
        m = policy_metrics(route, d, eval_mask)
        m["lambda"] = lam
        m["fallback_frac"] = float(fallback_mask.mean())
        rows.append(m)
    return rows
