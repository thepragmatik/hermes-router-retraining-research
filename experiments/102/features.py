"""Idea 102 Stage 0: frozen feature sets F_mu / F_tau (prereg)."""
import numpy as np

from data import TOP_FAMILIES, V1_THRESHOLD


def family_top5(d, fit_mask):
    """Top-5 eval families by TRAIN count (fit-side statistic, frozen)."""
    fams, counts = np.unique(d["family"][fit_mask], return_counts=True)
    order = np.argsort(-counts)[:TOP_FAMILIES]
    return set(fams[order].tolist())


def build_tau_features(p, family, fit_mask, top5):
    """F_tau: [1, p, 82 family one-hots, p*f for top-5 families]."""
    fams = list(sorted(set(family.tolist())))
    fam_index = {f: i for i, f in enumerate(fams)}
    n = len(p)
    F = np.zeros((n, 2 + len(fams) + TOP_FAMILIES))
    F[:, 0] = 1.0
    F[:, 1] = p
    for i, f in enumerate(fams):
        F[family == f, 2 + i] = 1.0
    for j, f in enumerate(sorted(top5)):
        F[:, 2 + len(fams) + j] = p * (family == f)
    return F, fams


def tau_feature_names(n_fams):
    names = ["intercept", "p"]
    names += [f"fam_{i}" for i in range(n_fams)]
    names += [f"pxtop_{j}" for j in range(TOP_FAMILIES)]
    return names
