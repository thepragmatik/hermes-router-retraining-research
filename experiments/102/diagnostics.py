"""Idea 102 Stage 0: weight/ESS/overlap diagnostics + integrity probes (T014,
T018, G4/G5 adversarial tests)."""
import numpy as np

from evaluate import dr_policy_value, ess
from simulate import assert_props, regime_e, v1_mask


def weight_diagnostics(pi1, a, e1, idx):
    """Importance weights of the target policy's preferred action vs the log."""
    pi1 = np.asarray(pi1, float)[idx]
    a_i = np.asarray(a, int)[idx]
    e1_i = assert_props(np.asarray(e1, float)[idx])
    pref = (pi1 >= 0.5).astype(int)
    e_pref = np.where(pref == 1, e1_i, 1.0 - e1_i)
    pi_pref = np.where(pref == 1, np.maximum(pi1, 1 - pi1), np.minimum(pi1, 1 - pi1))
    pi_pref = np.where(pref == 1, pi1, 1.0 - pi1)
    w = pi_pref / e_pref
    return {"ess_frac": ess(w) / len(w), "max_w": float(np.abs(w).max()),
            "p99_w": float(np.quantile(np.abs(w), 0.99))}


def corruption_probe(e1):
    """G5/A3: corrupted propensities (x10) must be refused loudly."""
    bad = np.asarray(e1, float) * 10.0
    try:
        assert_props(bad)
    except ValueError:
        return True
    return False


def nan_probe():
    try:
        assert_props(np.array([0.5, np.nan]))
    except ValueError:
        return True
    return False


def zero_probe():
    try:
        assert_props(np.array([0.5, 0.0]))
    except ValueError:
        return True
    return False


def identity_probe(pi1_exact, a, y, e1, mu0, mu1, idx, truth_value, tol=1e-10):
    """A5: for a deterministic policy that exactly equals a threshold rule on
    known data, DR policy value must equal its full-information truth within
    tol (exact-recovery check of the estimator plumbing)."""
    val, _, _ = dr_policy_value(pi1_exact, a, y, e1, mu0, mu1, idx)
    return abs(val - truth_value) <= tol, val, truth_value


def zero_overlap_mask(p_eval):
    """Synthetic weak-only log support: rows with p < 0.05 have e(strong)=0.02
    (near-zero overlap); the flag threshold is preregistered via OVERLAP_MIN."""
    return p_eval < 0.05
