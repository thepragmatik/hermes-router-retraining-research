"""Read-only pre-freeze sanity-anchor probe for idea 102 (T002 support).

Uses ONLY the full-information train matrix via the EXACT transform the
deterministic eval split will use (md5 bucketing). No learner, no simulated
log, no gate numbers beyond fold-boundary plausibility. Results feed the
PREREG's sanity-anchor section only.
"""
import hashlib

import numpy as np
import pandas as pd

WT = "/Users/rath/transfer-bundle/analysis/winrate_table.parquet"
PSTRONG = "telemetry/fixtures/v1_train_pstrong.npy"


def main():
    wt = pd.read_parquet(WT)
    tr = wt[wt.split == "train"].reset_index(drop=True)
    p = np.load(PSTRONG).astype(np.float64)
    sc = tr.strong_correct.to_numpy(float)
    wc = tr.weak_correct.to_numpy(float)
    cs = tr.cost_s.to_numpy(float)
    cw = tr.cost_w.to_numpy(float)

    # deterministic 102 fit/eval split: md5("102:{prompt}") % 10000 < 2000 -> eval
    h = tr.prompt.map(lambda s: int(hashlib.md5(f"102:{s}".encode()).hexdigest()[:8], 16) % 10000)
    ev = (h < 2000).to_numpy()
    fit = ~ev
    print("eval rows", int(ev.sum()), "fit rows", int(fit.sum()), "total", len(tr))

    def Q(strong):
        return float(np.where(strong, sc, wc)[ev].mean())

    def C(strong):
        return float(np.where(strong, cs, cw)[ev].mean())

    v1s = p >= 0.30
    print("EVAL: V1 Q=%.5f C=%.7f frac=%.4f" % (Q(v1s), C(v1s), v1s[ev].mean()))
    or0 = (sc - wc) > 0
    print("EVAL: oracle0 Q=%.5f C=%.7f frac=%.4f" % (Q(or0), C(or0), or0[ev].mean()))
    Qo, Co = Q(or0), C(or0)
    Qv, Cv = Q(v1s), C(v1s)
    print("EVAL: oracle lift=%+.5f saving=%+.7f; 35%%/50%% bar: Q>=%.5f C<=%.7f"
          % (Qo - Qv, Cv - Co, Qv + 0.35 * (Qo - Qv), Cv - 0.5 * (Cv - Co)))

    print("train upgrade rows (weak0,strong1) on v1-weak side:",
          int(((wc == 0) & (sc == 1) & ~v1s).sum()))
    print("train downgrade rows (weak1,strong0) on v1-strong side:",
          int(((wc == 1) & (sc == 0) & v1s).sum()))
    print("EVAL v1strong rows", int((v1s & ev).sum()),
          "weak acc there", float(wc[v1s & ev].mean()),
          "strong acc there", float(sc[v1s & ev].mean()))
    print("EVAL v1weak rows", int((~v1s & ev).sum()),
          "weak acc", float(wc[~v1s & ev].mean()),
          "strong acc", float(sc[~v1s & ev].mean()))

    # frozen decile edges on FIT rows; min logged-strong count per decile under L3
    qs = np.quantile(p[fit], np.linspace(0, 1, 11))
    d = np.clip(np.searchsorted(qs, p, side="right") - 1, 0, 9)
    e3 = 0.8 * (p >= 0.30) + 0.1
    strong_log = np.random.default_rng(102000).random(len(p)) < e3
    cnt = np.array([int((strong_log & fit & (d == k)).sum()) for k in range(10)])
    print("fit-row logged-strong count per decile (L3, seed 102000):", cnt.tolist())
    print("min decile logged-strong count:", int(cnt.min()))
    # family plausibility on eval split
    fam = tr.eval_name[ev].value_counts()
    print("eval families:", len(fam), "largest:", fam.head(5).to_dict())


if __name__ == "__main__":
    main()
