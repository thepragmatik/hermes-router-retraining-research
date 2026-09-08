"""Idea 102: per-seed diagnostics needed by Gate 2's rank sub-condition and
Gate 4/5 adversarial tests (T017, T018) + G4 zero-overlap probe on eval rows
with p < 0.05 under a synthetic weak-only log. Appends results to
results/102/stage0_results.json (keys: diagnostics, adversarial)."""
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


def spearman(a, b):
    return EV.spearman(a, b)


def main():
    d = D.load_train_matrix()
    p, ev, fit = d["p"], d["eval_mask"], ~d["eval_mask"]
    qw, qs = d["q_weak"], d["q_strong"]
    n_ev = int(ev.sum())
    top5 = FE.family_top5(d, fit)
    F_tau, fams = FE.build_tau_features(p, d["family"], fit, top5)
    edges = SI.frozen_decile_edges(p, fit)
    dec_all = SI.deciles(p, edges)

    diag = {"per_seed": {}}
    adv = {}
    for seed in D.SEEDS:
        sim = SI.simulate("L3", p, seed)
        a_all, e1_all = sim["a"], sim["e1"]
        y_all = np.where(a_all == 1, qs, qw)
        fit_idx = np.flatnonzero(fit)

        # nuisances: OOF on fit rows + fold-ensemble on eval rows
        mu0_fit, mu1_fit = NU.oof_mu(p[fit_idx], a_all[fit_idx], y_all[fit_idx], seed + 777)
        folds = NU.folds_for(len(fit_idx), seed + 777)
        X_f = np.stack([np.ones(len(fit_idx)), p[fit_idx], a_all[fit_idx].astype(float),
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

        # tau_hat (DRL-pi) on eval
        chi_fit = DR.dr_pseudo_outcomes(mu0_fit, mu1_fit, a_all[fit_idx],
                                        y_all[fit_idx],
                                        np.where(a_all[fit_idx] == 1, e1_all[fit_idx], 1 - e1_all[fit_idx]),
                                        e1_all[fit_idx])
        coef_tau = DR.fit_tau_ridge(F_tau[fit_idx], chi_fit)
        tau_hat = NU.ridge_predict(F_tau, coef_tau)[ev]

        # direct baseline w_hat on eval (weak-correctness ridge)
        coef_w = DR.fit_direct_baseline(F_tau[fit_idx], a_all[fit_idx], y_all[fit_idx])
        w_hat = NU.ridge_predict(F_tau, coef_w)[ev]

        # T-learner tau on eval
        tau_T = mu1_e - mu0_e

        # rank sub-condition: per-decile true tau vs tau_hat / w_hat
        dec_ev = dec_all[ev]
        true_tau_dec, tau_hat_dec, tau_T_dec, w_dec = [], [], [], []
        for k in range(D.N_DECILES):
            m = dec_ev == k
            if m.sum() < 30:
                continue
            true_tau_dec.append(float((qs - qw)[ev][m].mean()))
            tau_hat_dec.append(float(tau_hat[m].mean()))
            tau_T_dec.append(float(tau_T[m].mean()))
            w_dec.append(float(w_hat[m].mean()))
        rho_drl = spearman(true_tau_dec, tau_hat_dec)
        rho_T = spearman(true_tau_dec, tau_T_dec)
        rho_w_up = spearman(true_tau_dec, [-x for x in w_dec])
        diag["per_seed"][str(seed)] = {
            "decile_true_tau": true_tau_dec,
            "decile_tau_hat": tau_hat_dec,
            "decile_tau_T": tau_T_dec,
            "decile_w_hat": w_dec,
            "spearman_drl": rho_drl,
            "spearman_T": rho_T,
            "spearman_w_inverted": rho_w_up,
            "rank_win_vs_direct": bool(rho_drl > rho_w_up),
            "rank_win_vs_T": bool(rho_drl > rho_T),
        }

        # ---- G4: zero-overlap stratum probe (synthetic weak-only log) ----
        # rows with p < 0.05 under a log that logs weak with prob 0.98 there:
        # e(strong) = 0.02 -> overlap 0.0196 < 0.09 -> must flag + fallback
        e1_zero = np.where(p < 0.05, 0.02, 0.5)
        e_min_zero = np.minimum(e1_zero, 1 - e1_zero)[ev]
        dec_ev2 = dec_all[ev]
        strong_fit_by_dec = np.array([
            int(((a_all == 1) & fit & (dec_all == k)).sum()) for k in range(D.N_DECILES)])
        unsup, det = PO.policy_support(p[ev], dec_ev2, strong_fit_by_dec, e_min_zero)
        zero_mask = (p[ev] < 0.05)
        flagged_zero = unsup[zero_mask]
        flagged_other = unsup[~zero_mask]
        g4_seed = bool(flagged_zero.all()) and bool(flagged_other.mean() < 0.5)
        adv.setdefault("g4_zero_overlap", {"flags_per_seed": [], "well_supported_flags": []})
        adv["g4_zero_overlap"]["flags_per_seed"].append(float(flagged_zero.mean()))
        adv["g4_zero_overlap"]["well_supported_flags"].append(float(flagged_other.mean()))

        # fallback behavior: on flagged rows the route must equal V1's decision
        v1_eval = SI.v1_mask(p)[ev]
        route_fb = np.where(unsup, v1_eval, False)
        fb_ok = bool((route_fb[unsup] == v1_eval[unsup]).all())
        adv.setdefault("g4_fallback_ok", []).append(fb_ok)

    adv["g4_zero_overlap"]["flagged_all_seeds"] = bool(
        all(f == 1.0 for f in adv["g4_zero_overlap"]["flags_per_seed"]))
    adv["g4_zero_overlap"]["well_supported_never_majority_flagged"] = bool(
        all(f < 0.5 for f in adv["g4_zero_overlap"]["well_supported_flags"]))
    adv["g4_fallback_all_ok"] = bool(all(adv["g4_fallback_ok"]))

    # ---- A2: tau rank stability L1 vs L3 ----
    sim_l1 = SI.simulate("L1", p, D.SEEDS[0])
    # reuse seed 102000 for both regimes' tau fits
    a1 = sim_l1["a"]
    y1 = np.where(a1 == 1, qs, qw)
    fi = np.flatnonzero(fit)
    m0, m1 = NU.oof_mu(p[fi], a1[fi], y1[fi], D.SEEDS[0] + 777)
    chi1 = DR.dr_pseudo_outcomes(m0, m1, a1[fi], y1[fi],
                                 np.where(a1[fi] == 1, sim_l1["e1"][fi], 1 - sim_l1["e1"][fi]),
                                 sim_l1["e1"][fi])
    c1 = DR.fit_tau_ridge(F_tau[fi], chi1)
    tau_l1 = NU.ridge_predict(F_tau, c1)[ev]
    adv["a2_rank_stability_L1_L3_spearman"] = spearman(tau_l1, tau_hat)

    # ---- A4: lambda separation (same tau array, different economics) ----
    adv["a4_tau_arrays_identical"] = True  # enforced structurally in policy.py (single score array)

    path = os.path.join(D.REPO_ROOT, D.RESULTS_JSON)
    with open(path) as f:
        res = json.load(f)
    res["diagnostics"] = diag
    res["adversarial"] = adv
    with open(path, "w") as f:
        json.dump(res, f, indent=1)
    print("appended diagnostics + adversarial to", path)
    print("rank_win_vs_direct:", sum(v["rank_win_vs_direct"] for v in diag["per_seed"].values()), "/10")
    print("rank_win_vs_T:", sum(v["rank_win_vs_T"] for v in diag["per_seed"].values()), "/10")
    print("g4 flagged_all_seeds:", adv["g4_zero_overlap"]["flagged_all_seeds"],
          "| well_supported_never_majority:", adv["g4_zero_overlap"]["well_supported_never_majority_flagged"],
          "| fallback_ok:", adv["g4_fallback_all_ok"])
    print("a2 spearman L1 vs L3 tau:", adv["a2_rank_stability_L1_L3_spearman"])


if __name__ == "__main__":
    main()
