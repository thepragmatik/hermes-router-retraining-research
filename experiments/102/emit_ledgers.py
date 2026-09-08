"""Idea 102: emit machine-readable ledgers (T051): frontier.csv (all regimes,
seeds, scorers, lambdas + oracle/threshold rows) and support_diagnostics.csv.
Reads both result JSONs; appends frontier rows to results/frontier.csv."""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D


def main():
    with open(os.path.join(D.REPO_ROOT, D.RESULTS_JSON)) as f:
        res1 = json.load(f)
    with open(os.path.join(D.REPO_ROOT, "results/102/stage0_corrected.json")) as f:
        res2 = json.load(f)

    out_path = os.path.join(D.REPO_ROOT, D.FRONTIER_CSV)
    rows = []
    for tag, res in (("first_run", res1), ("corrected_run", res2)):
        for reg, rreg in res["regimes"].items():
            for seed, sr in rreg["seeds"].items():
                v1q = sr["v1_fullinfo_eval"]["Q"]
                v1c = sr["v1_fullinfo_eval"]["C"]
                rows.append({"run": tag, "regime": reg, "seed": seed,
                             "scorer": "v1_frozen", "lambda": "",
                             "Q": round(v1q, 6), "C": round(v1c, 8),
                             "frac_strong": round(sr["v1_fullinfo_eval"]["frac_strong"], 5),
                             "fallback_frac": 0.0})
                for scorer, fr in sr["frontier"].items():
                    for r in fr:
                        rows.append({"run": tag, "regime": reg, "seed": seed,
                                     "scorer": scorer, "lambda": r["lambda"],
                                     "Q": round(r["Q"], 6), "C": round(r["C"], 8),
                                     "frac_strong": round(r["frac_strong"], 5),
                                     "fallback_frac": round(r.get("fallback_frac", 0.0), 5)})
                for r in sr["oracle_frontier"]:
                    rows.append({"run": tag, "regime": reg, "seed": seed,
                                 "scorer": "oracle_fullinfo", "lambda": r["lambda"],
                                 "Q": round(r["Q"], 6), "C": round(r["C"], 8),
                                 "frac_strong": round(r["frac_strong"], 5),
                                 "fallback_frac": 0.0})
                for r in sr["threshold_frontier"]:
                    rows.append({"run": tag, "regime": reg, "seed": seed,
                                 "scorer": f"threshold_p_{r['threshold']:.2f}",
                                 "lambda": "", "Q": round(r["Q"], 6),
                                 "C": round(r["C"], 8),
                                 "frac_strong": round(r["frac_strong"], 5),
                                 "fallback_frac": 0.0})
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out_path, len(rows), "rows")

    # support diagnostics CSV (first run has the detailed support blocks)
    sup_path = os.path.join(D.REPO_ROOT, D.SUPPORT_CSV)
    with open(sup_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["regime", "seed", "unsupported_frac", "overlap_fail",
                    "ess_fail", "count_fail", "min_decile_strong",
                    "pv_drl", "pv_drl_truth", "pv_v1", "pv_v1_truth",
                    "ess_frac_v1", "max_w_v1"])
        for reg, rreg in res1["regimes"].items():
            for seed, sr in rreg["seeds"].items():
                sup = sr["support"]
                pv = sr["policy_value"]
                w.writerow([reg, seed, round(sup["unsupported_frac"], 5),
                            sup["detail"]["overlap_fail"], sup["detail"]["ess_fail"],
                            sup["detail"]["count_fail"], sr["min_decile_strong"],
                            round(pv["drl0"], 6), round(pv["truth"], 6),
                            round(pv["v1"], 6), round(pv["truth_v1"], 6),
                            round(pv.get("ess_frac_v1", 0.0), 5),
                            round(pv.get("max_w_v1", 0.0), 3)])
    print("wrote", sup_path)

    # summary rows for the repo frontier ledger use the LEDGER's own schema:
    # policy,quality,total_cost_usd,frontier_calls,mid_calls,cheap_extra_samples,
    # verifier_calls,p50_latency_s,p95_latency_s,notes
    repo_ledger = os.path.join(D.REPO_ROOT, "results/frontier.csv")
    summary_rows = []
    for tag in ("first_run", "corrected_run"):
        summary_rows.append({
            "policy": f"102_doubly_robust_uplift_router_stage0_{tag}_L3_best_lambda",
            "quality": 0.63641 if tag == "corrected_run" else 0.63748,
            "total_cost_usd": 0.00137947 if tag == "corrected_run" else 0.00139501,
            "frontier_calls": round(0.76873, 4),
            "mid_calls": 0, "cheap_extra_samples": 0, "verifier_calls": 0,
            "p50_latency_s": "", "p95_latency_s": "",
            "notes": "Stage-0 (train-only 102 eval split, 10 seeds, L3): best-cost-"
                     "nonincreasing DR-uplift frontier point vs V1 0.63944@0.0014224; "
                     "G3 numeric+materiality FAIL, G1/G2/G4/G5 pass after 1 preregistered "
                     "correction; terminal KILLED; detail results/102/STAGE0_REPORT.md"})
    with open(repo_ledger, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["policy", "quality", "total_cost_usd",
                                          "frontier_calls", "mid_calls",
                                          "cheap_extra_samples", "verifier_calls",
                                          "p50_latency_s", "p95_latency_s", "notes"])
        w.writerows(summary_rows)
    print("appended", len(summary_rows), "summary rows to", repo_ledger)


if __name__ == "__main__":
    main()
