"""Stage-0 evaluation for Idea 103: Bayesian Semantic Performance Memory (train-only).
Frozen per results/103/PREREG.md. $0. Test split untouched.
Estimators for weak-model success p_w, strong-model success p_s:
  GLOBAL, TASK, KNN raw, HIER (empirical-Bayes shrinkage).
Also routing frontier, support diagnostics, perturbation robustness, OOD.
"""
import numpy as np, pandas as pd, json, sys, time

BASE = "/Users/rath/src/idea-worktrees/103-bayesian-semantic-memory"
OUT = f"{BASE}/results/103"
tr = pd.read_parquet(f"{BASE}/experiments/103/train_frame.parquet")
emb = np.load(f"{BASE}/experiments/103/train_emb.npy").astype(np.float32)
assert len(tr) == len(emb)
sc_w = tr.weak_correct.values.astype(np.float32)
sc_s = tr.strong_correct.values.astype(np.float32)
cost_w = tr.cost_w.values.astype(np.float32)
cost_s = tr.cost_s.values.astype(np.float32)
fold_of = tr.fold.values
groups = np.sort(tr.eval_name.unique())

KS = [8, 16, 32, 64]
TS = [0.05, 0.1, 0.2]
KAPPAS = [4, 16, 64]
SUP_THR = [2, 5, 10]
OOD_DIST = 0.6

def topk_sims(Q, pool_emb, k):
    """Q: (nq,d) normalized; pool_emb: (np,d). Returns idx (nq,k) into pool, sims."""
    nq = Q.shape[0]; out_i = np.empty((nq, k), dtype=np.int32); out_s = np.empty((nq, k), dtype=np.float32)
    CH = 512
    for a in range(0, nq, CH):
        s = Q[a:a+CH] @ pool_emb.T
        t = np.argpartition(-s, k, axis=1)[:, :k]
        rows = np.arange(s.shape[0])[:, None]
        o = np.argsort(-s[rows, t], axis=1)
        out_i[a:a+CH] = t[rows, o]; out_s[a:a+CH] = s[rows, t][rows, o]
    return out_i, out_s

def neighbor_stats(qidx, fold_of, k, T):
    """kNN with same-fold exclusion. Returns n_eff, med_d, w, y_w, y_s, nb_global_idx per query."""
    f = fold_of[qidx]
    # neighbor pool excludes each query's own fold -> do per-fold batch
    res = {}
    for fd in np.unique(f):
        qm = f == fd
        pool = np.where(fold_of != fd)[0]
        pi, s = topk_sims(emb[qidx[qm]], emb[pool], k)
        d = 1 - s
        w = np.exp(-d / T)
        n_eff = w.sum(1)**2 / (w**2).sum(1) + 1e-12
        med = np.median(d, axis=1)
        yw = sc_w[pool][pi]; ys = sc_s[pool][pi]
        n = int(qm.sum())
        res[fd] = dict(rows=qidx[qm], n_eff=n_eff, med=med, w=w, yw=yw, ys=ys)
    return res

def logloss(p, y):
    p = np.clip(p, 1e-6, 1-1e-6)
    return float(-(y*np.log(p) + (1-y)*np.log(1-p)).mean())

def brier(p, y):
    return float(((p-y)**2).mean())

def run_cv(k, T, kap, sup_thr):
    """10-fold leave-group-out CV. Returns per-estimator losses on weak target + ranking metric."""
    n = len(tr)
    est = {name: np.full(n, np.nan) for name in ["GLOBAL","TASK","KNN","HIER"]}
    meta = dict(n_eff=np.full(n, np.nan), med=np.full(n, np.nan))
    gmean_w = sc_w.mean()
    # task priors computed per fold from training rows only
    for fd in range(10):
        qidx = np.where(fold_of == fd)[0]
        if len(qidx)==0: continue
        trm = fold_of != fd
        # Task prior: leave-group-out -> held-out groups have no train data by construction,
        # so the task-family prior is the EMBEDDING-KNN-of-groups prior: for each query,
        # average weak success of the kap strongest *group-mean* neighbors among TRAIN groups,
        # shrunk to global. This is the preregistered "task prior" in a strict LGO design.
        tg = tr[["eval_name"]][trm].assign(y=sc_w[trm]).groupby("eval_name").y.agg(["sum","count"])
        groups_tr = tg.index.to_numpy()
        gmean_vec = np.array([tg.loc[g, "sum"] / tg.loc[g, "count"] for g in groups_tr], dtype=np.float32)
        # group centroid in embedding space (train rows only)
        gids = pd.Series(groups_tr)
        centroids = np.stack([emb[trm][ (tr.eval_name.to_numpy()[trm] == g) ].mean(0) for g in groups_tr])
        centroids /= np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-12
        qe = emb[qidx]
        gsims = qe @ centroids.T  # (nq, G)
        gk = 16
        gtop = np.argpartition(-gsims, gk, axis=1)[:, :gk]
        rows_ = np.arange(gsims.shape[0])[:, None]
        gtops = np.sort(gtop, axis=1)
        gsim_top = gsims[rows_, gtop]
        gw = np.exp(gsim_top / 0.1)
        p_task_rows = (gw * gmean_vec[gtop]).sum(1) / gw.sum(1)
        kap_task_base = 16.0
        p_task_rows = (p_task_rows + kap_task_base * gmean_w) / (1.0 + kap_task_base)

        ns = neighbor_stats(qidx, fold_of, k, T)
        pos_all = np.searchsorted(qidx, np.arange(len(tr)))
        for fdkey, d in ns.items():
            rows = d["rows"]
            pos = pos_all[rows]
            sw = d["w"].sum(1)
            p_knn = (d["w"] * d["yw"]).sum(1) / sw
            # hierarchical: shrink knn toward task prior with kap pseudo-counts
            p_h = (sw * p_knn + kap * p_task_rows[pos]) / (sw + kap)
            est["GLOBAL"][rows] = gmean_w
            est["TASK"][rows] = p_task_rows[pos]
            est["KNN"][rows] = p_knn
            est["HIER"][rows] = p_h
            meta["n_eff"][rows] = d["n_eff"]; meta["med"][rows] = d["med"]
    out = {}
    for name in est:
        p = est[name]; y = sc_w
        out[name] = dict(logloss=logloss(p, y), brier=brier(p, y))
    # pairwise gain ranking metric: rank strong vs weak by predicted rescue prob
    # rescue = s - w; predicted rescue posterior
    return out, est, meta

t0 = time.time()
grid_res = []
for k in KS:
    for T in TS:
        for kap in KAPPAS:
            losses, est, meta = run_cv(k, T, kap, 5)
            grid_res.append(dict(k=k, T=T, kap=kap, **{f"{n}_{m}": v for n, d in losses.items() for m, v in d.items()}))
            print(f"k={k} T={T} kap={kap} HIER={losses['HIER']['logloss']:.5f} KNN={losses['KNN']['logloss']:.5f} TASK={losses['TASK']['logloss']:.5f} GLOBAL={losses['GLOBAL']['logloss']:.5f}", flush=True)
pd.DataFrame(grid_res).to_csv(f"{OUT}/cv_grid.csv", index=False)
print("cv done", time.time()-t0, flush=True)
