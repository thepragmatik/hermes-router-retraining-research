"""One-off read-only probe: what does the DRL-pi and control frontier look
like against V1 and the monotone threshold controls, across all seeds (L3)?
Reads results/102/stage0_results.json only. Feeds the correction decision."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import evaluate as EV

import numpy as np


def main():
    with open(os.path.join(D.REPO_ROOT, D.RESULTS_JSON)) as f:
        res = json.load(f)
    reg = res["regimes"]["L3"]["seeds"]

    # 1) frontier of DRL-pi vs threshold controls: is ANY lambda better than
    # the best threshold-on-p point (Q,C dominated)?
    lam_best = {}
    thr_best = None
    q_thr_best, c_thr_best = -1, None
    for s, sr in reg.items():
        for t in sr["threshold_frontier"]:
            if t["Q"] > q_thr_best or (abs(t["Q"] - q_thr_best) < 1e-9 and
                                       (c_thr_best is None or t["C"] < c_thr_best)):
                q_thr_best, c_thr_best = t["Q"], t["C"]
    print("best threshold-on-p control: Q=%.5f C=%.7f" % (q_thr_best, c_thr_best))

    # aggregate DRL frontier per lambda over seeds
    for lam in D.LAMBDA_GRID:
        qs = [max((r for r in sr["frontier"]["drl_pi"] if r["lambda"] == lam),
                  key=lambda r: r["Q"])["Q"] for sr in reg.values()]
        cs = [max((r for r in sr["frontier"]["drl_pi"] if r["lambda"] == lam),
                  key=lambda r: r["Q"])["C"] for sr in reg.values()]
        print("drl lam=%3d meanQ=%.5f meanC=%.7f" % (lam, np.mean(qs), np.mean(cs)))

    # V1 and oracle means
    v1q = np.mean([sr["v1_fullinfo_eval"]["Q"] for sr in reg.values()])
    v1c = np.mean([sr["v1_fullinfo_eval"]["C"] for sr in reg.values()])
    print("V1: Q=%.5f C=%.7f" % (v1q, v1c))
    orq = np.mean([max(r["Q"] for r in sr["oracle_frontier"]) for sr in reg.values()])
    orc = np.mean([min(r["C"] for r in sr["oracle_frontier"]) for sr in reg.values()])
    print("oracle(lam=0): Q=%.5f C=%.7f -> lift=%.5f saving=%.7f"
          % (orq, orc, orq - v1q, v1c - orc))

    # 2) what does tau_hat actually rank? compare with true tau on eval deciles
    diag = res["diagnostics"]["per_seed"]["102000"]
    print("decile true tau:", [round(x, 4) for x in diag["decile_true_tau"]])
    print("decile tau_hat:", [round(x, 4) for x in diag["decile_tau_hat"]])
    print("decile w_hat:", [round(x, 4) for x in diag["decile_w_hat"]])
    print("spearman: drl=%.4f w_inv=%.4f" %
          (diag["spearman_drl"], diag["spearman_w_inverted"]))

    # 3) min/max of tau_hat and w_hat on eval (scale check)
    # (tau arrays are not persisted; re-derive sign of problem from deciles)


if __name__ == "__main__":
    main()
