import numpy as np, pandas as pd, time, sys
from sentence_transformers import SentenceTransformer
wt = pd.read_parquet('/Users/rath/transfer-bundle/analysis/winrate_table.parquet')
tr = wt[wt.split=='train'].reset_index(drop=True)
m = SentenceTransformer('/Users/rath/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a', device='cpu')
t0=time.time()
emb = m.encode(tr.prompt.tolist(), batch_size=128, show_progress_bar=False, normalize_embeddings=True, device='cpu')
print(emb.shape, time.time()-t0, flush=True)
np.save('/Users/rath/src/idea-worktrees/103-bayesian-semantic-memory/experiments/103/train_emb.npy', emb.astype(np.float32))
