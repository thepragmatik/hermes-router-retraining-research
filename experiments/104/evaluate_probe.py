#!/usr/bin/env python3
"""Idea 104 — T012/T013/T024/T025: leakage tests, covariance diagnostics, task-family metrics, label-shuffle, policy economics."""
import os, json
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

ART="/Users/rath/src/idea-worktrees/104-whitened-latent-gain-probe/artifacts/104"
X=np.load(os.path.join(ART,"latent_train.npy")).astype(np.float32)
t=pd.read_parquet(os.path.join(ART,"train_targets.parquet"))
y_bin=((t.strong_correct-t.weak_correct)>0).astype(int).values
evals=t.eval_name.values
oof=np.load(os.path.join(ART,"oof_probs.npz"))
sep=json.load(open(os.path.join(ART,"separability.json")))
out={}

# T013 covariance diagnostics per frozen layer block
def diag(name,M):
    C=np.cov(M.T); ev=np.linalg.eigvalsh(C)[::-1]
    ev=np.maximum(ev,1e-12)
    out[name]={"dim":int(M.shape[1]),"top_eig":float(ev[0]),"median_eig":float(np.median(ev)),
               "cond":float(ev[0]/ev[-1] if ev[-1]>0 else np.inf),
               "anisotropy_top10_var_frac":float(ev[:10].sum()/ev.sum())}
diag("l8",X[:,:960]); diag("l24",X[:,960:1920]); diag("l31",X[:,1920:2880]); diag("genmean",X[:,2880:3840])

# T012 label-shuffle control (collapses to chance?)
rng=np.random.default_rng(104)
ys=y_bin.copy()
for s in range(3):
    rng.shuffle(ys)
    from sklearn.linear_model import LogisticRegression
    from sklearn.decomposition import PCA
    # cheap: probe on PCA-32 of l31 only, 1 fold
    from sklearn.model_selection import train_test_split
    Xtr,Xte,ytr,yte=train_test_split(X[:,1920:2880],ys,test_size=0.3,random_state=0)
    mu,sd=Xtr.mean(0),Xtr.std(0)+1e-6
    p=PCA(n_components=32,random_state=0).fit((Xtr-mu)/sd)
    Ztr=p.transform((Xtr-mu)/sd); Zte=p.transform((Xte-mu)/sd)
    ev=p.explained_variance_; w=1/np.sqrt(np.maximum(ev,1e-5))
    m=LogisticRegression(C=0.3,max_iter=300).fit(Ztr*w,ytr)
    out[f"shuffle_auc_{s}"]=float(roc_auc_score(yte,m.predict_proba(Zte*w)[:,1]))

# T012 join test: row alignment (targets file rows == capture rows, eval_name overlap with frozen table)
tb=pd.read_parquet("/Users/rath/transfer-bundle/analysis/winrate_table.parquet")
tb_tr=tb[tb.split=="train"].reset_index(drop=True)
out["join_ok"]=bool(len(tb_tr)==len(t) and (tb_tr.prompt.astype(str).values==t.key.values).all())

# T024 task-family AUROC for whiten_90 vs bge
fams=pd.Series(evals).value_counts()
fam_metrics={}
for f in fams.index[fams>=200]:
    m=evals==f
    fam_metrics[f]={"n":int(m.sum()),
        "auc_whiten90_s0":float(roc_auc_score(y_bin[m],oof["whiten_90_s0"][m])),
        "auc_bge_s0":float(roc_auc_score(y_bin[m],oof["bge_s0"][m])),
        "auc_task_s0":float(roc_auc_score(y_bin[m],oof["task_s0"][m]))}
out["task_families"]=fam_metrics
deltas=sorted(((v["auc_whiten90_s0"]-v["auc_bge_s0"],k) for k,v in fam_metrics.items()),reverse=True)
out["top_family_share_of_gain"]=float(deltas[0][0]/sum(d for d,_ in deltas)) if sum(d for d,_ in deltas)>0 else None

# T025 policy economics: cost-aware escalation on OOF (whiten_90 vs bge vs v1-referenced random-coverage)
# policy: escalate (pay strong) when p>=tau; else pay weak. Quality = acc of routed model; cost = routed cost.
sc=t.strong_correct.values; wc=t.weak_correct.values; cs=t.cost_s.values; cw=t.cost_w.values
def policy_metrics(p, taus):
    rows=[]
    for tau in taus:
        esc=p>=tau
        acc=np.where(esc,sc,wc).mean(); cost=np.where(esc,cs,cw).mean(); share=float(esc.mean())
        rows.append({"tau":float(tau),"acc":float(acc),"cost":float(cost),"esc_share":share})
    return rows
taus=np.quantile(oof["whiten_90_s0"],np.linspace(0.1,0.95,18))
pol_w=policy_metrics(oof["whiten_90_s0"],taus)
pol_b=policy_metrics(oof["bge_s0"],np.quantile(oof["bge_s0"],np.linspace(0.1,0.95,18)))
# oracle uplift over weak-always, and capture
weak_always_cost=cw.mean(); weak_always_acc=wc.mean(); strong_always_acc=sc.mean(); strong_always_cost=cs.mean()
oracle_esc=y_bin==1
oracle_acc=np.where(oracle_esc,sc,wc).mean(); oracle_cost=np.where(oracle_esc,cs,cw).mean()
def best_frontier(pol, ref_cost):
    # quality gain at matched cost vs weak-always OR cost reduction at matched quality
    best={"quality_gain_at_matched_cost":0.0,"cost_reduction_at_matched_quality":0.0,"row":None}
    for r in pol:
        if abs(r["cost"]-ref_cost)/ref_cost<0.02:  # ~matched cost
            g=r["acc"]-weak_always_acc
            if g>best["quality_gain_at_matched_cost"]: best={"quality_gain_at_matched_cost":g,"row":r}
        if abs(r["acc"]-weak_always_acc)/weak_always_acc<0.01:  # ~matched quality
            cr=1-r["cost"]/ref_cost
            if cr>best["cost_reduction_at_matched_quality"]: best["cost_reduction_at_matched_quality"]=cr
    return best
out["policy"]={
    "weak_always":{"acc":float(weak_always_acc),"cost":float(weak_always_cost)},
    "strong_always":{"acc":float(strong_always_acc),"cost":float(strong_always_cost)},
    "oracle":{"acc":float(oracle_acc),"cost":float(oracle_cost),"esc_share":float(oracle_esc.mean())},
    "whiten90_best":best_frontier(pol_w,weak_always_cost),
    "bge_best":best_frontier(pol_b,weak_always_cost),
}
# oracle-capture: (acc_policy - weak) / (oracle_acc - weak) at similar cost
bw=out["policy"]["whiten90_best"]["row"]
if bw:
    out["policy"]["whiten90_oracle_capture"]=(bw["acc"]-weak_always_acc)/(oracle_acc-weak_always_acc)
bb=out["policy"]["bge_best"]["row"]
if bb:
    out["policy"]["bge_oracle_capture"]=(bb["acc"]-weak_always_acc)/(oracle_acc-weak_always_acc)

json.dump(out,open(os.path.join(ART,"stage0_metrics.json"),"w"),indent=1)
print(json.dumps(out,indent=1)[:3500])
