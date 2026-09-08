"""Read-only probe of the corrected-run frontier details (feeds the report)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    res = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "..", "results/102/stage0_corrected.json")))
    reg = res["regimes"]["L3"]["seeds"]
    for lam in [0, 10, 25, 50, 100]:
        qs, cs = [], []
        for sr in reg.values():
            r = max((x for x in sr["frontier"]["drl_pi"] if x["lambda"] == lam),
                    key=lambda x: x["Q"])
            qs.append(r["Q"])
            cs.append(r["C"])
        print("drl lam=%3d meanQ=%.5f meanC=%.7f" % (lam, np.mean(qs), np.mean(cs)))
    v1q = np.mean([sr["v1_fullinfo_eval"]["Q"] for sr in reg.values()])
    v1c = np.mean([sr["v1_fullinfo_eval"]["C"] for sr in reg.values()])
    print("V1 %.5f @ %.7f" % (v1q, v1c))
    tq = np.mean([max((r for r in sr["threshold_frontier"] if r["threshold"] == 0.05),
                      key=lambda r: r["Q"])["Q"] for sr in reg.values()])
    tc = np.mean([max((r for r in sr["threshold_frontier"] if r["threshold"] == 0.05),
                      key=lambda r: r["Q"])["C"] for sr in reg.values()])
    print("threshold t=0.05 %.5f @ %.7f" % (tq, tc))
    rk = [sr["rank"] for sr in reg.values()]
    print("rho_drl mean %.4f  rho_w mean %.4f  wins %d/10"
          % (np.mean([r["spearman_drl"] for r in rk]),
             np.mean([r["spearman_w_inverted"] for r in rk]),
             sum(r["rank_win_vs_direct"] for r in rk)))
    s0 = reg["102000"]
    print("decile tau_hat corrected:", [round(x, 3) for x in
                                        (s0["rank"]["spearman_drl"],)])


if __name__ == "__main__":
    main()
