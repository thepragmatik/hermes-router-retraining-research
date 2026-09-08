"""R6 Task 3 (TDD): Variant A — solve-answer string agreement (_norm-equal
to the declared `answer`) counts as a consistency signal alongside the
verifier, still requiring >=2 of K=3. No network: fake call_fn."""
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402

ITEM = {"question": "What is 3 + 3?", "answer": "6",
        "verifier": {"type": "exact_match", "value": "six"}}
# NOTE: _norm is text-only (no numeric canonicalization), so the agreement
# signal requires the solve to spell the answer like the declared key; the
# verifier must FAIL on the agreement-matching region for this test.


def solve(text):
    return lambda m, p, k, s: "Solve step by step.\nFinal answer: " + text


def test_key_consistent_accepts_norm_equal_solve():
    # verifier fails on the solve text ("six" != "6" under exact_match),
    # but the solve's final answer is _norm-equal to the declared key "6"
    ok, passes, k = gi._key_consistent(
        ITEM, solve("6"), "test/gen", "k", 1)
    assert (ok, passes, k) == (True, 3, 3)


def test_key_consistent_still_rejects_disagreeing_solves():
    ok, passes, k = gi._key_consistent(
        ITEM, solve("5"), "test/gen", "k", 1)
    assert (ok, passes, k) == (False, 0, 3)


def test_key_consistent_mixed_verifier_and_agreement():
    # 1 of 3 solves verifier-passes ("six"), 2 agree by string ("6")
    texts = ["Final answer: 6", "Final answer: 6", "Final answer: six"]
    calls = {"i": 0}

    def call_fn(m, p, k, s):
        t = texts[calls["i"]]
        calls["i"] += 1
        return t

    ok, passes, k = gi._key_consistent(ITEM, call_fn, "test/gen", "k", 1)
    assert (ok, passes, k) == (True, 3, 3)
