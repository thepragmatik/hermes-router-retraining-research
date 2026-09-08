"""R6 Task 4: offline replay of the combined parse-capture + key-agreement
path. Fake call_fn scripted to return (1) fenced-JSON-wrapped valid item,
(2) truncated/garbage JSON, (3) valid item with solving replies. Asserts
accepted/rejected rows and a NON-EMPTY not_json detail. Zero network."""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402
import numpy as np  # noqa: E402
import hashlib  # noqa: E402

Q_SEED = "What is twelve plus seven in plain words?"
V1_Q = "State the boiling point of water in degrees Celsius at one atmosphere"
V1 = json.dumps({"question": V1_Q, "answer": "100 degrees Celsius",
                 "verifier": {"type": "exact_match",
                              "value": "100 degrees Celsius"}})
# fenced-JSON wrap of the same item (strict parse must recover it)
V1_FENCED = "Sure! Here is the item:\n```json\n" + V1 + "\n```"
# truncated generation (not_json; detail must capture the raw text)
TRUNCATED = 'Sure! the item is: {"question": "What is two plus two in words'
# solves end with the declared key "six"; the exact_match verifier scores
# that spelling directly — exercises the full K=3 gate end-to-end through
# generate_batch (the verifier-phrasing-mismatch case is covered standalone
# in tests/test_gen_factory_key_agreement.py, and note that inside
# generate_batch the self-verifier gate runs run_verifier on the DECLARED
# key, so an item whose verifier rejects its own key is rejected before the
# K=3 gate regardless of the agreement signal).
V3_Q = "What is 3 + 3?"
V3 = json.dumps({"question": V3_Q, "answer": "six",
                 "verifier": {"type": "exact_match", "value": "six"}})


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


def _is_solve(prompt):
    return "Final answer:" in prompt and "step" in prompt


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def test_r6_replay_parse_capture_and_agreement(tmp_path, monkeypatch):
    monkeypatch.setattr(gi, "ITEMS_DIR", str(tmp_path))
    monkeypatch.setattr(gi, "_PROMPT_CACHE", None)
    monkeypatch.setattr(
        gi, "load_prompt_sources",
        lambda root=None: {"winrate_table": [Q_SEED],
                           "mf_val_frame": ["Write a short memo about plants"],
                           "mf_test_frame": ["Fix a login traceback"]})
    gens = [V1_FENCED, TRUNCATED, V3]
    idx = {"i": 0}

    def call_fn(model, prompt, key, seed):
        if _is_solve(prompt):
            if "3 + 3" in prompt:
                # solve reply agrees with the declared key "six" by _norm —
                # the Variant A agreement signal is exercised end-to-end
                # through generate_batch (the standalone disagreement case
                # is covered in tests/test_gen_factory_key_agreement.py).
                return "Solve step by step.\nFinal answer: six"
            return "Solve step by step.\nFinal answer: 100 degrees Celsius"
        out = gens[idx["i"]]
        idx["i"] += 1
        return out

    rows = gi.generate_batch(rung=6, n_items=3, model="test/gen",
                             api_key="k", seed_base=0, call_fn=call_fn,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    # 2 accepted: fenced-JSON parse recovery + agreeing solves through the
    # full K=3 gate; the truncated item is rejected with captured detail.
    assert [r["question"] for r in rows] == [V1_Q, V3_Q]
    assert rows[0]["answer"] == "100 degrees Celsius"
    assert rows[1]["answer"] == "six"
    rejects = read_jsonl(os.path.join(str(tmp_path), "gen_rejects_batch6.jsonl"))
    assert len(rejects) == 1
    r = rejects[0]
    assert r["reason"] == "not_json"
    # R6 parse-capture: the not_json detail is NON-EMPTY and carries raw text
    assert r["detail"], "not_json reject must carry raw generator output"
    assert "Sure! the item is:" in r["detail"]
