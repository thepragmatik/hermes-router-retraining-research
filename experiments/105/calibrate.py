"""Idea 105 Stage-0 conformal safety envelope (frozen per results/105/PREREG.md).

Global nested-threshold risk control with exact one-sided Clopper-Pearson bounds,
vectorized. Emits results/105/coverage_risk_global.csv.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats as sps

ALPHAS = [0.01, 0.025, 0.05]
DELTA = 0.05
SEEDS = list(range(10))

p = np.load('/tmp/v1p.npy')      # frozen V1 P(strong wins)
sc = np.load('/tmp/sc.npy')
wc = np.load('/tmp/wc.npy')
cs = np.load('/tmp/cost_s.npy')
cw = np.load('/tmp/cost_w.npy')
risk = ((wc == 0) & (sc == 1)).astype(int)   # frozen risk event
s = 1.0 - p                                   # frozen safety score
always_strong_cost = cs.mean()
always_strong_acc = sc.mean()


def calibrate(s_cal, y_cal, alpha, delta=DELTA):
    """Largest-coverage threshold whose CP (1-delta) upper bound <= alpha."""
    order = np.argsort(-s_cal)
    y_sorted = y_cal[order].astype(int)
    n = len(y_cal)
    ks = np.cumsum(y_sorted).astype(int)          # failures among top m
    ms = np.arange(1, n + 1)
    ubs = np.where(ks > 0, sps.beta.ppf(1 - delta, ks + 1, ms - ks),
                   1 - delta ** (1.0 / ms))
    ubs = np.where(ks >= ms, 1.0, ubs)
    ok = np.where(ubs <= alpha)[0]
    if len(ok) == 0:
        return None, 0.0, 1.0
    m = int(ok[-1]) + 1
    return float(s_cal[order][m - 1]), m / n, float(ubs[ok[-1]])


def evaluate(thr, idx):
    accept = s[idx] >= thr
    cov = float(accept.mean())
    if accept.sum() == 0:
        return cov, 0.0, 0.0, 0.0
    return (cov, float(risk[idx][accept].mean()),
            float(np.where(accept, cw[idx], cs[idx]).mean()),
            float(np.where(accept, wc[idx], sc[idx]).mean()))


rows = []
for seed in SEEDS:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(p))
    cal_idx, ev_idx = perm[: int(0.4 * len(p))], perm[int(0.4 * len(p)): int(0.8 * len(p))]
    for alpha in ALPHAS:
        thr, cov_cal, ub = calibrate(s[cal_idx], risk[cal_idx], alpha)
        if thr is None:
            rows.append(dict(seed=seed, alpha=alpha, cal_n=len(cal_idx), threshold=None,
                             cov_cal=cov_cal, cp_ub=ub, cov_ev=0.0, risk_ev=None,
                             cost_ev=None, acc_ev=None, note='NO_SAFE_COVERAGE'))
            continue
        cov_ev, risk_ev, cost_ev, acc_ev = evaluate(thr, ev_idx)
        rows.append(dict(seed=seed, alpha=alpha, cal_n=len(cal_idx), threshold=thr,
                         cov_cal=cov_cal, cp_ub=ub, cov_ev=cov_ev, risk_ev=risk_ev,
                         cost_ev=cost_ev, acc_ev=acc_ev, note=''))

df = pd.DataFrame(rows)
df.to_csv('results/105/coverage_risk_global.csv', index=False)

print('always_strong: cost=%.6f acc=%.4f' % (always_strong_cost, always_strong_acc))
summary = {}
for alpha in ALPHAS:
    d = df[(df.alpha == alpha) & (df.threshold.notna())]
    if len(d) == 0:
        summary[alpha] = 'NO_SAFE_COVERAGE'
        continue
    summary[alpha] = dict(
        folds=len(d), folds_risk_le_alpha=int((d.risk_ev <= alpha).sum()),
        mean_cov=d.cov_ev.mean(), min_cov=d.cov_ev.min(), max_cov=d.cov_ev.max(),
        mean_risk=d.risk_ev.mean(), max_risk=d.risk_ev.max(),
        mean_cost=d.cost_ev.mean(),
        saving_vs_always_strong=1 - d.cost_ev.mean() / always_strong_cost,
        mean_acc=d.acc_ev.mean(), acc_gap=always_strong_acc - d.acc_ev.mean())
print(json.dumps({str(k): v for k, v in summary.items()}, indent=1))
