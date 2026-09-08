"""Idea 102 Stage 0: policy-value estimators for Gate 2 (cross-fitted DR policy
value; full-feedback-honest), paired bootstrap, decile diagnostics, gate
evaluation (T017, T020, T021)."""
import numpy as np

from data import (BOOT_N, BOOT_SEED, G1_TOL, G1_TRIPWIRE, G2_MIN_SEEDS,
                  G3_C_BAR, G3_MATER_Q, G3_Q_BAR, GATES, LAMBDA_GRID)
from nuisance import folds_for, N_FOLDS, ridge_fit, ridge_predict
from simulate import assert_props


def ess(w):
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum()) if w.sum() > 0 else 0.0


def dr_policy_value(pi1, a, y, e1, mu0, mu1, idx):
    """Cross-fitted DR value of policy pi (pi1 = P(strong|x)) on rows idx using
    OOF nuisances mu0/mu1 (arrays aligned to logged rows), exact e1."""
    pi1 = np.clip(np.asarray(pi1, float), 0.0, 1.0)
    pi0 = 1.0 - pi1
    a_i, y_i = np.asarray(a)[idx], np.asarray(y)[idx]
    e1_i = assert_props(np.asarray(e1)[idx])
    mu0_i, mu1_i = mu0[idx], mu1[idx]
    e_chosen_i = np.where(a_i == 1, e1_i, 1.0 - e1_i)
    w = np.where(a_i == 1, pi1[idx] / e1_i, pi0[idx] / (1.0 - e1_i))
    mu_a_i = np.where(a_i == 1, mu1_i, mu0_i)
    contrib = pi0[idx] * mu0_i + pi1[idx] * mu1_i
    dr = contrib + w * (y_i - mu_a_i)
    val = float(dr.mean())
    se = float(np.sqrt(dr.var(ddof=1) / len(dr)))
    return val, se, w


def paired_bootstrap(dq, dc, n=BOOT_N, seed=BOOT_SEED):
    rng = np.random.default_rng(seed)
    dq, dc = np.asarray(dq, float), np.asarray(dc, float)
    m = len(dq)
    out = []
    for _ in range(n):
        i = rng.integers(0, m, m)
        out.append((dq[i].mean(), dc[i].mean()))
    out = np.array(out)
    lo_q, hi_q = np.quantile(out[:, 0], [0.025, 0.975])
    lo_c, hi_c = np.quantile(out[:, 1], [0.025, 0.975])
    return {"dq_ci": [float(lo_q), float(hi_q)], "dc_ci": [float(lo_c), float(hi_c)]}


def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    denom = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / denom) if denom > 0 else 0.0


def best_lambda(frontier_rows, q_v1, c_v1):
    """Frozen best-lambda rule: argmax mean (Q - Q_V1) subject to mean
    (C - C_V1) <= 0; ties -> lowest lambda, then lowest frac_strong."""
    cands = [r for r in frontier_rows if r["C"] <= c_v1 + 1e-12]
    if not cands:
        return None
    key = lambda r: (round(r["Q"], 12), -r["lambda"], -r["frac_strong"])
    return max(cands, key=key)
