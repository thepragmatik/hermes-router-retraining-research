#!/usr/bin/env python3
"""Local semantic router CLI. Reads one prompt per line on stdin (or a single
prompt as argv). Prints one JSON line per prompt:
{"prompt_id": int, "decision": "weak"|"strong", "confidence": float}

Decision rule copied verbatim from train_mf_router.py / eval_apgr.py:
  score = w2(v_m(mid) * relu(W1(x)))
  P(strong wins) = sigmoid(score_strong - score_weak); route strong iff >= 0.30.
Threshold pinned from deployment_threshold.md (2026-09-04) — NOT rebalanceable
outside a new preregistration. Val reproduction: routed acc 0.6395,
frac_strong 0.7686 at 0.30 (n=3626).
"""
import json
import sys
import numpy as np
import torch
import torch.nn as nn

THRESHOLD = 0.30
MODEL_DIR = __file__.rsplit("/", 1)[0]
DIM_TEXT, DIM_LATENT = 384, 128


class MF(nn.Module):
    """Same class as train_mf_router.py (checkpoint is a state_dict)."""

    def __init__(self):
        super().__init__()
        self.W1 = nn.Linear(DIM_TEXT, DIM_LATENT)
        self.v_m = nn.Embedding(2, DIM_LATENT)  # 0=weak, 1=strong
        self.w2 = nn.Linear(DIM_LATENT, 1, bias=False)

    def score(self, x, mid):
        return self.w2(self.v_m(mid) * torch.relu(self.W1(x))).squeeze(-1)


_enc = None
_head = None


def _load():
    global _enc, _head
    if _enc is None:
        from sentence_transformers import SentenceTransformer
        _enc = SentenceTransformer("BAAI/bge-small-en-v1.5")
    if _head is None:
        _head = MF()
        _head.load_state_dict(
            torch.load(f"{MODEL_DIR}/mf_router.pt", map_location="cpu",
                       weights_only=True))
        _head.eval()
    return _enc, _head


def route(prompt: str):
    """Returns (decision, confidence) using the training forward pass."""
    enc, head = _load()
    emb = enc.encode([prompt], normalize_embeddings=True).astype(np.float32)
    x = torch.from_numpy(emb)
    with torch.no_grad():
        s_strong = head.score(x, torch.ones(1, dtype=torch.long))
        s_weak = head.score(x, torch.zeros(1, dtype=torch.long))
        p = float(torch.sigmoid(s_strong - s_weak).item())
    return ("strong" if p >= THRESHOLD else "weak"), round(p, 4)


def main():
    lines = sys.stdin.read().splitlines()
    prompts = lines if lines else ([" ".join(sys.argv[1:]).strip()] if sys.argv[1:] else [])
    for i, prompt in enumerate(prompts):
        if not prompt.strip():
            continue
        decision, conf = route(prompt)
        print(json.dumps({"prompt_id": i, "decision": decision,
                          "confidence": conf}))


if __name__ == "__main__":
    main()
