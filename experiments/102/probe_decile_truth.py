"""One-off read-only probe: per-decile true tau and its correlation with p
on eval rows (explains DRL-pi frontier shape; feeds the correction memo)."""
import hashlib
import sys
import os

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D


def main():
    wt = pd.read_parquet(D.WINRATE_TABLE)
    tr = wt[wt.split == "train"].reset_index(drop=True)
    p = np.load(D.PSTRONG_PATH).astype(np.float64)
    ev = tr.prompt.map(lambda s: int(hashlib.md5(("102:" + s).encode()).hexdigest()[:8], 16) % 10000 < 2000).to_numpy()
    fit = ~ev
    qs = tr.strong_correct.to_numpy(float)
    wc = tr.weak_correct.to_numpy(float)
    tau = qs - wc
    edges = np.quantile(p[fit], np.linspace(0, 1, 11))
    dec = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, 9)
    for k in range(10):
        m = (dec == k) & ev
        print("dec %d n=%5d true_tau=%+.4f P(s=1)=%.3f P(w=1)=%.3f corr(p,tau)=%+.3f"
              % (k, int(m.sum()), tau[m].mean(), qs[m].mean(), wc[m].mean(),
                 float(np.corrcoef(p[m], tau[m])[0, 1]) if m.sum() > 2 else float("nan")))
    # conditional variance of tau given p (is p a sufficient statistic?)
    m_ev = ev
    print("corr(p, tau) on all eval:", float(np.corrcoef(p[m_ev], tau[m_ev])[0, 1]))
    print("Var(tau | p-decile) residual sd:", float(np.std(tau[m_ev] - np.array(
        [np.mean(tau[m_ev][dec[m_ev] == k]) for k in dec[m_ev]]))))


if __name__ == "__main__":
    main()
