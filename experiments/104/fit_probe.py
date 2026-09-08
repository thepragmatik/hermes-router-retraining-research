#!/usr/bin/env python3
"""Idea 104 — Stage-0 probe experiment per results/104/PREREG.md (frozen gates)."""
import os, json, hashlib
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

ART="/Users/rath/src/idea-worktrees/104-whitened-latent-gain-probe/artifacts/104"
X=np.load(os.path.join(ART,"latent_train.npy")).astype(np.float32)  # (29193, 3846)
t=pd.read_parquet(os.path.join(ART,"train_targets.parquet"))
y_gain=(t.strong_correct - t.weak_correct).values.astype(int)  # escalation utility target
y_bin=(y_gain>0).astype(int)  # weak-fails/strong-wins vs rest
evals=t.eval_name.values
N=len(t); D=X.shape[1]
print("N,D:",N,D,"gain rate:",y_bin.mean())

# feature slices
SL=lambda a,b: slice(a,b)
l8=SL(0,960); l24=SL(960,1920); l31=SL(1920,2880); genm=SL(2880,3840); lg=SL(3840,3846)
HIDDEN=np.concatenate([X[:,l8],X[:,l24],X[:,l31],X[:,genm]],axis=1)  # raw latent (3840)
LOGIT=X[:,lg]

# prompt BGE baseline (frozen): compute embeddings
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
from sentence_transformers import SentenceTransformer
bge=SentenceTransformer("/Users/rath/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/"+os.listdir("/Users/rath/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots")[0])
bpath=os.path.join(ART,"bge_train.npy")
if os.path.exists(bpath):
    BGE=np.load(bpath)
else:
    BGE=bge.encode(t["key"].tolist(), batch_size=256, show_progress_bar=False, normalize_embeddings=True).astype(np.float32)
    np.save(bpath,BGE)
print("BGE:",BGE.shape)

# task-only baseline
TASK=pd.get_dummies(evals).values.astype(np.float32)

# folds: md5(row index + salt) blocks, seed 104
def folds_for(salt):
    h=np.array([int(hashlib.md5(f"104:{salt}:{i}".encode()).hexdigest()[:8],16) for i in range(N)])
    return h%5

C_GRID=[0.03,0.1,0.3,1.0,3.0]
def fit_probe(Xtr,ytr,Xte,C):
    best=None;bestauc=None
    # inner 3-fold for C selection (train-fold only)
    inner=StratifiedKFold(3,shuffle=True,random_state=7)
    for c in C_GRID:
        aucs=[]
        for itr,ite in inner.split(Xtr,ytr):
            m=LogisticRegression(C=c,max_iter=500).fit(Xtr[itr],ytr[itr])
            p=m.predict_proba(Xtr[ite])[:,1]
            if len(np.unique(ytr[ite]))>1: aucs.append(roc_auc_score(ytr[ite],p))
        a=np.mean(aucs)
        if bestauc is None or a>bestauc: bestauc=a;best=c
    m=LogisticRegression(C=best,max_iter=1000).fit(Xtr,ytr)
    return m,m.predict_proba(Xte)[:,1],best

def zfit(Xtr):
    mu=Xtr.mean(0); sd=Xtr.std(0)+1e-6; return mu,sd

def variant_feats(name, Xtr, Xte):
    if name=="raw":
        mu,sd=zfit(Xtr); return (Xtr-mu)/sd,(Xte-mu)/sd
    if name.startswith("pca") or name.startswith("whiten"):
        k=int(name.split("_")[1]) if "_" in name else None
        mu=Xtr.mean(0); sd=Xtr.std(0)+1e-6
        Xtrz=(Xtr-mu)/sd
        if k is None:
            p=PCA(n_components=0.90,random_state=0).fit(Xtrz)
        else:
            p=PCA(n_components=k,random_state=0).fit(Xtrz)
        V=p.components_.T; ev=p.explained_variance_
        ptr=Xtrz@V; pte=((Xte-mu)/sd)@V
        if name.startswith("whiten"):
            floor=max(1e-5,1e-4*ev.max())
            w=1.0/np.sqrt(np.maximum(ev,floor))
            return ptr*w, pte*w
        return ptr,pte
    raise ValueError(name)

def run_variant(featname, salt):
    fl=folds_for(salt)
    oof=np.zeros(N)
    for f in range(5):
        tr=np.where(fl!=f)[0]; te=np.where(fl==f)[0]
        if featname=="bge": A,B=BGE[tr],BGE[te]
        elif featname=="logit":
            mu,sd=zfit(LOGIT[tr]); A,B=(LOGIT[tr]-mu)/sd,(LOGIT[te]-mu)/sd
        elif featname=="task": A,B=TASK[tr],TASK[te]
        else: A,B=variant_feats(featname,HIDDEN[tr],HIDDEN[te])
        _,p,c=fit_probe(A,y_bin[tr],B,None)
        oof[te]=p
    auc=roc_auc_score(y_bin,oof)
    return auc,oof

FEATURES=["bge","logit","task","raw","pca_16","pca_32","pca_64","pca_90","whiten_16","whiten_32","whiten_64","whiten_90"]
results={}
oof_store={}
for salt in [0,1]:
    for f in FEATURES:
        auc,oof=run_variant(f,salt)
        results[f"{f}_s{salt}"]=auc
        oof_store[f"{f}_s{salt}"]=oof
        print(f,salt,round(auc,4),flush=True)
json.dump(results,open(os.path.join(ART,"separability.json"),"w"),indent=1)
np.savez_compressed(os.path.join(ART,"oof_probs.npz"),**oof_store)
print(json.dumps(results,indent=1))
