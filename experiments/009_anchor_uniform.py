"""C0 anchor arm (prereg 009): v1 recipe on 608 UNIFORM random train rows ($0).

Identical trainer to 009_train_two_dollar.run_training but with an EMPTY
purchased-labels file and a uniform-random 608-row labeled set (seed 42).
Out: results/exp009_anchor.csv
"""
import os

import numpy as np
import pandas as pd

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
TAB = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")
DIM_LATENT = 128
SEED = 42

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location(
    "t009", os.path.join(os.path.dirname(__file__), "009_train_two_dollar.py"))
t009 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t009)

torch.manual_seed(SEED)
np.random.seed(SEED)

df = pd.read_parquet(TAB)
tr = df[df.split == "train"].reset_index(drop=True)
va = df[df.split == "val"].reset_index(drop=True)
assert len(tr) == 29193 and len(va) == 3626, (len(tr), len(va))

enc = t009.load_encoder()
E_tr = torch.tensor(enc.encode(list(tr.prompt), batch_size=256,
                               show_progress_bar=False,
                               normalize_embeddings=True).astype(np.float32))
E_va = torch.tensor(enc.encode(list(va.prompt), batch_size=256,
                               show_progress_bar=False,
                               normalize_embeddings=True).astype(np.float32))
va_weak = va.weak_correct.astype(bool).values
va_strong = va.strong_correct.astype(bool).values

y_all = (tr.strong_correct > tr.weak_correct).astype(int).values
rng = np.random.default_rng(SEED)
labeled_idx = np.sort(rng.choice(len(tr), size=608, replace=False))
y_labeled = y_all[labeled_idx]
print(f"C0 anchor: 608 uniform-random rows, seed {SEED}", flush=True)


class MF(nn.Module):
    def __init__(self):
        super().__init__()
        self.W1 = nn.Linear(E_tr.shape[1], DIM_LATENT)
        self.v_m = nn.Embedding(2, DIM_LATENT)
        self.w2 = nn.Linear(DIM_LATENT, 1, bias=False)

    def score(self, x, mid):
        return self.w2(self.v_m(mid) * torch.relu(self.W1(x))).squeeze(-1)


m = MF()
opt = torch.optim.Adam(m.parameters(), lr=3e-4, weight_decay=1e-5)
ids_w = torch.zeros(len(labeled_idx), dtype=torch.long)
ids_s = torch.ones(len(labeled_idx), dtype=torch.long)
yb = torch.tensor(y_labeled.astype(np.float32))
n = len(labeled_idx)
for ep in range(10):
    perm = torch.randperm(n)
    for i in range(0, n, 64):
        b = perm[i:i + 64]
        d = m.score(E_tr[labeled_idx][b], ids_s[b]) - \
            m.score(E_tr[labeled_idx][b], ids_w[b])
        loss = nn.functional.binary_cross_entropy_with_logits(d, yb[b])
        opt.zero_grad()
        loss.backward()
        opt.step()
    print(f"  ep{ep} loss {loss.item():.4f}", flush=True)

with torch.no_grad():
    dv = m.score(E_va, torch.ones(len(va), dtype=torch.long)) - \
         m.score(E_va, torch.zeros(len(va), dtype=torch.long))
    p_va = torch.sigmoid(dv).numpy()

apgr = t009.apgr_score_from_arrays(p_va, va_weak, va_strong)
print(f"C0_uniform_2pct VAL APGR: {apgr:.4f}")
pd.DataFrame([{"arm": "C0_uniform_2pct", "val_apgr": apgr, "seed": SEED,
               "n_labels": 608}]).to_csv("results/exp009_anchor.csv", index=False)
