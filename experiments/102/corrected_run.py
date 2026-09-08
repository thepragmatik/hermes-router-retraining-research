"""Idea 102: CORRECTED gate run (single preregistered correction: isotonic
recalibration of OOF DR pseudo-outcomes on OOF tau_hat, fit rows only).
Re-evaluates G1-G5 exactly as frozen; writes results/102/stage0_corrected.json."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import diagnostics as DG
import dr_learner as DR
import evaluate as EV
import features as FE
import nuisance as NU
import policy as PO
import simulate as SI


def isotonic_pava(x, y):
    """Unweighted PAVA isotonic regression of y on x (sorted by x). Returns
    function values at the sorted-x positions (monotone non-decreasing)."""
    order = np.argsort(x, kind="stable")
    xs, ys = x[order], y[order]
    # pool adjacent violators
    vals = []
    weights = []
    for v in ys:
        vals.append(v)
        weights.append(1.0)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2 = vals.pop(), weights.pop()
            v1, w1 = vals.pop(), weights.pop()
            vals.append((w1 * v1 + w2 * v2) / (w1 + w2))
            weights.append(w1 + w2)
    fitted = np.empty(len(ys))
    idx = 0
    for v, w in zip(vals, weights):
        n = int(round(w))
        fitted[idx:idx + n] = v
        idx += n
    out = np.empty(len(ys))
    out[order] = fitted
    return out


def build_isotonic_map(tau_oof, chi_oof):
    """Fit isotonic regression of chi on tau_oof over fit rows; return a
    monotone step function (x-sorted knots) for mapping eval tau_hat."""
    order = np.argsort(tau_oof, kind="stable")
    xs = tau_oof[order]
    gvals = isotonic_pava(tau_oof, chi_oof)[order]
    # collapse to unique knots
    keep = np.concatenate([[True], np.diff(xs) > 0])
    return xs[keep], gvals[keep]


def apply_map(x, knot_x, knot_y):
    idx = np.searchsorted(knot_x, x, side="right") - 1
    idx = np.clip(idx, 0, len(knot_y) - 1)
    return knot_y[idx]


def main():
    os.makedirs(os.path.join(D.REPO_ROOT, "results/102"), exist_ok=True)
    d = D.load_train_matrix()
    D.assert_artifacts()
    p, ev, fit = d["p"], d["eval_mask"], ~d["eval_mask"]
    qw, qs, cw, cs, dcost = (d["q_weak"], d["q_strong"], d["c_weak"],
                             d["c_strong"], d["dcost"])
    n_ev = int(ev.sum())
    top5 = FE.family_top5(d, fit)
    F_tau, fams = FE.build_tau_features(p, d["family"], fit, top5)
    edges = SI.frozen_decile_edges(p, fit)
    dec_all = SI.deciles(p, edges)
    v1_all = SI.v1_mask(p)

    results = {"prereg": "results/102/PREREG.md",
               "correction": "results/102/CORRECTION_LOG.md",
               "regimes": {}, "integrity": {}}

    for regime in D.REGIMES:
        reg_res = {"seeds": {}}
        for seed in D.SEEDS:
            sim = SI.simulate(regime, p, seed)
            SI.assert_log_invariants(sim, p, fit, d)
            a_all, e1_all = sim["a"], sim["e1"]
            y_all = np.where(a_all == 1, qs, qw)
            fit_idx = np.flatnonzero(fit)

            mu0_fit, mu1_fit = NU.oof_mu(p[fit_idx], a_all[fit_idx],
                                         y_all[fit_idx], seed + 777)
            folds = NU.folds_for(len(fit_idx), seed + 777)
            X_f = np.stack([np.ones(len(fit_idx)), p[fit_idx],
                            a_all[fit_idx].astype(float),
                            p[fit_idx] * a_all[fit_idx]], axis=1)
            X_e0 = np.stack([np.ones(n_ev), p[ev], np.zeros(n_ev), np.zeros(n_ev)], axis=1)
            X_e1 = np.stack([np.ones(n_ev), p[ev], np.ones(n_ev), p[ev]], axis=1)
            mu0_e = np.zeros(n_ev)
            mu1_e = np.zeros(n_ev)
            for f in range(D.N_FOLDS):
                tr = folds != f
                coef = NU.ridge_fit(X_f[tr], y_all[fit_idx][tr], 1e-4 * int(tr.sum()))
                mu0_e += NU.ridge_predict(X_e0, coef)
                mu1_e += NU.ridge_predict(X_e1, coef)
            mu0_e /= D.N_FOLDS
            mu1_e /= D.N_FOLDS

            # tau_hat DRL-pi: OOF on fit rows, fold-ensemble on eval rows
            X_fit_tau = F_tau[fit_idx]
            tau_oof = np.zeros(len(fit_idx))
            chi_oof = np.zeros(len(fit_idx))
            coef_full = DR.fit_tau_ridge(X_fit_tau, np.zeros(len(fit_idx)))  # placeholder
            # OOF tau_hat: second-stage fit per fold on chi of other folds
            for f in range(D.N_FOLDS):
                tr = folds != f
                chi_f = DR.dr_pseudo_outcomes(
                    mu0_fit[tr], mu1_fit[tr], a_all[fit_idx][tr],
                    y_all[fit_idx][tr],
                    np.where(a_all[fit_idx][tr] == 1, e1_all[fit_idx][tr],
                             1 - e1_all[fit_idx][tr]), e1_all[fit_idx][tr])
                c_f = DR.fit_tau_ridge(X_fit_tau[tr], chi_f)
                te = folds == f
                tau_oof[te] = NU.ridge_predict(X_fit_tau[te], c_f)
                # OOF chi for the SAME rows uses OOF nuisances mu (already OOF)
            chi_all = DR.dr_pseudo_outcomes(
                mu0_fit, mu1_fit, a_all[fit_idx], y_all[fit_idx],
                np.where(a_all[fit_idx] == 1, e1_all[fit_idx],
                         1 - e1_all[fit_idx]), e1_all[fit_idx])
            chi_oof = chi_all

            # CORRECTION: isotonic map chi <- tau_oof (fit rows only)
            knot_x, knot_y = build_isotonic_map(tau_oof, chi_oof)

            # eval tau_hat: full-fit second stage then isotonic map
            c_full = DR.fit_tau_ridge(X_fit_tau, chi_all)
            tau_hat_raw = NU.ridge_predict(F_tau, c_full)[ev]
            tau_hat = apply_map(tau_hat_raw, knot_x, knot_y)

            # T-learner and direct baselines (unchanged by correction)
            tau_T_eval = mu1_e - mu0_e
            coef_w = DR.fit_direct_baseline(F_tau[fit_idx], a_all[fit_idx], y_all[fit_idx])
            w_hat = NU.ridge_predict(F_tau, coef_w)[ev]

            # support / fallback
            dec_ev = dec_all[ev]
            e_min_eval = np.minimum(sim["e1"], 1 - sim["e1"])[ev]
            strong_fit_by_dec = np.array([
                int(((a_all == 1) & fit & (dec_all == k)).sum())
                for k in range(D.N_DECILES)])
            unsupported, sup_detail = PO.policy_support(
                p[ev], dec_ev, strong_fit_by_dec, e_min_eval)
            v1_eval = v1_all[ev]
            dcost_ev = dcost[ev]

            # lambda sweeps (corrected score)
            frontier = {}
            for name, score in (("drl_pi", tau_hat),
                                ("t_learner", tau_T_eval),
                                ("direct_baseline", (0.30 - w_hat))):
                rows = PO.lambda_sweep(score, d, ev, dcost_ev, unsupported, v1_eval)
                for r in rows:
                    r["scorer"] = name
                frontier[name] = rows
            v1_q, v1_c = PO.policy_metrics(v1_eval, d, ev)["Q"], \
                PO.policy_metrics(v1_eval, d, ev)["C"]

            oracle_rows = []
            tau_true = (qs - qw)[ev]
            for lam in D.LAMBDA_GRID:
                route = (tau_true - lam * dcost_ev) > 0
                m = PO.policy_metrics(route, d, ev)
                oracle_rows.append({"lambda": lam, "Q": m["Q"], "C": m["C"],
                                    "frac_strong": m["frac_strong"],
                                    "scorer": "oracle_fullinfo"})
            thr_rows = []
            for t in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70):
                m = PO.policy_metrics(p[ev] >= t, d, ev)
                thr_rows.append({"threshold": t, "Q": m["Q"], "C": m["C"],
                                 "frac_strong": m["frac_strong"]})

            # Gate 1 policy values (same construction as first run)
            pi_drl0 = (tau_hat - 0.0 * dcost_ev) > 0
            pi_drl0 = np.where(unsupported, v1_eval, pi_drl0).astype(float)
            pi_full = np.zeros(d["n"])
            pi_full[ev] = pi_drl0
            pi_full[fit] = v1_all[fit]
            mu0_full = np.zeros(d["n"])
            mu1_full = np.zeros(d["n"])
            mu0_full[fit_idx] = mu0_fit
            mu1_full[fit_idx] = mu1_fit
            mu0_full[ev] = mu0_e
            mu1_full[ev] = mu1_e
            pv_drl, pv_drl_se, _ = EV.dr_policy_value(
                pi_full, a_all, y_all, e1_all, mu0_full, mu1_full, np.arange(d["n"]))
            pv_v1, pv_v1_se, _ = EV.dr_policy_value(
                v1_all.astype(float), a_all, y_all, e1_all, mu0_full, mu1_full,
                np.arange(d["n"]))
            truth_drl = float((np.where(pi_full.astype(bool), qs, qw)).mean())
            truth_v1 = float((np.where(v1_all, qs, qw)).mean())

            # rank diagnostics (corrected)
            true_tau_dec, tau_hat_dec, w_dec, tau_T_dec = [], [], [], []
            for k in range(D.N_DECILES):
                m = dec_ev == k
                if m.sum() < 30:
                    continue
                true_tau_dec.append(float(tau_true[m].mean()))
                tau_hat_dec.append(float(tau_hat[m].mean()))
                w_dec.append(float(w_hat[m].mean()))
                tau_T_dec.append(float(tau_T_eval[m].mean()))
            rho_drl = EV.spearman(true_tau_dec, tau_hat_dec)
            rho_w = EV.spearman(true_tau_dec, [-x for x in w_dec])
            rho_T = EV.spearman(true_tau_dec, tau_T_dec)

            reg_res["seeds"][str(seed)] = {
                "v1_fullinfo_eval": {"Q": v1_q, "C": v1_c,
                                     "frac_strong": float(v1_eval.mean())},
                "policy_value": {"drl0": pv_drl, "drl0_se": pv_drl_se,
                                 "truth": truth_drl, "v1": pv_v1,
                                 "v1_se": pv_v1_se, "truth_v1": truth_v1},
                "frontier": frontier, "oracle_frontier": oracle_rows,
                "threshold_frontier": thr_rows,
                "support": {"unsupported_frac": float(unsupported.mean()),
                            "detail": sup_detail},
                "rank": {"spearman_drl": rho_drl, "spearman_w_inverted": rho_w,
                         "spearman_T": rho_T,
                         "rank_win_vs_direct": bool(rho_drl > rho_w)},
                "min_decile_strong": int(strong_fit_by_dec.min()),
            }
            print(f"[{regime} {seed}] pv_drl={pv_drl:.5f} truth={truth_drl:.5f} "
                  f"rho_drl={rho_drl:.3f} rho_w={rho_w:.3f}", flush=True)
        results["regimes"][regime] = reg_res

    results["integrity"] = {
        "g5_nan_loud": DG.nan_probe(), "g5_zero_loud": DG.zero_probe(),
        "g5_corruption_loud": DG.corruption_probe(SI.regime_e("L3", p)),
    }
    out = os.path.join(D.REPO_ROOT, "results/102/stage0_corrected.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    print("wrote", out, flush=True)


if __name__ == "__main__":
    main()
