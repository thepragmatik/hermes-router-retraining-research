"""Idea 101 Stage-0: logging-policy simulator + OPE reconstruction harness.

Train-only full-information replay. Frozen contract: results/101/PREREG.md.
$0 spend; RouterBench test split never loaded.
"""
import numpy as np
import pandas as pd
import hashlib
import os

SEEDS = list(range(101000, 101010))
EPS = 0.20
V1_THRESHOLD = 0.30
HI_THRESHOLD = 0.50
SWITCH_M = 20.0
N_FOLDS = 5

WINRATE_TABLE = "/Users/rath/transfer-bundle/analysis/winrate_table.parquet"
PSTRONG_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "v1_train_pstrong.npy")
ACTIONS = [0, 1]  # 0=weak, 1=strong


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_train_matrix():
    """Return (features, outcomes [n,2], n). Train split only; test never loaded."""
    wt = pd.read_parquet(WINRATE_TABLE)
    train = wt[wt["split"] == "train"].reset_index(drop=True)
    p = np.load(PSTRONG_PATH)
    assert len(p) == len(train) == 29193, (len(p), len(train))
    outcomes = np.stack([train.weak_correct.to_numpy(float),
                         train.strong_correct.to_numpy(float)], axis=1)
    return p.reshape(-1, 1), outcomes, len(train)


# ---------- policies ----------

def v1_policy(p_strong, threshold=V1_THRESHOLD):
    """Deterministic V1: P(strong)=1 if p>=thr else 0."""
    return np.stack([1.0 - (p_strong[:, 0] >= threshold), (p_strong[:, 0] >= threshold)], axis=1)


def target_policies(p_strong):
    return {
        "V1": v1_policy(p_strong, V1_THRESHOLD),
        "V1_hi": v1_policy(p_strong, HI_THRESHOLD),
        "always_weak": np.tile([1.0, 0.0], (len(p_strong), 1)),
    }


def logging_probs(p_strong):
    """Epsilon-mixture: 0.80*V1 + 0.20*uniform. Nonzero support everywhere."""
    return (1.0 - EPS) * v1_policy(p_strong) + EPS / 2.0


# ---------- simulator ----------

def simulate_logging(p_strong, outcomes, seed):
    """Sample one action per row; hide all unchosen outcomes. Returns
    (chosen_actions, chosen_outcomes, chosen_logging_props)."""
    probs = logging_probs(p_strong)
    rng = np.random.default_rng(seed)
    cum = np.cumsum(probs, axis=1)
    u = rng.random(len(probs))
    chosen = (u[:, None] > cum).sum(axis=1).clip(0, 1)
    rows = np.arange(len(chosen))
    chosen_outcomes = outcomes[rows, chosen]
    chosen_props = probs[rows, chosen]
    assert (chosen_props > 0).all(), "zero logging propensity for a sampled action"
    return chosen, chosen_outcomes, chosen_props


def full_info_truth(p_strong, outcomes):
    """Completely separate full-information path (never touches simulated log)."""
    out = {}
    for name, pol in target_policies(p_strong).items():
        vals = (pol * outcomes).sum(axis=1)
        out[name] = float(vals.mean())
    return out


# ---------- estimators ----------

def _check_props(props):
    props = np.asarray(props, float)
    if not np.isfinite(props).all():
        raise ValueError("missing/NaN logging propensity: refusing OPE")
    if not ((props > 0) & (props <= 1)).all():
        raise ValueError(f"logging propensity out of (0,1]: refusing OPE "
                         f"(min={props.min():.4g}, max={props.max():.4g})")
    return props


def ess(w):
    return float(w.sum() ** 2 / (w ** 2).sum()) if w.sum() > 0 else 0.0


def ips(target_probs, actions, outcomes_chosen, props):
    """Preregistered G4 invariant: propensities MUST lie in (0,1] and be finite;
    violations raise loudly instead of returning a silent estimate."""
    props = np.asarray(props, float)
    if not np.isfinite(props).all():
        raise ValueError("missing/NaN logging propensity: refusing OPE")
    if not ((props > 0) & (props <= 1)).all():
        raise ValueError(f"logging propensity out of (0,1]: refusing OPE "
                         f"(min={props.min():.4g}, max={props.max():.4g})")
    t = target_probs[np.arange(len(actions)), actions]
    w = t / props
    v = float((w * outcomes_chosen).mean())
    var = float((w * outcomes_chosen).var(ddof=1) / len(w))
    return v, np.sqrt(max(var, 0.0)), w


def _dr_predict_both(p_strong, actions, outcomes_chosen, seed, folds=None, lam_scale=1e-4):
    """Cross-fitted interaction outcome model. Returns mu_hat for both actions
    per row: array [n,2] = [mu(weak|x), mu(strong|x)]."""
    rng = np.random.default_rng(seed)
    n = len(actions)
    folds = rng.permutation(n) % N_FOLDS
    a0 = (actions == 0).astype(float)
    a1 = (actions == 1).astype(float)
    Xobs = np.stack([p_strong[:, 0], a0, a1, p_strong[:, 0] * a0, p_strong[:, 0] * a1,
                     np.ones(n)], axis=1)
    mu = np.zeros((n, 2))
    for f in range(N_FOLDS):
        tr, te = folds != f, folds == f
        A = Xobs[tr]
        LAM = lam_scale * len(outcomes_chosen[tr])
        coef = np.linalg.solve(A.T @ A + LAM * np.eye(A.shape[1]), A.T @ outcomes_chosen[tr])
        if te.any():
            Xt0 = np.stack([p_strong[te, 0], np.ones(te.sum()), np.zeros(te.sum()),
                            p_strong[te, 0], np.zeros(te.sum()), np.ones(te.sum())], axis=1)
            Xt1 = np.stack([p_strong[te, 0], np.zeros(te.sum()), np.ones(te.sum()),
                            np.zeros(te.sum()), p_strong[te, 0], np.ones(te.sum())], axis=1)
            mu[te, 0] = Xt0 @ coef
            mu[te, 1] = Xt1 @ coef
    return mu


def dr_crossfit(p_strong, target_probs, actions, outcomes_chosen, props, seed):
    """Cross-fitted DR with ridge interaction outcome model."""
    props = _check_props(props)
    mu = _dr_predict_both(p_strong, actions, outcomes_chosen, seed)
    n = len(actions)
    t = target_probs[np.arange(n), actions]
    w = t / props
    dr = (target_probs * mu).sum(axis=1) + w * (outcomes_chosen - mu[np.arange(n), actions])
    return float(dr.mean()), np.sqrt(float(dr.var(ddof=1) / n)), w


def switch_dr(p_strong, target_probs, actions, outcomes_chosen, props, seed, M=SWITCH_M):
    """SWITCH-DR: rows with weight > M use direct-model contribution only."""
    props = _check_props(props)
    mu = _dr_predict_both(p_strong, actions, outcomes_chosen, seed)
    n = len(actions)
    t = target_probs[np.arange(n), actions]
    w = t / props
    clipped = w > M
    w_used = np.where(clipped, 0.0, w)
    contrib = (target_probs * mu).sum(axis=1)
    term = np.where(clipped, contrib,
                    contrib + w * (outcomes_chosen - mu[np.arange(n), actions]))
    # variance ignoring clipped-row cross terms (preregistered plug-in)
    var = float(term.var(ddof=1) / n)
    return float(term.mean()), np.sqrt(max(var, 0.0)), w, w_used, int(clipped.sum())


def support_flag(target_probs, actions, props, w, max_w=50.0, min_ess_frac=0.01,
                 min_prop=1e-6, min_cov=0.05):
    t = target_probs[np.arange(len(actions)), actions]
    reasons = []
    if (props[t > min_prop] <= 0).any() or (t > 0).any() and (props[t > min_prop] < min_prop).any():
        pass
    if (t > 0) .any() and (t[props < min_prop] > 0).any():
        reasons.append("zero_logging_support")
    cov = float((t > 0).mean())
    if cov < min_cov:
        reasons.append(f"target_coverage_{cov:.4f}<_{min_cov}")
    e = ess(w) / len(w)
    if e < min_ess_frac:
        reasons.append(f"ESS_frac_{e:.5f}<_{min_ess_frac}")
    if np.abs(w).max() > max_w:
        reasons.append(f"max_weight_{np.abs(w).max():.1f}>_{max_w}")
    return (len(reasons) > 0), reasons


# ---------- stage-0 run ----------

def run_stage0():
    p_strong, outcomes, n = load_train_matrix()
    truth = full_info_truth(p_strong, outcomes)
    results = {"seeds": {}, "truth": truth, "n_train": n,
               "prereg": "results/101/PREREG.md",
               "artifact_hashes": {
                   "winrate_table": sha256_file(WINRATE_TABLE),
                   "pstrong": sha256_file(PSTRONG_PATH)}}

    for seed in SEEDS:
        actions, oc, props = simulate_logging(p_strong, outcomes, seed)
        seed_res = {}
        for name, tp in target_policies(p_strong).items():
            # support check against the preregistered robust estimator's weights
            v_s, se_s, w_raw, w_used, n_clip = switch_dr(p_strong, tp, actions, oc, props, seed)
            unsupported, reasons = support_flag(tp, actions, props, w_raw)
            v_i, se_i, w_i = ips(tp, actions, oc, props)
            v_d, se_d, _ = dr_crossfit(p_strong, tp, actions, oc, props, seed)
            seed_res[name] = {
                "ips": v_i, "ips_se": se_i,
                "ips_ci": [v_i - 1.96 * se_i, v_i + 1.96 * se_i],
                "snips": v_i * 0 + float((w_i * oc).sum() / w_i.sum()),
                "dr": v_d, "dr_se": se_d,
                "switch_dr": v_s, "switch_dr_se": se_s,
                "switch_dr_ci": [v_s - 1.96 * se_s, v_s + 1.96 * se_s],
                "n_clipped": n_clip,
                "unsupported": unsupported, "support_reasons": reasons,
                "ess_frac": ess(w_i) / n,
                "max_w": float(np.abs(w_i).max()),
                "p99_w": float(np.quantile(np.abs(w_i), 0.99)),
            }
        results["seeds"][str(seed)] = seed_res
    return results


def evaluate_gates(results, primary="switch_dr"):
    truth = results["truth"]
    names = ["V1", "V1_hi", "always_weak"]
    g1_ok_seeds = 0
    g2_v1_err, g2_hi_err, g2_v1_cov, g2_hi_cov = [], [], [], []
    for s, sr in results["seeds"].items():
        est = [sr[n][primary] for n in names]
        g1_ok_seeds += int(list(np.argsort(est)) == list(np.argsort([truth[n] for n in names])))
        for nm, errs, covs in (("V1", g2_v1_err, g2_v1_cov), ("V1_hi", g2_hi_err, g2_hi_cov)):
            errs.append(abs(sr[nm][primary] - truth[nm]))
            lo, hi = sr[nm][f"{primary}_ci"]
            covs.append(int(lo <= truth[nm] <= hi))
    g1 = g1_ok_seeds >= 9
    g2 = ((np.mean(g2_v1_err) <= 0.015 and np.mean(g2_hi_err) <= 0.015)
          or (np.mean(g2_v1_cov) >= 0.9 and np.mean(g2_hi_cov) >= 0.9))
    g3_passed = results.get("support_probe", {}).get("flagged_all_seeds", False)
    g4_passed = results.get("propensity_integrity", {}).get("all_loud", False)
    return {"G1_ordering": {"passed": bool(g1), "seeds_correct": g1_ok_seeds, "required": 9},
            "G2_accuracy": {"passed": bool(g2),
                            "mean_abs_err_V1": float(np.mean(g2_v1_err)),
                            "mean_abs_err_V1_hi": float(np.mean(g2_hi_err)),
                            "ci_coverage_V1": float(np.mean(g2_v1_cov)),
                            "ci_coverage_V1_hi": float(np.mean(g2_hi_cov))},
            "G3_support": {"passed": bool(g3_passed)},
            "G4_propensity_integrity": {"passed": bool(g4_passed)}}
