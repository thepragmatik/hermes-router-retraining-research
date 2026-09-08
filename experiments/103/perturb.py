"""Gate C: perturbation robustness on train-derived holdout rows (index mod 5 == 4).
Distractor prefix/suffix/format/meta-repetition; measure neighbor Jaccard, posterior delta, route flip, support drop."""
import numpy as np, pandas as pd, json, re

BASE = "/Users/rath/src/idea-worktrees/103-bayesian-semantic-memory"
OUT = f"{BASE}/results/103"
tr = pd.read_parquet(f"{BASE}/experiments/103/train_frame.parquet")
emb = np.load(f"{BASE}/experiments/103/train_emb.npy").astype(np.float32)
sc_w = tr.weak_correct.values.astype(np.float32)
fold_of = tr.fold.values
K, T, KAP, GK = 16, 0.05, 4, 16
gmean_w = sc_w.mean()
n = len(tr)
hold = (np.arange(n) % 5 == 4)
hidx = np.where(hold)[0]
print("holdout rows", len(hidx))

P_w_all = np.load(f"{OUT}/posteriors_weak.npy")
P_s_all = np.load(f"{OUT}/posteriors_strong.npy")
names = ["GLOBAL","TASK","KNN","HIER"]
P_w = {nm: P_w_all[i][hidx] for i, nm in enumerate(names)}
P_s = {nm: P_s_all[i][hidx] for i, nm in enumerate(names)}
n_eff_h = np.load(f"{OUT}/n_eff.npy")[hidx]

# perturbations (deterministic, semantic-preserving)
PFX = "Please answer the following request carefully.\n\n"
SFX = "\n\nRespond to the request above to the best of your ability."
def fmt(p):  # collapse whitespace variants -> formatting change
    return re.sub(r"\s+", " ", p)
def meta(p):  # repeated instruction/meta-language
    return ("Follow the instructions exactly.\n\n" + p + "\n\nFollow the instructions exactly.")

def perturb(p, kind):
    if kind == "prefix": return PFX + p
    if kind == "suffix": return p + SFX
    if kind == "format": return fmt(p)
    if kind == "meta": return meta(p)

# encode perturbed holdout prompts
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('/Users/rath/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a', device='cpu')

def topk(Q, pool, k):
    s = Q @ pool.T
    t = np.argpartition(-s, k, axis=1)[:, :k]
    rows = np.arange(s.shape[0])[:, None]
    o = np.argsort(-s[rows, t], axis=1)
    return t[rows, o], s[rows, t][rows, o]

def posterior(qemb, fd_pool_mask, k=K, T_=T, kap=KAP):
    pool = np.where(fd_pool_mask)[0]
    pi, s = topk(qemb, emb[pool], k)
    d = 1-s; w = np.exp(-d/T_)
    sw = w.sum(1)
    neff = sw**2/(w**2).sum(1) + 1e-12
    pk = (w*sc_w[pool][pi]).sum(1)/sw
    return pk, neff, pi, pool, d

res = []
KINDS = ["prefix","suffix","format","meta"]
for kind in KINDS:
    ptexts = [perturb(p, kind) for p in tr.prompt.to_numpy()[hidx]]
    pe = m.encode(ptexts, batch_size=128, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    # memory pool: exclude each held-out row's fold (use each row's own fold exclusion, batch by fold)
    knn_base = np.zeros(len(hidx)); knn_pert = np.zeros(len(hidx))
    neff_base = np.zeros(len(hidx)); neff_pert = np.zeros(len(hidx))
    jac = np.zeros(len(hidx))
    for fd in np.unique(fold_of[hidx]):
        qm = fold_of[hidx] == fd
        poolm = fold_of != fd
        qe = emb[hidx][qm]; qep = pe[qm]
        pk0, ne0, i0, pool, d0 = posterior(qe, poolm)
        pk1, ne1, i1, pool, d1 = posterior(qep, poolm)
        gidx0 = pool[i0]; gidx1 = pool[i1]
        knn_base[qm] = pk0; knn_pert[qm] = pk1
        neff_base[qm] = ne0; neff_pert[qm] = ne1
        for r in range(qm.sum()):
            jac[np.where(qm)[0][r]] = len(np.intersect1d(gidx0[r], gidx1[r])) / len(np.union1d(gidx0[r], gidx1[r]))
    # route under HIER policy at tau=0.3 (the only tau with nonzero flips) vs base
    p_task_h = P_w["TASK"]  # held from CV; recompute hier posterior for base & pert via same shrinkage
    hier_base = (neff_base*knn_base + KAP*P_w["TASK"]) / (neff_base + KAP)
    hier_pert = (neff_pert*knn_pert + KAP*P_w["TASK"]) / (neff_pert + KAP)
    ps_base = P_s["HIER"]; ps_pert = P_s["HIER"]  # strong posterior unchanged (no perturbed strong scores available) -> note
    # route flip: route strong if gain>tau; use HIER weak + strong posteriors; strong posterior from base CV (approximation noted in report)
    tau = 0.3
    flip = ((ps_base - hier_base > tau) != (ps_pert - hier_pert > tau))
    flip6 = ((ps_base - hier_base > 0.6) != (ps_pert - hier_pert > 0.6))
    # unperturbed nearest-neighbor uncertainty baseline flip rate: use base knn posterior jitter? Instead: baseline = flip rate between base route and route from a second independent kNN (different k)
    # simpler preregistered baseline: flip rate of HIER route between base and k=32 variant
    # compute k=32 base
    hier32 = np.zeros(len(hidx))
    for fd in np.unique(fold_of[hidx]):
        qm = fold_of[hidx] == fd
        poolm = fold_of != fd
        pk32, ne32, _, _, _ = posterior(emb[hidx][qm], poolm, k=32)
        hier32[qm] = (ne32*pk32 + KAP*P_w["TASK"][qm])/(ne32+KAP)
    flip_base = ((ps_base - hier_base > tau) != (ps_base - hier32 > tau))
    res.append(dict(kind=kind, mean_jaccard=float(jac.mean()),
                    mean_post_delta=float(np.abs(hier_pert-hier_base).mean()),
                    route_flip_pp=100*float(flip.mean()), route_flip6_pp=100*float(flip6.mean()),
                    baseline_flip_pp=100*float(flip_base.mean()),
                    mean_neff_base=float(neff_base.mean()), mean_neff_pert=float(neff_pert.mean()),
                    frac_flip_with_support_drop=float((neff_pert[flip] < neff_base[flip]).mean()) if flip.sum() else float('nan')))
    print(res[-1], flush=True)
df = pd.DataFrame(res)
df.to_csv(f"{OUT}/perturbation_results.csv", index=False)
print(df)
