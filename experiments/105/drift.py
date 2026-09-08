"""Idea 105: stratified (Mondrian) calibration vs global, and drift stress tests.

Strata: the two preregistered strata only (eval_name task family; V1 decision).
Strata with < 200 calibration rows, or whose within-stratum threshold search
yields NO_SAFE_COVERAGE, back off to global calibration (spec FR-007).
Standalone (does not import calibrate.py's main block).
"""
import numpy as np
import pandas as pd
from scipy import stats as sps

ALPHAS = [0.01, 0.025, 0.05]
SEEDS = list(range(10))
N_MIN_STRATUM = 200
DELTA = 0.05

p = np.load('/tmp/v1p.npy')
sc = np.load('/tmp/sc.npy')
wc = np.load('/tmp/wc.npy')
cs = np.load('/tmp/cost_s.npy')
cw = np.load('/tmp/cost_w.npy')
ev = np.load('/tmp/eval_name.npy', allow_pickle=True)
risk = ((wc == 0) & (sc == 1)).astype(int)
s = 1.0 - p
always_strong_cost = cs.mean()
always_strong_acc = sc.mean()


def cp_upper(k, n, delta=DELTA):
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    return sps.beta.ppf(1 - delta, k + 1, n - k) if k > 0 else 1 - delta ** (1 / n)


def calibrate(s_cal, y_cal, alpha, delta=DELTA):
    order = np.argsort(-s_cal)
    y_sorted = y_cal[order].astype(int)
    n = len(y_cal)
    ks = np.cumsum(y_sorted).astype(int)
    ms = np.arange(1, n + 1)
    ubs = np.where(ks > 0, sps.beta.ppf(1 - delta, ks + 1, ms - ks), 1 - delta ** (1.0 / ms))
    ubs = np.where(ks >= ms, 1.0, ubs)
    ok = np.where(ubs <= alpha)[0]
    if len(ok) == 0:
        return None, 0.0, 1.0
    m = int(ok[-1]) + 1
    return float(s_cal[order][m - 1]), m / n, float(ubs[ok[-1]])


# ---------------- Phase 2: stratified calibration ----------------
rows = []
for seed in SEEDS:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(p))
    cal_idx, ev_idx = perm[: int(0.4 * len(p))], perm[int(0.4 * len(p)): int(0.8 * len(p))]
    for alpha in ALPHAS:
        for strat in ['eval_name', 'v1_decision']:
            if strat == 'eval_name':
                cal_g, ev_g = ev[cal_idx], ev[ev_idx]
            else:
                cal_g = (p[cal_idx] >= 0.30).astype('U')
                ev_g = (p[ev_idx] >= 0.30).astype('U')
            acc = np.zeros(len(ev_idx), bool)
            any_none = False
            for g in np.unique(ev_g):
                m_cal = cal_g == g
                m_ev = ev_g == g
                if m_cal.sum() < N_MIN_STRATUM:
                    thr, _, _ = calibrate(s[cal_idx], risk[cal_idx], alpha)
                else:
                    thr, _, _ = calibrate(s[cal_idx][m_cal], risk[cal_idx][m_cal], alpha)
                if thr is None:  # stratum cannot hit target -> global backoff (FR-007)
                    thr, _, _ = calibrate(s[cal_idx], risk[cal_idx], alpha)
                if thr is None:
                    any_none = True
                    break
                acc[m_ev] = s[ev_idx][m_ev] >= thr
            if any_none:
                continue
            r = risk[ev_idx][acc]
            rows.append(dict(seed=seed, alpha=alpha, strat=strat,
                             cov=float(acc.mean()),
                             risk=float(r.mean()) if acc.any() else None,
                             cost=float(np.where(acc, cw[ev_idx], cs[ev_idx]).mean()),
                             acc=float(np.where(acc, wc[ev_idx], sc[ev_idx]).mean())))

print('strat rows collected:', len(rows))
dfs = pd.DataFrame(rows)
assert len(dfs) > 0, 'no stratified rows produced'
dfs.to_csv('results/105/coverage_risk_stratified.csv', index=False)

recs = []
for (st, a), d in dfs.groupby(['strat', 'alpha']):
    recs.append(dict(strat=st, alpha=a, folds=len(d),
                     mean_cov=d["cov"].mean(), mean_risk=d["risk"].mean(), max_risk=d["risk"].max(),
                     folds_risk_le=int((d["risk"] <= a).sum()),
                     mean_cost=d["cost"].mean(), saving=1 - d["cost"].mean() / always_strong_cost,
                     mean_acc=d["acc"].mean()))
gsum = pd.DataFrame(recs)
print('=== STRATIFIED (mean across 10 folds) ===')
print(gsum.to_string(index=False))

# ---------------- Phase 3: drift stress (train rows only) ----------------
rng = np.random.default_rng(0)
perm = rng.permutation(len(p))
cal_idx, ev_idx = perm[: int(0.4 * len(p))], perm[int(0.4 * len(p)): int(0.8 * len(p))]
alpha = 0.01
thr, _, _ = calibrate(s[cal_idx], risk[cal_idx], alpha)
res = []


def drift_eval(name, ev_idx_d, s_shift=None):
    y = risk[ev_idx_d]
    acc = (s_shift if s_shift is not None else s[ev_idx_d]) >= thr
    r = float(y[acc].mean()) if acc.any() else None
    ks_p = float(sps.ks_2samp(s[cal_idx], s_shift if s_shift is not None else s[ev_idx_d]).pvalue)
    alarm = (r is not None and r > alpha) or ks_p < 0.01
    res.append(dict(fixture=name, eval_n=len(ev_idx_d), cov=float(acc.mean()),
                    emp_risk=r, ks_p=ks_p, alarm=bool(alarm),
                    action='reduce/disable envelope' if alarm else 'keep'))


drift_eval('in-distribution control', ev_idx)
fams = np.unique(ev[ev_idx])
pick = np.isin(ev[ev_idx], np.random.default_rng(1).choice(fams, 3, replace=False))
drift_eval('task-mix reweight (3 families only)', ev_idx[pick])
drift_eval('score-distribution shift (+0.05)', ev_idx, s_shift=s[ev_idx] + 0.05)
counts = pd.Series(ev[ev_idx]).value_counts()
rare = list(counts[counts <= counts.quantile(0.05)].index)
drift_eval('rare/OOD-like task families', ev_idx[np.isin(ev[ev_idx], rare)])
s_noisy = np.clip(s[ev_idx] + np.random.default_rng(2).normal(0, 0.05, len(ev_idx)), 0, 1)
drift_eval('score revision noise (sd=0.05)', ev_idx, s_shift=s_noisy)
# user-controlled manipulation simulation: adversarial score push (+0.2 safety
# inflates acceptance; detector must fire on the score-distribution change)
drift_eval('manipulation: adversarial score push (+0.2)', ev_idx, s_shift=np.clip(s[ev_idx] - 0.2, 0, 1))

dfd = pd.DataFrame(res)
dfd.to_csv('results/105/drift_stress.csv', index=False)
print('\n=== DRIFT STRESS (alpha=0.01 global envelope) ===')
print(dfd.to_string(index=False))
