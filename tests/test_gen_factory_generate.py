"""RED-first tests for the R0 generator (Task 3b/3c, $0, mock-tested).

ZERO real network: call_fn is always injected; the real OpenRouter caller is
a thin module-level function the tests never execute. The dedup encoder is
injected too (tiny char-bigram encode_fn) so no bge model download happens.
Corpus prompts come from a monkeypatched load_prompt_sources, never parquet.
"""
import hashlib, json, os, subprocess, sys
import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
EV = os.path.join(REPO, "evidence", "gen_factory")
SCRIPT = os.path.join(GEN, "generate_items.py")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402
from verifiers import run_verifier  # noqa: E402

Q_SEED = "What is twelve plus seven in plain words?"
VALID_Q = "State the boiling point of water in degrees Celsius at one atmosphere"
VALID = json.dumps({
    "question": VALID_Q,
    "answer": "100 degrees Celsius",
    "verifier": {"type": "exact_match", "value": "100 degrees Celsius"}})


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
    """R5: distinguish K=3 solve prompts from generation prompts."""
    return "Final answer:" in prompt and "step" in prompt


def solve_ok(answer):
    """Fake model solve response that agrees with `answer`."""
    return "Solve step by step.\\nFinal answer: " + str(answer)


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Redirect all evidence writes to tmp_path; fake corpus; tiny encoder."""
    monkeypatch.setattr(gi, "ITEMS_DIR", str(tmp_path))
    monkeypatch.setattr(gi, "_PROMPT_CACHE", None)
    monkeypatch.setattr(
        gi, "load_prompt_sources",
        lambda root=None: {"winrate_table": [Q_SEED],
                           "mf_val_frame": ["Write a short memo about office plants"],
                           "mf_test_frame": ["Fix the login traceback in the django admin"]})
    return tmp_path


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def test_happy_path_verifier_item_accepted_sha16(env):
    n = 1
    rows = gi.generate_batch(rung=0, n_items=n, model="test/gen", api_key="k",
                             seed_base=17, call_fn=lambda m, p, k, seed: VALID,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert len(rows) == 1
    item = rows[0]
    expected_id = hashlib.sha256(VALID_Q.encode("utf-8")).hexdigest()[:16]
    assert item["item_id"] == expected_id and len(item["item_id"]) == 16
    assert item["question"] == VALID_Q and item["answer"] == "100 degrees Celsius"
    assert item["verifier"] == {"type": "exact_match", "value": "100 degrees Celsius"}
    assert item["gen_model"] == "test/gen"
    # deterministic seed derivation: batch_seed = 1000 + 7919*rung + seed_base
    batch_seed = 1000 + 7919 * 0 + 17
    assert item["seed"] == batch_seed
    # R2 salted batch id: r<rung>_b<batch_seed>_<seed_base%100000>
    assert item["batch_id"] == "r0_b%d_%d" % (batch_seed, 17)
    assert item["ts"].endswith("Z") and "T" in item["ts"]


def test_items_file_schema_exact(env):
    gi.generate_batch(rung=3, n_items=1, model="test/gen", api_key="k",
                      seed_base=0, call_fn=lambda m, p, k, seed: VALID,
                      encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    path = os.path.join(str(env), "items_batch3.jsonl")
    rows = read_jsonl(path)
    assert len(rows) == 1
    assert set(rows[0].keys()) == {"item_id", "question", "answer", "verifier",
                                   "gen_model", "seed", "batch_id", "ts"}


def test_strict_parse_rejects_counted_not_raised(env):
    bad = ["not json at all", "{broken", json.dumps({"question": "q only"}),
           json.dumps({"question": "q", "answer": "a"})]  # missing verifier
    resp = {"gen/1": bad + [VALID]}
    calls = {"i": 0}

    def call_fn(model, prompt, key, seed):
        if _is_solve(prompt):
            return solve_ok("100 degrees Celsius")
        out = resp["gen/1"][calls["i"]]
        calls["i"] += 1
        return out

    rows = gi.generate_batch(rung=0, n_items=5, model="gen/1", api_key="k",
                             seed_base=0, call_fn=call_fn,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert len(rows) == 1  # only the valid JSON survives
    rejects = read_jsonl(os.path.join(str(env), "gen_rejects_batch0.jsonl"))
    assert len(rejects) == 4
    reasons = [r["reason"] for r in rejects]
    assert reasons.count("not_json") == 2 and reasons.count("missing_keys") == 2
    assert all("ts" in r for r in rejects)
    # reject rows never carry the full question text of accepted items
    assert all(VALID_Q not in json.dumps(r) for r in rejects)


def test_verifier_shape_and_self_verifier_gates(env):
    bad_shape = json.dumps({"question": "Name the largest moon of Saturn",
                            "answer": "Titan",
                            "verifier": {"type": "hmm", "value": "Titan"}})
    self_fail = json.dumps({"question": "What is two plus two in words?",
                            "answer": "five",
                            "verifier": {"type": "exact_match", "value": "four"}})
    resp = {"gen/1": [bad_shape, self_fail, VALID]}
    idx = {"i": 0}

    def call_fn(model, prompt, key, seed):
        if _is_solve(prompt):
            return solve_ok("100 degrees Celsius")
        out = resp["gen/1"][idx["i"]]
        idx["i"] += 1
        return out

    rows = gi.generate_batch(rung=0, n_items=3, model="gen/1", api_key="k",
                             seed_base=0, call_fn=call_fn,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert [r["question"] for r in rows] == [VALID_Q]
    rejects = read_jsonl(os.path.join(str(env), "gen_rejects_batch0.jsonl"))
    reasons = [r["reason"] for r in rejects]
    assert "verifier_shape" in reasons and "self_verifier" in reasons


def test_call_fn_exception_counted_never_crashes_batch(env):
    state = {"i": 0}

    def flaky(model, prompt, key, seed):
        state["i"] += 1
        if state["i"] == 1:
            raise RuntimeError("simulated API outage")
        return VALID

    rows = gi.generate_batch(rung=0, n_items=2, model="gen/1", api_key="k",
                             seed_base=0, call_fn=flaky,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert len(rows) == 1
    rejects = read_jsonl(os.path.join(str(env), "gen_rejects_batch0.jsonl"))
    assert any(r["reason"] == "exception" for r in rejects)


def test_dedup_reject_vs_corpus_logged_no_question_text(env):
    near_dup = Q_SEED + "!"  # tiny-encoder sim vs Q_SEED is ~0.99 >= 0.85
    resp = json.dumps({"question": near_dup, "answer": "nineteen",
                       "verifier": {"type": "exact_match", "value": "nineteen"}})
    rows = gi.generate_batch(rung=0, n_items=1, model="gen/1", api_key="k",
                             seed_base=0,
                             call_fn=lambda m, p, k, seed: resp,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert rows == []
    logs = read_jsonl(os.path.join(str(env), "dedup_log.jsonl"))
    assert len(logs) == 1
    rec = logs[0]
    assert rec["source_frame"] == "winrate_table"
    assert rec["max_sim"] >= gi.DEDUP_THRESHOLD
    assert len(rec["item_id"]) == 16
    # NO question text in the dedup log (privacy posture)
    assert Q_SEED not in json.dumps(rec) and near_dup not in json.dumps(rec)
    assert not os.path.exists(os.path.join(str(env), "items_batch0.jsonl"))


def test_dedup_reject_within_batch_itself(env):
    q = "Name the largest planet in the solar system by mass"
    same = json.dumps({"question": q, "answer": "Jupiter",
                       "verifier": {"type": "exact_match", "value": "Jupiter"}})
    again = json.dumps({"question": q + "?", "answer": "Jupiter",
                        "verifier": {"type": "exact_match", "value": "Jupiter"}})
    resp = {"gen/1": [same, again]}
    idx = {"i": 0}

    def call_fn(model, prompt, key, seed):
        if _is_solve(prompt):
            return solve_ok("Jupiter")
        out = resp["gen/1"][idx["i"]]
        idx["i"] += 1
        return out

    rows = gi.generate_batch(rung=0, n_items=2, model="gen/1", api_key="k",
                             seed_base=0, call_fn=call_fn,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert len(rows) == 1  # first accepted, in-batch near-dup rejected
    logs = read_jsonl(os.path.join(str(env), "dedup_log.jsonl"))
    assert len(logs) == 1 and logs[0]["source_frame"] == "in_batch"
    assert logs[0]["max_sim"] >= gi.DEDUP_THRESHOLD


def test_unrelated_items_pass_dedup_gate(env):
    cands = [json.dumps({"question": "State the boiling point of water in "
                                    "degrees Celsius at one atmosphere",
                         "answer": "100 degrees Celsius",
                         "verifier": {"type": "exact_match",
                                      "value": "100 degrees Celsius"}}),
             json.dumps({"question": "Convert 5 kilometers to meters.",
                         "answer": "5000",
                         "verifier": {"type": "numeric_tol", "value": 5000}})]
    resp = {"gen/1": cands}
    idx = {"i": 0}

    solve_answers = {"100 degrees Celsius": "100 degrees Celsius",
                     "5000": "5000"}
    def call_fn(model, prompt, key, seed):
        if _is_solve(prompt):
            return solve_ok("5000") if "kilometers" in prompt \
                else solve_ok("100 degrees Celsius")
        out = resp["gen/1"][idx["i"]]
        idx["i"] += 1
        return out

    rows = gi.generate_batch(rung=0, n_items=2, model="gen/1", api_key="k",
                             seed_base=0, call_fn=call_fn,
                             encode_fn=tiny_encode, corpus_encode_fn=tiny_encode)
    assert len(rows) == 2
    assert read_jsonl(os.path.join(str(env), "dedup_log.jsonl")) == []


def test_cli_help_works_without_api_key():
    clean = {k: v for k, v in os.environ.items()
             if k != "OPENROUTER_API_KEY"}
    r = subprocess.run(["/usr/bin/python3", SCRIPT, "--help"],
                       capture_output=True, text=True, env=clean, timeout=60)
    assert r.returncode == 0, r.stderr[-500:]
    assert "--rung" in r.stdout


def test_cli_real_path_refuses_without_key():
    clean = {k: v for k, v in os.environ.items()
             if k != "OPENROUTER_API_KEY"}
    r = subprocess.run(["/usr/bin/python3", SCRIPT,
                        "--rung", "0", "--n", "0", "--model", "test/gen"],
                       capture_output=True, text=True, env=clean, timeout=60)
    assert r.returncode != 0
    assert "OPENROUTER_API_KEY" in (r.stderr + r.stdout)
    # --n 0 means zero calls were due anyway; refusal happened before any
    # network path could exist.


def test_strict_parse_recovers_json_fenced_block():
    """R1 postmortem fix: 72/100 raw generations were fenced/markdown-wrapped
    JSON; strict parse must recover fenced blocks before rejecting."""
    from generate_items import _strict_parse
    fenced = '```json\n{"question": "Q?", "answer": "42", "verifier": {"type": "exact_match", "value": "42"}}\n```'
    obj = _strict_parse(fenced)
    # R6: _strict_parse returns (item, raw_text)
    assert isinstance(obj, tuple) and obj[0] is not None
    assert isinstance(obj[0], dict) and obj[0]["answer"] == "42"
    assert obj[1] is None
    # prose-wrapped bare JSON also recovers
    obj2 = _strict_parse('Here is the item:\n{"question": "Q2?", "answer": "7", "verifier": {"type": "numeric_tol", "value": 7}}')
    assert isinstance(obj2[0], dict) and obj2[0]["verifier"]["type"] == "numeric_tol"
    # true garbage still rejects (raw text threaded back for capture)
    parsed, raw = _strict_parse("no json here at all")
    assert parsed is None and raw == "no json here at all"


# ---------------- R2: build_prompt must fill GEN_PROMPT placeholders --------

def test_build_prompt_fills_all_placeholders():
    for seed in range(20):
        p = gi.build_prompt(seed)
        assert "{domain}" not in p and "{difficulty}" not in p and "{style}" not in p
        assert p != gi.GEN_PROMPT


def test_build_prompt_rotation_covers_taxonomy():
    prefixes = {gi.build_prompt(s).split(" question ")[0] for s in range(40)}
    assert len(prefixes) >= 6  # >=6 distinct (domain, difficulty, style) heads
