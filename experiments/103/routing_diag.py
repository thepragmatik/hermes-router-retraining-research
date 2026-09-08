"""Routing frontier (Gate B), support/OOD diagnostics (Gate D), perturbation robustness (Gate C)."""
import numpy as np, pandas as pd, json

BASE = "/Users/rath/src/idea-worktrees/103-bayesian-semantic-memory"
OUT = f"{BASE}/results/103"
tr = pd.read_parquet(f"{BASE}/experiments/103/train_frame.parquet")
emb = np.load(f"{BASE}/experiments/103/train_emb.npy").astype(np.float32)
sc_w = tr.weak_correct.values.astype(np.float32)
sc_s = tr.strong_correct.values.astype(np.float32)
cost_w = tr.cost_w.values.astype(np.float32)
cost_s = tr.cost_s.values.astype(np.float32)
fold_of = tr.fold.values
n = len(tr)
names = ["GLOBAL","TASK","KNN","HIER"]
P_w = np.load(f"{OUT}/posteriors_weak.npy")  # order = names
P_s = np.load(f"{OUT}/posteriors_strong.npy")
n_eff = np.load(f"{OUT}/n_eff.npy"); med = np.load(f"{OUT}/med_dist.npy")
P_w = {nm: P_w[i] for i, nm in enumerate(names)}
P_s = {nm: P_s[i] for i, nm in enumerate(names)}

# --- Gate B: routing frontier. Policy per estimator: route strong if E[rescue]*(delta_quality)
# justifies cost delta; diagnostic: always-route-cheap (weak), always-strong, oracle, V1-ish (prior-based).
rows = []
for nm in names:
    # expected marginal gain of strong over weak = P_s - P_w
    gain = P_s[nm] - P_w[nm]
    # route strong where gain > cost_ratio threshold tau; tau grid
    for tau in [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]:
        route_s = gain > tau
        q = route_s*sc_s + (~route_s)*sc_w
        c = route_s*cost_s + (~route_s)*cost_w
        rows.append(dict(estimator=nm, tau=tau, quality=q.mean(), cost=c.mean(),
                         frac_strong=route_s.mean()))
fr = pd.DataFrame(rows)
fr.to_csv(f"{OUT}/frontier.csv", index=False)
# matched-cost comparison: for each estimator, pick tau minimizing cost subject to quality>=base (always-weak GLOBAL tau=inf)
def pareto_points(nm):
    sub = fr[fr.estimator==nm].sort_values("cost")
    best = sub.groupby("cost").quality.max().reset_index()
    return best
g_task = fr[fr.estimator=="TASK"]
print("== frontier summary (per estimator, best quality at <= mean cost of always-strong/always-weak anchors) ==")
for nm in names:
    sub = fr[fr.estimator==nm]
    print(nm, "maxQ", sub.quality.max().round(4), "minC", sub.cost.min().round(6))

# Reference policies
ref = {}
ref["always_weak"] = (sc_w.mean(), cost_w.mean())
ref["always_strong"] = (sc_s.mean(), cost_s.mean())
# oracle
o_s = sc_s >= sc_w
oracle_q = np.where(sc_s>sc_w, sc_s, sc_w).mean()
oracle_c = np.where(sc_s>sc_w, cost_s, cost_w).mean()
ref["oracle_pair"] = (oracle_q, oracle_c)
# quality at matched cost: compare HIER policy vs TASK policy with cost of TASK policy
sub_h = fr[fr.estimator=="HIER"]; sub_t = fr[fr.estimator=="TASK"]
res_b = {}
for _, r in sub_t.iterrows():
    tau_t, q_t, c_t = r.tau, r.quality, r.cost
    # HIER point with cost <= c_t*1.02 maximizing quality
    cand = sub_h[sub_h.cost <= c_t*1.02]
    if len(cand):
        b = cand.loc[cand.quality.idxmax()]
        res_b[tau_t] = dict(task_q=q_t, task_c=c_t, hier_q=b.quality, hier_c=b.cost,
                            dQ_pp=100*(b.quality-q_t), dC_rel=(b.cost-c_t)/c_t)
matched = pd.DataFrame(res_b).T
matched.to_csv(f"{OUT}/matched_cost_comparison.csv")
print(matched.head(10))

# --- Gate D: support informativeness. low-support = n_eff < 5 (frozen threshold), OOD med dist > 0.6
sup_low = n_eff < 5
ood = (n_eff < 5) | (med > 0.6)
y = sc_w
def brier(p, y): return float(((p-y)**2).mean())
def ll(p, y):
    p = np.clip(p, 1e-6, 1-1e-6); return float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean())
diag = {}
for nm in names:
    diag[nm] = dict(
        brier_low=brier(P_w[nm][sup_low], y[sup_low]), brier_high=brier(P_w[nm][~sup_low], y[~sup_low]),
        ll_low=ll(P_w[nm][sup_low], y[sup_low]), ll_high=ll(P_w[nm][~sup_low], y[~sup_low]),
        n_low=int(sup_low.sum()), n_high=int((~sup_low).sum()))
json.dump(diag, open(f"{OUT}/support_diagnostics.json","w"), indent=1)
print(json.dumps(diag, indent=1))
print("sup_low frac", sup_low.mean(), "ood frac", ood.mean())
np.save(f"{OUT}/sup_low.npy", sup_low); np.save(f"{OUT}/ood.npy", ood)
