"""Idea 102 Stage 0: cross-fitted nuisance outcome models (T012) + closed-form
ridge helpers. Frozen per PREREG: ridge alpha = 1e-4 * n_train_fold (matching
101's convention), 5-fold OOF via default_rng(seed).permutation(n) % 5."""
import numpy as np

from data import N_FOLDS


def ridge_fit(X, y, alpha):
    """Closed-form ridge with intercept carried in X (no penalty on scale
    ambiguity here; alpha is absolute as preregistered)."""
    d = X.shape[1]
    return np.linalg.solve(X.T @ X + alpha * np.eye(d), X.T @ y)


def ridge_predict(X, coef):
    return X @ coef


def folds_for(n, seed):
    return np.random.default_rng(seed).permutation(n) % N_FOLDS


def oof_mu(p_strong_logged, actions, y_logged, seed):
    """Cross-fitted mu0/mu1 on logged rows. Features per row: [1, p, a, p*a]
    (intercept + p, strong-indicator, interaction). Returns (mu0, mu1) OOF
    predictions for every logged row (arrays aligned to logged rows)."""
    p = np.asarray(p_strong_logged, float)
    a = np.asarray(actions, int)
    y = np.asarray(y_logged, float)
    n = len(a)
    folds = folds_for(n, seed)
    X_full = np.stack([np.ones(n), p, a.astype(float), p * a], axis=1)
    mu = np.zeros((n, 2))
    for f in range(N_FOLDS):
        tr, te = folds != f, folds == f
        if not te.any():
            continue
        Xa1 = X_full[tr]
        alpha = 1e-4 * len(y[tr])
        coef = ridge_fit(Xa1, y[tr], alpha)
        X_te0 = np.stack([np.ones(te.sum()), p[te], np.zeros(te.sum()), np.zeros(te.sum())], axis=1)
        X_te1 = np.stack([np.ones(te.sum()), p[te], np.ones(te.sum()), p[te]], axis=1)
        mu[te, 0] = ridge_predict(X_te0, coef)
        mu[te, 1] = ridge_predict(X_te1, coef)
    return mu[:, 0], mu[:, 1]
