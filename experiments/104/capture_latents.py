#!/usr/bin/env python3
"""Idea 104 — streaming latent-summary capture (train rows only). Frozen per results/104/PREREG.md."""
import os, json, time
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
import torch, numpy as np, pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer

SNAP="/Users/rath/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-360M-Instruct/snapshots/a10cc1512eabd3dde888204e902eca88bddb4951"
WINRATE="/Users/rath/transfer-bundle/analysis/winrate_table.parquet"
ART="/Users/rath/src/idea-worktrees/104-whitened-latent-gain-probe/artifacts/104"
OUT=os.path.join(ART,"latent_train.npy")
LAYERS=[8,24,31]
MAXNEW=16

tok=AutoTokenizer.from_pretrained(SNAP)
model=AutoModelForCausalLM.from_pretrained(SNAP, torch_dtype=torch.float32).eval()
acts={}
hooks=[model.model.layers[i].register_forward_hook(
    (lambda i: lambda m,inp,out: acts.__setitem__(i, out[0].detach()))(i)) for i in LAYERS]

def summarise(prompt):
    acts.clear()
    text=tok.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)
    enc=tok(text, return_tensors="pt", truncation=True, max_length=2048)
    with torch.no_grad():
        gen=model.generate(**enc, max_new_tokens=MAXNEW, do_sample=False,
                           output_hidden_states=True, output_scores=True, return_dict_in_generate=True)
    feats=[acts[i][-1].float().numpy().reshape(-1) for i in LAYERS]
    feats.append(torch.stack([h[-1][0,-1] for h in gen.hidden_states[1:]]).mean(0).float().numpy().reshape(-1))
    lp=torch.stack(gen.scores).log_softmax(-1)[0]
    top=lp.max(-1).values; ent=-(lp.exp()*lp).sum(-1); srt=lp.sort(-1,descending=True).values
    var=float(top.var()) if lp.shape[0]>1 else 0.0
    logit_feats=np.array([float(top.mean()), float(top.min()), var,
                          float(ent.mean()), float((srt[:,0]-srt[:,1]).mean()), float(lp.shape[0])])
    return np.concatenate(feats+[logit_feats])

def main():
    tb=pd.read_parquet(WINRATE)
    train=tb[tb.split=="train"].reset_index(drop=True).copy()
    train["key"]=train.prompt.astype(str)
    N=len(train); D=960*4+6
    X=np.lib.format.open_memmap(OUT, mode="w+", dtype=np.float16, shape=(N,D))
    t0=time.time()
    for n,p in enumerate(train.prompt.tolist()):
        X[n]=summarise(p).astype(np.float16)
        if n%500==0:
            print(n, round(time.time()-t0,1),"s", flush=True)
            X.flush()
    X.flush()
    train[["key","eval_name","strong_correct","weak_correct","cost_s","cost_w"]].to_parquet(os.path.join(ART,"train_targets.parquet"))
    json.dump({"rows":N,"dim":D,"elapsed_s":time.time()-t0,"layers":LAYERS,"max_new_tokens":MAXNEW},
              open(os.path.join(ART,"capture_meta.json"),"w"))
    print("DONE", N, D, round(time.time()-t0,1),"s")

if __name__=="__main__":
    main()
