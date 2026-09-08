"""Idea 102 Stage 0: DR pseudo-outcome learner + comparators (T011, T013).

Estimand (frozen): tau(x) = E[Q_strong - Q_weak | x]. Exact simulated logging
propensities are consumed (never estimated). Corrupted/missing propensities
raise loudly (G5).
"""
import numpy as np

from data import RIDGE_ALPHA_PSEUDO
from nuisance import ridge_fit, ridge_predict
from simulate import assert_props


def dr_pseudo_outcomes(mu0, mu1, a, y, e_chosen, e1):
    """DR pseudo-outcomes with known propensities (exact, from the simulator):
    chi = (mu1 - mu0) + A/e1 * (Y - mu_A) - (1-A)/(1-e1) * (0 - mu_A)
        = (mu1 - mu0) + [A/e1 + (1-A)/(1-e1)] * (Y - mu_A)
    (Y=0 counterfactual for the unchosen action of a binary 0/1 outcome)."""
    a = np.asarray(a, int)
    y = np.asarray(y, float)
    mu_a = np.where(a == 1, mu1, mu0)
    w_f = np.where(a == 1, 1.0 / assert_props(e1), 1.0 / assert_props(1.0 - e1))
    chi = (mu1 - mu0) + w_f * (y - mu_a)
    return chi


def fit_tau_ridge(X_tau, chi, alpha=RIDGE_ALPHA_PSEUDO):
    """DRL-pi second stage: ridge of DR pseudo-outcomes on F_tau."""
    return ridge_fit(X_tau, np.asarray(chi, float), alpha)


def fit_direct_baseline(X_tau, a, y, alpha=RIDGE_ALPHA_PSEUDO):
    """Direct weak-correctness baseline (non-causal control, same feature
    budget): ridge of 1[A=0]*Y on F_tau -> w_hat(x)."""
    target = (np.asarray(a, int) == 0).astype(float) * np.asarray(y, float)
    return ridge_fit(X_tau, target, alpha)


def tau_direct_tlearner(mu0, mu1):
    """T-learner comparator: tau = mu1 - mu0 (cross-fitted nuisances)."""
    return mu1 - mu0


def eval_rows_index(d):
    return np.flatnonzero(d["eval_mask"])


def eval_mu_oof(d, sim, mu0, mu1):
    """OOF nuisance predictions for EVAL rows: refit folds over logged rows
    restricted to fit-set rows only (eval rows never contribute to any fold
    training set used to score them)."""
    p = d["p"]
    a_all = sim["a"]
    # logged outcomes for fit rows only
    fit_idx = np.flatnonzero(~d["eval_mask"])
    y_all = np.where(a_all == 1, d["q_strong"], d["q_weak"])
    from nuisance import oof_mu, folds_for, N_FOLDS  # local import to avoid cycle
    # OOF predictions on fit rows (each fit row's prediction excludes its own
    # fold); then a model trained on ALL fit rows predicts eval rows.
    mu0_fit, mu1_fit = oof_mu(p[fit_idx], a_all[fit_idx], y_all[fit_idx],
                              sim["seed"] + 777)
    # full-fit models for eval scoring
    folds = folds_for(len(fit_idx), sim["seed"] + 777)
    p_f, a_f, y_f = p[fit_idx], a_all[fit_idx], y_all[fit_idx]
    X_f = np.stack([np.ones(len(fit_idx)), p_f, a_f.astype(float), p_f * a_f], axis=1)
    X_e = np.stack([np.ones(d["eval_mask"].sum()), p[d["eval_mask"]],
                    np.zeros(d["eval_mask"].sum()), np.zeros(d["eval_mask"].sum())], axis=1)
    X_e1 = np.stack([np.ones(d["eval_mask"].sum()), p[d["eval_mask"]],
                     np.ones(d["eval_mask"].sum()), p[d["eval_mask"]]], axis=1)
    mu0_e = np.zeros(d["eval_mask"].sum())
    mu1_e = np.zeros(d["eval_mask"].sum())
    for f in range(N_FOLDS):
        tr = folds != f
        alpha = 1e-4 * int(tr.sum())
        coef = ridge_fit(X_f[tr], y_f[tr], alpha)
        mu0_e += ridge_predict(X_e, coef)
        mu1_e += ridge_predict(X_e1, coef)
    mu0_e /= N_FOLDS
    mu1_e /= N_FOLDS
    return (fit_idx, mu0_fit, mu1_fit), (mu0_e, mu1_e)
