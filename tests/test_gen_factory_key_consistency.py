"""R5 prereg: K=3 self-consistency key validation. After an item passes the
self_verifier gate, the generator model must re-solve its own question K=3
times; the key is accepted only if >= 2 of 3 solves pass the item's own
verifier on the solve's final-answer region. Otherwise reject with reason
`key_inconsistent` and the raw item captured in detail (<= 400 chars)."""
import json
import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
import generate_items


def _run_batch(fake_call):
    d = tempfile.mkdtemp()
    with mock.patch.object(generate_items, "ITEMS_DIR", d):
        accepted = generate_items.generate_batch(
            5, 1, "m", "k", 0, call_fn=fake_call,
            encode_fn=lambda t: [[0.0]],
            corpus_encode_fn=lambda t: [])
    path = os.path.join(d, "gen_rejects_batch5.jsonl")
    rej = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
    return accepted, rej


def _gen_item_call(call_log, gen_text):
    """Fake call_fn returning gen_text for generation prompts, and logging
    every (prompt, seed) call. Solve prompts are answered by _solve_side."""
    calls = call_log

    def fake_call(model, prompt, key, seed):
        calls.append(prompt)
        return gen_text

    return fake_call


GEN_OK = json.dumps({"question": "What is 2+2?",
                     "answer": "4",
                     "verifier": {"type": "numeric_tol", "value": 4}})

SOLVE_PASS = ("Reasoning step by step. "
              "Final answer: 4")
SOLVE_FAIL = ("Reasoning step by step. "
              "Final answer: 7")


def _split_caller(gen_text, solve_texts):
    """call_fn: generation prompt -> gen_text; solve prompts -> solve_texts
    in order. Distinguishes solve prompts by the SOLVE_PROMPT signature."""
    def fake_call(model, prompt, key, seed):
        if "Final answer:" in prompt and "step" in prompt:
            return solve_texts.pop(0)
        return gen_text
    return fake_call


def test_two_of_three_agreeing_solves_accepted():
    calls = []
    caller = _split_caller(GEN_OK, [SOLVE_PASS, SOLVE_PASS, SOLVE_FAIL])
    accepted, rej = _run_batch(caller)
    assert accepted, "2/3 agreeing solves must accept the item"
    assert not [r for r in rej if r["reason"] == "key_inconsistent"]


def test_zero_agreement_rejected_with_raw_detail():
    caller = _split_caller(GEN_OK, [SOLVE_FAIL, SOLVE_FAIL, SOLVE_FAIL])
    accepted, rej = _run_batch(caller)
    assert not accepted
    r = [x for x in rej if x["reason"] == "key_inconsistent"]
    assert r, "0/3 agreement must produce a key_inconsistent reject"
    assert r[0]["detail"], "detail must carry the raw item JSON"
    assert len(r[0]["detail"]) <= 400
    assert json.loads(r[0]["detail"])["question"] == "What is 2+2?"


def test_call_fn_called_exactly_three_times_for_validation():
    calls = []
    counts = {"n": 0}

    def caller(model, prompt, key, seed):
        if "Final answer:" in prompt and "step" in prompt:
            counts["n"] += 1
            return SOLVE_PASS
        return GEN_OK

    accepted, rej = _run_batch(caller)
    assert accepted
    assert counts["n"] == 3, "validation must make exactly K=3 solve calls"


def test_one_of_three_rejected_majority_strict():
    caller = _split_caller(GEN_OK, [SOLVE_PASS, SOLVE_FAIL, SOLVE_FAIL])
    accepted, rej = _run_batch(caller)
    assert not accepted, "1/3 agreement must reject (majority >= 2 strict)"
    assert [r for r in rej if r["reason"] == "key_inconsistent"]
