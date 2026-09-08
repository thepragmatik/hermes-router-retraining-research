"""Idea 102 Stage 0: logging-policy simulator (T010).

Simulates propensity-logged partial feedback from the train-only
full-information matrix. Exact chosen propensities are stored; unchosen
counterfactual outcomes are hidden from the learner (only (A, Y, e(A|x)) rows
leave this module toward learners).
"""
import numpy as np

from data import (DECILE_MIN_STRONG, N_DECILES, OVERLAP_MIN, REGIMES,
                  V1_THRESHOLD)


def v1_mask(p):
    """Frozen V1 decision: strong iff p >= 0.30 (explicit comparison, never a
    bool cast of the score)."""
    return p >= V1_THRESHOLD


def regime_e(regime, p):
    """Exact logging propensity of the strong action under each frozen regime.
    Every row keeps strictly positive support for both actions."""
    if regime == "L1":
        return np.full(len(p), 0.5)
    if regime == "L2":
        return 0.60 * v1_mask(p).astype(float) + 0.20
    if regime == "L3":
        return 0.80 * v1_mask(p).astype(float) + 0.10
    raise ValueError(f"unknown regime {regime!r}; expected one of {REGIMES}")


def assert_props(props):
    props = np.asarray(props, float)
    if not np.isfinite(props).all():
        raise ValueError("missing/NaN propensity: refusing")
    if not ((props > 0) & (props <= 1)).all():
        raise ValueError(f"propensity out of (0,1]: refusing "
                         f"(min={props.min():.4g}, max={props.max():.4g})")
    return props


def simulate(regime, p, seed):
    """One sampled action per row; store exact chosen propensity. Returns dict
    with actions, chosen outcomes NOT included (learner gets outcomes joined
    elsewhere), chosen propensities, and full e-matrix for support math."""
    e1 = assert_props(regime_e(regime, p))          # P(strong|x)
    e0 = assert_props(1.0 - e1)                     # P(weak|x) >= 0.10
    rng = np.random.default_rng(seed)
    u = rng.random(len(p))
    a_strong = u < e1                               # exact inverse-CDF sampling
    a = a_strong.astype(int)
    e_chosen = np.where(a_strong, e1, e0)
    overlap = np.minimum(e1, e0) * np.maximum(e1, e0)
    return {"a": a, "e_chosen": e_chosen, "e1": e1, "e0": e0,
            "overlap": overlap, "seed": seed, "regime": regime}


def frozen_decile_edges(p, fit_mask):
    """Frozen p-decile edges from fit rows only (fit-side statistic)."""
    return np.quantile(p[fit_mask], np.linspace(0, 1, N_DECILES + 1))


def deciles(p, edges):
    return np.clip(np.searchsorted(edges, p, side="right") - 1, 0, N_DECILES - 1)


def assert_log_invariants(sim, p, fit_mask, d):
    """Run-invariant asserts from the prereg; the pipeline refuses to print
    gate numbers if any of these fail."""
    assert_props(sim["e_chosen"])
    e1 = sim["e1"]
    # exact regime formula equality (learner consumes stored exact props)
    assert np.array_equal(e1, regime_e(sim["regime"], p))
    assert (sim["e_chosen"] >= 0.10 - 1e-12).all()
    # per-decile fit-side logged strong count >= 100
    dec = deciles(p, frozen_decile_edges(p, fit_mask))
    strong_fit = (sim["a"] == 1) & fit_mask
    cnt = np.array([int((strong_fit & (dec == k)).sum()) for k in range(N_DECILES)])
    assert cnt.min() >= DECILE_MIN_STRONG, f"decile logged-strong count {cnt}"
    # outcome column joined to actions only
    assert len(sim["a"]) == len(p) == d["n"]
    return cnt
