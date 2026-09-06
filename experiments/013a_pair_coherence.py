"""Prereg 013 + Amendment A — pair coherence of the rescue signal.
Corrected pair universe: 9 non-control models, C(9,2)=36 unordered pairs,
roles assigned on D1 only (higher D1 accuracy = strong). First run VOID
(see 013a-prereg-amendment.md).
$0; test SEALED.
Run: python3 experiments/013a_pair_coherence.py
Out: results/exp013a_pair_coherence.csv ; stdout tee results/EXPERIMENT_013_raw.txt
"""
import hashlib
import os

import numpy as np
import pandas as pd

PK = os.path.expanduser(
    "~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl")
raw = pd.read_pickle(PK)
CONTROL = {"gpt-4-1106-preview", "mistralai/mistral-7b-chat"}
MODELS = ["WizardLM/WizardLM-13B-V1.2", "claude-instant-v1", "claude-v1",
          "claude-v2", "gpt-3.5-turbo-1106",
          "meta/code-llama-instruct-34b-chat", "meta/llama-2-70b-chat",
          "mistralai/mixtral-8x7b-chat", "zero-one-ai/Yi-34B-Chat"]
assert len(MODELS) == 9 and not CONTROL & set(MODELS)


def bin_acc(model):
    return raw[model].fillna(0).astype(int).values


B = {m: bin_acc(m) for m in MODELS}
n = len(raw)
half = np.array([int(hashlib.sha256(str(p).encode()).hexdigest()[:8], 16)
                 % 2 for p in raw["prompt"]])
D1, D2 = half == 0, half == 1
assert D1.sum() + D2.sum() == n and abs(D1.mean() - 0.5) < 0.02

# ---- D1: roles + rescue for all 36 pairs (roles frozen here) -----------
pairs = []
for i, a in enumerate(MODELS):
    for b in MODELS[i + 1:]:
        acc_a, acc_b = float(B[a][D1].mean()), float(B[b][D1].mean())
        wk, st = (a, b) if acc_a < acc_b else (b, a)
        ww = B[wk] < 0.5
        rescue = (ww & (B[st] > 0.5))
        pairs.append({"weak": wk, "strong": st,
                      "acc_weak_d1": min(acc_a, acc_b),
                      "acc_strong_d1": max(acc_a, acc_b),
                      "rescue_d1": float(rescue[D1].mean()),
                      "n_d1": int(D1.sum())})
sel = pd.DataFrame(pairs)
assert len(sel) == 36, len(sel)
sel = sel.sort_values("rescue_d1", ascending=False).reset_index(drop=True)
chosen = pd.concat([sel.head(3), sel.tail(3)])
print("selected pairs (from D1 only; roles frozen):")
print(chosen[["weak", "strong", "acc_weak_d1", "acc_strong_d1",
              "rescue_d1"]].to_string(index=False))

# ---- D2: recompute rescue for the 6 selected pairs ---------------------
rows = []
for _, r in chosen.iterrows():
    ww2 = B[r["weak"]] < 0.5
    rescue2 = (ww2 & (B[r["strong"]] > 0.5))
    rows.append({"weak": r["weak"], "strong": r["strong"],
                 "rescue_d1": float(r["rescue_d1"]),
                 "rescue_d2": float(rescue2[D2].mean()),
                 "n_d2": int(D2.sum())})
out = pd.DataFrame(rows)
os.makedirs("results", exist_ok=True)
out.to_csv("results/exp013a_pair_coherence.csv", index=False)
print("\nD2 verification:")
print(out.to_string(index=False))

top_d2 = float(out.head(3)["rescue_d2"].mean())
bot_d2 = float(out.tail(3)["rescue_d2"].mean())
lift = top_d2 - bot_d2
order_ok = bool((out.head(3)["rescue_d2"] > bot_d2).all())
n_ok = bool((out["n_d2"] >= 2000).all())
print(f"\nD2 top3 mean rescue {top_d2:.4f} bottom3 {bot_d2:.4f} "
      f"lift {lift:+.4f} order_ok={order_ok} n_ok={n_ok}")
if order_ok and lift >= 0.15 and n_ok:
    print("PAIR-COHERENCE COHERENT (pair selection worth a paid study)")
else:
    print("PAIR-COHERENCE INCOHERENT (prompt-idiosyncratic story stands)")
