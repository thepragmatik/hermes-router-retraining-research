"""Per-fold CV at the best frozen grid point (k=16, T=0.05, kap=4) to apply Gate A (>=8/10 folds),
plus routing frontier, support/OOD diagnostics, and save posteriors for perturbation analysis."""
import numpy as np, pandas as pd, json, time

BASE = "/Users/rath/src/idea-worktrees/103-bayesian-semantic-memory"
OUT = f"{BASE}/results/103"
tr = pd.read_parquet(f"{BASE}/experiments/103/train_frame.parquet")
emb = np.load(f"{BASE}/experiments/103/train_emb.npy").astype(np.float32)
sc_w = tr.weak_correct.values.astype(np.float32)
sc_s = tr.strong_correct.values.astype(np.float32)
cost_w = tr.cost_w.values.astype(np.float32)
cost_s = tr.cost_s.values.astype(np.float32)
fold_of = tr.fold.values
K, T, KAP = 16, 0.05, 4
GK = 16
n = len(tr)

def topk_sims(Q, pool_emb, k):
    nq = Q.shape[0]; out_i = np.empty((nq, k), dtype=np.int32); out_s = np.empty((nq, k), dtype=np.float32)
    CH = 512
    for a in range(0, nq, CH):
        s = Q[a:a+CH] @ pool_emb.T
        t = np.argpartition(-s, k, axis=1)[:, :k]
        rows = np.arange(s.shape[0])[:, None]
        o = np.argsort(-s[rows, t], axis=1)
        out_i[a:a+CH] = t[rows, o]; out_s[a:a+CH] = s[rows, t][rows, o]
    return out_i, out_s

gmean_w = sc_w.mean()
est = {nm: np.full(n, np.nan) for nm in ["GLOBAL","TASK","KNN","HIER"]}
n_eff = np.full(n, np.nan); med = np.full(n, np.nan)
fold_ll = {nm: [] for nm in est}
for fd in range(10):
    qidx = np.where(fold_of == fd)[0]
    trm = fold_of != fd
    tg = tr[["eval_name"]][trm].assign(y=sc_w[trm]).groupby("eval_name").y.agg(["sum","count"])
    groups_tr = tg.index.to_numpy()
    gmean_vec = np.array([tg.loc[g,"sum"]/tg.loc[g,"count"] for g in groups_tr], dtype=np.float32)
    centroids = np.stack([emb[trm][tr.eval_name.to_numpy()[trm]==g].mean(0) for g in groups_tr])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-12
    qe = emb[qidx]
    gsims = qe @ centroids.T
    gtop = np.argpartition(-gsims, GK, axis=1)[:, :GK]
    rows_ = np.arange(gsims.shape[0])[:, None]
    gsim_top = gsims[rows_, gtop]
    gw = np.exp(gsim_top/0.1)
    p_task = (gw*gmean_vec[gtop]).sum(1)/gw.sum(1)
    p_task = (p_task + 16.0*gmean_w)/17.0
    pool = np.where(trm)[0]
    pi, s = topk_sims(qe, emb[pool], K)
    d = 1-s; w = np.exp(-d/T)
    sw = w.sum(1)
    n_eff[qidx] = sw**2/(w**2).sum(1) + 1e-12
    med[qidx] = np.median(d, axis=1)
    p_knn = (w*sc_w[pool][pi]).sum(1)/sw
    p_hier = (sw*p_knn + KAP*p_task)/(sw+KAP)
    y = sc_w[qidx]
    est["GLOBAL"][qidx]=gmean_w; est["TASK"][qidx]=p_task; est["KNN"][qidx]=p_knn; est["HIER"][qidx]=p_hier
    def ll(p):
        p = np.clip(p,1e-6,1-1e-6); return float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean())
    for nm in est: fold_ll[nm].append(ll(est[nm][qidx]))
np.save(f"{OUT}/posteriors_weak.npy", np.stack([est[nm] for nm in est]))
fold_df = pd.DataFrame(fold_ll)
fold_df["HIER_beats_KNN"] = (fold_df.HIER < fold_df.KNN).astype(int)
fold_df["HIER_beats_TASK"] = (fold_df.HIER < fold_df.TASK).astype(int)
fold_df["HIER_beats_GLOBAL"] = (fold_df.HIER < fold_df.GLOBAL).astype(int)
fold_df.to_csv(f"{OUT}/fold_losses.csv", index=False)
print(fold_df)
print("folds HIER<KNN:", fold_df.HIER_beats_KNN.sum(), "/10; HIER<TASK:", fold_df.HIER_beats_TASK.sum(), "/10")
np.save(f"{OUT}/n_eff.npy", n_eff); np.save(f"{OUT}/med_dist.npy", med)
# Save strong posteriors too (same shrinkage for strong target) for routing
est_s = {nm: np.full(n, np.nan) for nm in ["GLOBAL","TASK","KNN","HIER"]}
gmean_s = sc_s.mean()
for fd in range(10):
    qidx = np.where(fold_of == fd)[0]
    trm = fold_of != fd
    tg = tr[["eval_name"]][trm].assign(y=sc_s[trm]).groupby("eval_name").y.agg(["sum","count"])
    groups_tr = tg.index.to_numpy()
    gmean_vec = np.array([tg.loc[g,"sum"]/tg.loc[g,"count"] for g in groups_tr], dtype=np.float32)
    centroids = np.stack([emb[trm][tr.eval_name.to_numpy()[trm]==g].mean(0) for g in groups_tr])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True) + 1e-12
    gsims = emb[qidx] @ centroids.T
    gtop = np.argpartition(-gsims, GK, axis=1)[:, :GK]
    rows_ = np.arange(gsims.shape[0])[:, None]
    gw = np.exp(gsims[rows_, gtop]/0.1)
    p_task = (gw*gmean_vec[gtop]).sum(1)/gw.sum(1)
    p_task = (p_task + 16.0*gmean_s)/17.0
    pool = np.where(trm)[0]
    pi, s = topk_sims(emb[qidx], emb[pool], K)
    d = 1-s; w = np.exp(-d/T); sw = w.sum(1)
    p_knn = (w*sc_s[pool][pi]).sum(1)/sw
    p_hier = (sw*p_knn + KAP*p_task)/(sw+KAP)
    est_s["GLOBAL"][qidx]=gmean_s; est_s["TASK"][qidx]=p_task; est_s["KNN"][qidx]=p_knn; est_s["HIER"][qidx]=p_hier
np.save(f"{OUT}/posteriors_strong.npy", np.stack([est_s[nm] for nm in est]))
print("saved")
