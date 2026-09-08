"""Idea 102 Stage-0 gate run (T015-T021). Executes the frozen prereg:
results/102/PREREG.md. Simulation-only, $0, train-only, test sealed.

Pipeline per (regime, seed):
  1. simulate logged actions + exact propensities (unchosen outcomes hidden);
  2. cross-fitted nuisances mu0/mu1 (fit rows only; eval rows scored by
     fold-ensemble models never trained on eval rows);
  3. DR pseudo-outcomes with exact propensities -> DRL-pi tau_hat (eval);
     T-learner tau; direct weak-correctness baseline w_hat (eval);
  4. support flags -> fallback mask (V1 decision on unsupported rows);
  5. lambda sweep frontiers for DRL-pi / T-learner / direct / oracle / V1;
  6. DR policy-value estimate for the DRL-pi@lambda=0 policy + V1 (Gate 1),
     full-information eval truth (hidden matrix, separate path);
  7. Gate arithmetic (G1-G5) + diagnostics emitted to JSON/CSV.

No gate number is printed before all run-invariant asserts pass.
"""
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


def q_cols(d):
    return (d["q_weak"], d["q_strong"], d["c_weak"], d["c_strong"],
            d["dcost"])


def full_info_policy_value(route_eval, d):
    qw, qs, cw, cs, _ = q_cols(d)
    ev = d["eval_mask"]
    q = np.where(route_eval, qs[ev], qw[ev])
    c = np.where(route_eval, cs[ev], cw[ev])
    return float(q.mean()), float(c.mean())


def main():
    os.makedirs(os.path.join(D.REPO_ROOT, "results/102"), exist_ok=True)
    d = D.load_train_matrix()
    D.assert_artifacts()
    p, ev, fit = d["p"], d["eval_mask"], ~d["eval_mask"]
    qw, qs, cw, cs, dcost = q_cols(d)
    n_ev = int(ev.sum())

    top5 = FE.family_top5(d, fit)
    F_tau, fams = FE.build_tau_features(p, d["family"], fit, top5)
    edges = SI.frozen_decile_edges(p, fit)
    dec_all = SI.deciles(p, edges)
    v1_all = SI.v1_mask(p)

    results = {"prereg": "results/102/PREREG.md",
               "artifact_hashes": D.assert_artifacts(),
               "split": {"n_train": d["n"], "n_eval": n_ev, "n_fit": int(fit.sum())},
               "regimes": {}, "integrity": {}}

    # ---- G5 integrity probes (loud refusal) ----
    g5_nan = DG.nan_probe()
    g5_zero = DG.zero_probe()

    for regime in D.REGIMES:
        reg_res = {"seeds": {}}
        for seed in D.SEEDS:
            sim = SI.simulate(regime, p, seed)
            SI.assert_log_invariants(sim, p, fit, d)
            a_all = sim["a"]
            e1_all = sim["e1"]
            y_all = np.where(a_all == 1, qs, qw)  # joined observed outcome only

            # ---- nuisances (fit rows only) ----
            fit_idx = np.flatnonzero(fit)
            mu0_fit, mu1_fit = NU.oof_mu(p[fit_idx], a_all[fit_idx],
                                         y_all[fit_idx], seed + 777)
            folds = NU.folds_for(len(fit_idx), seed + 777)
            X_f = np.stack([np.ones(len(fit_idx)), p[fit_idx],
                            a_all[fit_idx].astype(float),
                            p[fit_idx] * a_all[fit_idx]], axis=1)
            n_e = n_ev
            X_e0 = np.stack([np.ones(n_e), p[ev], np.zeros(n_e), np.zeros(n_e)], axis=1)
            X_e1m = np.stack([np.ones(n_e), p[ev], np.ones(n_e), p[ev]], axis=1)
            mu0_e = np.zeros(n_e)
            mu1_e = np.zeros(n_e)
            for f in range(D.N_FOLDS):
                tr = folds != f
                coef = NU.ridge_fit(X_f[tr], y_all[fit_idx][tr],
                                    1e-4 * int(tr.sum()))
                mu0_e += NU.ridge_predict(X_e0, coef)
                mu1_e += NU.ridge_predict(X_e1m, coef)
            mu0_e /= D.N_FOLDS
            mu1_e /= D.N_FOLDS

            # ---- DR pseudo-outcomes (fit rows) -> tau second stages ----
            chi_fit = DR.dr_pseudo_outcomes(
                mu0_fit, mu1_fit, a_all[fit_idx], y_all[fit_idx],
                np.where(a_all[fit_idx] == 1, e1_all[fit_idx], 1 - e1_all[fit_idx]),
                e1_all[fit_idx])
            coef_tau = DR.fit_tau_ridge(F_tau[fit_idx], chi_fit)
            tau_hat_all = NU.ridge_predict(F_tau, coef_tau)[ev]

            # T-learner tau on eval
            tau_T_eval = mu1_e - mu0_e

            # direct weak-correctness baseline on eval
            coef_w = DR.fit_direct_baseline(F_tau[fit_idx], a_all[fit_idx],
                                            y_all[fit_idx])
            w_hat_all = NU.ridge_predict(F_tau, coef_w)[ev]
            # decision-form identity: route strong iff w_hat < 0.30
            direct_route = w_hat_all < D.V1_THRESHOLD

            # oracle (diagnostic, full-information on eval)
            tau_true = (qs - qw)[ev]

            # ---- support / fallback ----
            dec_ev = dec_all[ev]
            e_min_eval = np.minimum(sim["e1"], 1 - sim["e1"])[ev]
            strong_fit_by_dec = np.array([
                int(((a_all == 1) & fit & (dec_all == k)).sum())
                for k in range(D.N_DECILES)])
            unsupported, sup_detail = PO.policy_support(
                p[ev], dec_ev, strong_fit_by_dec, e_min_eval)
            v1_eval = v1_all[ev]
            dcost_ev = dcost[ev]

            # ---- lambda sweeps ----
            frontier = {}
            for name, score in (("drl_pi", tau_hat_all),
                                ("t_learner", tau_T_eval),
                                ("direct_baseline", (0.30 - w_hat_all))):
                rows = PO.lambda_sweep(score, d, ev, dcost_ev, unsupported,
                                       v1_eval)
                for r in rows:
                    r["scorer"] = name
                frontier[name] = rows
            # V1 reference point (lambda-independent)
            v1_q, v1_c = full_info_policy_value(v1_eval, d)

            # oracle frontier (full-information diagnostic)
            oracle_rows = []
            for lam in D.LAMBDA_GRID:
                route = (tau_true - lam * dcost_ev) > 0
                qv, cv = full_info_policy_value(route, d)
                oracle_rows.append({"lambda": lam, "Q": qv, "C": cv,
                                    "frac_strong": float(route.mean()),
                                    "scorer": "oracle_fullinfo"})

            # threshold-on-p controls (full-information, monotone family)
            thr_rows = []
            for t in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70):
                route = p[ev] >= t
                qv, cv = full_info_policy_value(route, d)
                thr_rows.append({"threshold": t, "Q": qv, "C": cv,
                                 "frac_strong": float(route.mean())})

            # ---- Gate 1: DR policy value of tau-policy@0 and V1 ----
            # Policy surface: full train (fit rows get the conservative V1
            # decision, eval rows the tau-policy@0 with fallback). Nuisance
            # values are OOF on fit rows and fold-ensemble (out-of-sample) on
            # eval rows. The frozen truth comparator is the full-information
            # value of the SAME policy surface.
            pi_drl0 = (tau_hat_all - 0.0 * dcost_ev) > 0
            pi_drl0 = np.where(unsupported, v1_eval, pi_drl0).astype(float)
            pi_full = np.zeros(d["n"])
            pi_full[ev] = pi_drl0
            pi_full[fit] = v1_all[fit]
            mu0_full = np.zeros(d["n"])
            mu1_full = np.zeros(d["n"])
            mu0_full[fit_idx] = mu0_fit
            mu1_full[fit_idx] = mu1_fit
            # eval rows: use the fold-ensemble predictions (out-of-sample)
            mu0_full[ev] = mu0_e
            mu1_full[ev] = mu1_e
            pv_drl, pv_drl_se, w_pv = EV.dr_policy_value(
                pi_full, a_all, y_all, e1_all, mu0_full, mu1_full,
                np.arange(d["n"]))
            pi_v1_full = v1_all.astype(float)
            pv_v1, pv_v1_se, w_v1 = EV.dr_policy_value(
                pi_v1_full, a_all, y_all, e1_all, mu0_full, mu1_full,
                np.arange(d["n"]))

            # full-information truth on the SAME surface (fit+eval)
            truth_drl = float((np.where(pi_full.astype(bool), qs, qw)).mean())
            truth_v1 = float((np.where(v1_all, qs, qw)).mean())

            # weight diagnostics
            wd_drl = DG.weight_diagnostics(pi_full.astype(bool), a_all, e1_all,
                                           np.arange(d["n"]))
            wd_v1 = DG.weight_diagnostics(v1_all, a_all, e1_all,
                                          np.arange(d["n"]))

            reg_res["seeds"][str(seed)] = {
                "v1_truth": truth_v1,
                "v1_fullinfo_eval": {"Q": v1_q, "C": v1_c,
                                     "frac_strong": float(v1_eval.mean())},
                "policy_value": {
                    "drl0": pv_drl, "drl0_se": pv_drl_se, "truth": truth_drl,
                    "v1": pv_v1, "v1_se": pv_v1_se, "truth_v1": truth_v1,
                    "ess_frac_drl": wd_drl["ess_frac"],
                    "max_w_drl": wd_drl["max_w"],
                    "ess_frac_v1": wd_v1["ess_frac"],
                    "max_w_v1": wd_v1["max_w"]},
                "frontier": frontier,
                "oracle_frontier": oracle_rows,
                "threshold_frontier": thr_rows,
                "support": {"unsupported_frac": float(unsupported.mean()),
                            "detail": sup_detail},
                "direct_route_equals_v1": bool(
                    np.array_equal(direct_route, v1_eval)),
                "min_decile_strong": int(strong_fit_by_dec.min()),
            }
            print(f"[{regime} seed={seed}] support_frac="
                  f"{unsupported.mean():.4f} pv_drl={pv_drl:.5f} "
                  f"truth_drl={truth_drl:.5f} pv_v1={pv_v1:.5f} "
                  f"truth_v1={truth_v1:.5f}", flush=True)

        results["regimes"][regime] = reg_res

    results["integrity"] = {
        "g5_nan_loud": g5_nan, "g5_zero_loud": g5_zero,
        "g5_corruption_loud": DG.corruption_probe(SI.regime_e("L3", p)),
    }

    out_path = os.path.join(D.REPO_ROOT, D.RESULTS_JSON)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=1)
    print("wrote", out_path, flush=True)


if __name__ == "__main__":
    main()
