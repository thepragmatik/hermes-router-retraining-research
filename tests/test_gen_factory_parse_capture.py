"""R6 Task 1 (TDD): not_json rejects must carry the raw generator output
(first 400 chars) in `detail`. Currently detail is empty — RED first."""
import json, os, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402

Q_SEED = "What is twelve plus seven in plain words?"


def tiny_encode(texts, dim=96):
    out = np.zeros((len(texts), dim))
    for i, t in enumerate(texts):
        tl = str(t).lower()
        for j in range(len(tl) - 1):
            h = int(hashlib.md5(tl[j:j + 2].encode()).hexdigest(), 16) % dim
            out[i, h] += 1
        n = np.linalg.norm(out[i])
        if n:
            out[i] /= n
    return out


import hashlib  # noqa: E402


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def test_not_json_reject_carries_raw_output(monkeypatch, tmp_path):
    monkeypatch.setattr(gi, "ITEMS_DIR", str(tmp_path))
    monkeypatch.setattr(gi, "_PROMPT_CACHE", None)
    monkeypatch.setattr(
        gi, "load_prompt_sources",
        lambda root=None: {"winrate_table": [Q_SEED]})
    truncated = 'sure! the item is: {"question"'
    gi.generate_batch(rung=0, n_items=1, model="test/gen", api_key="k",
                      seed_base=0, call_fn=lambda m, p, k, s: truncated,
                      encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    rejects = read_jsonl(os.path.join(str(tmp_path), "gen_rejects_batch0.jsonl"))
    assert len(rejects) == 1 and rejects[0]["reason"] == "not_json"
    assert rejects[0]["detail"] and "sure!" in rejects[0]["detail"]
