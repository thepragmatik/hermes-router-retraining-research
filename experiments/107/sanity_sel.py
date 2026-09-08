#!/usr/bin/env python3
"""Sanity diagnostics for the Stage-0 selected portfolio (read-only)."""
import os

import numpy as np
import pandas as pd

wr = pd.read_parquet(os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet"))
sp = dict(zip(wr.prompt, wr.split))
raw = pd.read_pickle(os.path.expanduser("~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl"))
raw["split"] = raw.prompt.map(sp)
tr = raw[raw.split == "train"]

w = tr["mistralai/mistral-7b-chat"].fillna(0).astype(int).to_numpy()
y = tr["zero-one-ai/Yi-34B-Chat"].fillna(0).astype(int).to_numpy()
g = tr["gpt-3.5-turbo-1106"].fillna(0).astype(int).to_numpy()
s = tr["gpt-4-1106-preview"].fillna(0).astype(int).to_numpy()

sel = [w, y, g]
print("sel oracle        ", round(float(np.vstack(sel).max(0).mean()), 4))
print("always gpt-3.5 acc", round(float(g.mean()), 4))
print("weak+yi oracle    ", round(float(np.vstack([w, y]).max(0).mean()), 4))
print("weak+yi+gpt4 orac ", round(float(np.vstack([w, y, g, s]).max(0).mean()), 4))
print("weak+gpt4 oracle  ", round(float(np.vstack([w, s]).max(0).mean()), 4))
print("gpt4 acc          ", round(float(s.mean()), 4))
# conditional rescue structure
print("P(yi ok | gpt3.5 fail)", round(float(y[g == 0].mean()), 4),
      " P(gpt3.5 ok | yi fail)", round(float(g[y == 0].mean()), 4))
