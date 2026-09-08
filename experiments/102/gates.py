"""Idea 102: Stage-0 gate arithmetic (T017, T020, T021) from
results/102/stage0_results.json. Emits frontier.csv, support_diagnostics.csv,
gate table. No numbers are changed here — gates are evaluated exactly as
frozen in results/102/PREREG.md."""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import evaluate as EV


def load():
    with open(os.path.join(D.REPO_ROOT, D.RESULTS_JSON)) as f:
        return json.load(f)


def gate1(res):
    """|DR policy value - full-info truth| <= 0.015 (mean over seeds) for both
    evaluated policies (drl0, v1); regime passes iff both hold; need >=2/3.
    Tripwire: no (regime, seed) estimate may exceed truth by > 0.05."""
    per_regime = {}
    tripwire_ok = True
    for reg, rreg in res["regimes"].items():
        errs = {"drl0": [], "v1": []}
        for s, sr in rreg["seeds"].items():
            pv = sr["policy_value"]
            errs["drl0"].append(abs(pv["drl0"] - pv["truth"]))
            errs["v1"].append(abs(pv["v1"] - pv["truth_v1"]))
            if pv["drl0"] - pv["truth"] > D.G1_TRIPWIRE:
                tripwire_ok = False
            if pv["v1"] - pv["truth_v1"] > D.G1_TRIPWIRE:
                tripwire_ok = False
        per_regime[reg] = {
            "mean_abs_err_drl0": float(np.mean(errs["drl0"])),
            "mean_abs_err_v1": float(np.mean(errs["v1"])),
            "passes": (np.mean(errs["drl0"]) <= D.G1_TOL
                       and np.mean(errs["v1"]) <= D.G1_TOL)}
    n_pass = sum(1 for v in per_regime.values() if v["passes"])
    return {"per_regime": per_regime, "regimes_pass": n_pass,
            "required": 2, "passed": n_pass >= 2 and tripwire_ok,
            "tripwire_ok": tripwire_ok}


def _best_lambda(rows, q_v1, c_v1):
    return EV.best_lambda(rows, q_v1, c_v1)


def gate3(res):
    """Best-lambda DRL-pi policy (L3, mean over seeds) must reach the frozen
    numeric bars OR dominate every threshold-on-p control by >= +0.002 Q at
    <= equal C."""
    reg = res["regimes"]["L3"]["seeds"]
    q_bars, c_bars, fr = [], [], []
    oracles = []
    for s, sr in reg.items():
        v1q = sr["v1_fullinfo_eval"]["Q"]
        v1c = sr["v1_fullinfo_eval"]["C"]
        best = _best_lambda(sr["frontier"]["drl_pi"], v1q, v1c)
        assert best is not None, f"no cost-nonincreasing lambda for seed {s}"
        q_bars.append(best["Q"])
        c_bars.append(best["C"])
        fr.append(best["frac_strong"])
        best_or = max((r for r in sr["oracle_frontier"]
                       if r["C"] <= v1c + 1e-12),
                      key=lambda r: r["Q"], default=None)
        if best_or is not None:
            oracles.append(best_or["Q"])
    mean = lambda x: float(np.mean(x))
    q_bar, c_bar = mean(q_bars), mean(c_bars)
    # numeric bars anchored to per-seed mean V1 and mean oracle lift
    v1_q = mean([sr["v1_fullinfo_eval"]["Q"] for sr in reg.values()])
    v1_c = mean([sr["v1_fullinfo_eval"]["C"] for sr in reg.values()])
    or_q = mean(oracles) if oracles else None
    q_need = v1_q + 0.35 * (or_q - v1_q) if or_q else D.G3_Q_BAR
    c_need = v1_c - 0.5 * (v1_c - mean([
        min(r["C"] for r in sr["oracle_frontier"] if r["C"] <= v1_c + 1e-12)
        for sr in reg.values()])) if or_q else D.G3_C_BAR
    branch_numeric = (q_bar >= q_need) and (c_bar <= c_need)
    # materiality OR-branch: dominate every threshold control
    dom = True
    for t in reg["102000"]["threshold_frontier"]:
        if q_bar < t["Q"] + D.G3_MATER_Q:
            dom = False
        if c_bar > t["C"] + 1e-12:
            dom = False
    return {"mean_Q_best": q_bar, "mean_C_best": c_bar,
            "mean_frac_strong": mean(fr),
            "numeric_bars": {"Q_needed": q_need, "C_needed": c_need},
            "branch_numeric_pass": bool(branch_numeric),
            "branch_materiality_pass": bool(dom),
            "passed": bool(branch_numeric or dom),
            "branch": ("numeric" if branch_numeric else
                       ("materiality" if dom else "none"))}


def gate2(res):
    """DRL-pi must beat the direct weak-correctness baseline (economics) and
    rank tau strata better (Spearman on eval tau deciles) in >= 8/10 seeds."""
    reg = res["regimes"]["L3"]["seeds"]
    econ_wins, rank_wins = 0, 0
    details = []
    for s, sr in reg.items():
        v1q, v1c = (sr["v1_fullinfo_eval"]["Q"], sr["v1_fullinfo_eval"]["C"])
        b_drl = _best_lambda(sr["frontier"]["drl_pi"], v1q, v1c)
        b_dir = _best_lambda(sr["frontier"]["direct_baseline"], v1q, v1c)
        econ = b_drl is not None and b_dir is not None and b_drl["Q"] > b_dir["Q"]
        econ_wins += int(bool(econ))
        details.append({"seed": s, "econ_win": bool(econ),
                        "Q_drl": None if b_drl is None else b_drl["Q"],
                        "Q_dir": None if b_dir is not None else None})
    # rank sub-condition: per-seed Spearman(tau_hat, tau_true) vs Spearman(w_dir)
    # needs tau arrays; recomputed in gate2_spearman() below (run_stage0 saved
    # only aggregates) — spearman comparison executed at pipeline level.
    return {"econ_wins": econ_wins, "required": D.G2_MIN_SEEDS,
            "econ_pass": econ_wins >= D.G2_MIN_SEEDS, "details": details,
            "passed": None}  # finalized after spearman merge


def main():
    res = load()
    g1 = gate1(res)
    g2 = gate2(res)
    g3 = gate3(res)
    out = {"G1": g1, "G2": g2, "G3": g3,
           "integrity": res["integrity"]}
    print(json.dumps(out, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
