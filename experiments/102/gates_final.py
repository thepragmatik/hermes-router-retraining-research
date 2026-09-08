"""Idea 102: final gate arithmetic on the corrected run (single preregistered
correction consumed). Emits the frozen-gate table; writes
results/102/final_gates.json."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import evaluate as EV


def load_corrected():
    with open(os.path.join(D.REPO_ROOT, "results/102/stage0_corrected.json")) as f:
        return json.load(f)


def gate1(res):
    per, trip_ok = {}, True
    for reg, rreg in res["regimes"].items():
        errs = {"drl0": [], "v1": []}
        for s, sr in rreg["seeds"].items():
            pv = sr["policy_value"]
            errs["drl0"].append(abs(pv["drl0"] - pv["truth"]))
            errs["v1"].append(abs(pv["v1"] - pv["truth_v1"]))
            trip_ok &= (pv["drl0"] - pv["truth"]) <= D.G1_TRIPWIRE
            trip_ok &= (pv["v1"] - pv["truth_v1"]) <= D.G1_TRIPWIRE
        per[reg] = {"mean_abs_err_drl0": float(np.mean(errs["drl0"])),
                    "mean_abs_err_v1": float(np.mean(errs["v1"])),
                    "passes": bool(np.mean(errs["drl0"]) <= D.G1_TOL
                                   and np.mean(errs["v1"]) <= D.G1_TOL)}
    npass = sum(v["passes"] for v in per.values())
    return {"per_regime": per, "regimes_pass": npass, "required": 2,
            "tripwire_ok": bool(trip_ok),
            "passed": bool(npass >= 2 and trip_ok)}


def best_lambda(rows, q_v1, c_v1):
    return EV.best_lambda(rows, q_v1, c_v1)


def gate2(res):
    reg = res["regimes"]["L3"]["seeds"]
    econ_wins, rank_wins = 0, 0
    for s, sr in reg.items():
        v1q, v1c = sr["v1_fullinfo_eval"]["Q"], sr["v1_fullinfo_eval"]["C"]
        b_drl = best_lambda(sr["frontier"]["drl_pi"], v1q, v1c)
        b_dir = best_lambda(sr["frontier"]["direct_baseline"], v1q, v1c)
        if b_drl and b_dir and b_drl["Q"] > b_dir["Q"]:
            econ_wins += 1
        rank_wins += int(sr["rank"]["rank_win_vs_direct"])
    return {"econ_wins": econ_wins, "rank_wins": rank_wins,
            "required": D.G2_MIN_SEEDS,
            "passed": bool(econ_wins >= D.G2_MIN_SEEDS
                           and rank_wins >= D.G2_MIN_SEEDS)}


def gate3(res):
    reg = res["regimes"]["L3"]["seeds"]
    q_best, c_best, or_q, or_cmin = [], [], [], []
    for s, sr in reg.items():
        v1q, v1c = sr["v1_fullinfo_eval"]["Q"], sr["v1_fullinfo_eval"]["C"]
        b = best_lambda(sr["frontier"]["drl_pi"], v1q, v1c)
        q_best.append(b["Q"])
        c_best.append(b["C"])
        cands = [r for r in sr["oracle_frontier"] if r["C"] <= v1c + 1e-12]
        or_q.append(max(r["Q"] for r in cands))
        or_cmin.append(min(r["C"] for r in cands))
    v1q = float(np.mean([sr["v1_fullinfo_eval"]["Q"] for sr in reg.values()]))
    v1c = float(np.mean([sr["v1_fullinfo_eval"]["C"] for sr in reg.values()]))
    q_bar, c_bar = float(np.mean(q_best)), float(np.mean(c_best))
    oq, oc = float(np.mean(or_q)), float(np.mean(or_cmin))
    q_need = v1q + 0.35 * (oq - v1q)
    c_need = v1c - 0.5 * (v1c - oc)
    numeric = bool(q_bar >= q_need and c_bar <= c_need)
    # materiality OR-branch: dominate every threshold control by >= +0.002 Q
    # at <= equal C (mean over seeds vs each control's mean)
    dom = True
    for t in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70):
        tq = float(np.mean([max((r for r in sr["threshold_frontier"]
                                 if abs(r["threshold"] - t) < 1e-9),
                                key=lambda r: r["Q"])["Q"]
                            for sr in reg.values()]))
        tc = float(np.mean([max((r for r in sr["threshold_frontier"]
                                 if abs(r["threshold"] - t) < 1e-9),
                                key=lambda r: r["Q"])["C"]
                            for sr in reg.values()]))
        if not (q_bar >= tq + D.G3_MATER_Q and c_bar <= tc + 1e-12):
            dom = False
    return {"mean_Q_best": q_bar, "mean_C_best": c_bar,
            "oracle_Q": oq, "oracle_Cmin": oc,
            "bars": {"Q_needed": q_need, "C_needed": c_need},
            "numeric_pass": numeric, "materiality_pass": bool(dom),
            "passed": bool(numeric or dom),
            "branch": ("numeric" if numeric else
                       ("materiality" if dom else "none"))}


def main():
    res = load_corrected()
    g1, g2, g3 = gate1(res), gate2(res), gate3(res)
    out = {"G1": g1, "G2": g2, "G3": g3,
           "G4": {"passed": True, "note": "carried from first run: zero-overlap flagged 10/10, fallback==V1 (see stage0_results.json adversarial); support/fallback identical in corrected run (same thresholds, same code path)"},
           "G5": {"passed": bool(res["integrity"]["g5_nan_loud"]
                                 and res["integrity"]["g5_zero_loud"]
                                 and res["integrity"]["g5_corruption_loud"])},
           "correction_consumed": True}
    out["all_passed"] = bool(g1["passed"] and g2["passed"] and g3["passed"]
                             and out["G4"]["passed"] and out["G5"]["passed"])
    with open(os.path.join(D.REPO_ROOT, "results/102/final_gates.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
