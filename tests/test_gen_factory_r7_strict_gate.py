"""R7a strict gate: solve passes ONLY via run_verifier; a solve whose
final-answer string is _norm-equal to the declared key but whose verifier
fails must NOT count toward the K=3 majority. Zero network."""
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402

STRICT_ITEM = {"question": "What is 6*7 minus 0?", "answer": "41",
               "verifier": {"type": "exact_match", "value": "42"}}
PASS_ITEM = {"question": "What is 6*7?", "answer": "42",
             "verifier": {"type": "exact_match", "value": "42"}}


def seq_call(texts):
    calls = {"i": 0}

    def call_fn(m, p, k, s):
        t = texts[calls["i"] % len(texts)]
        calls["i"] += 1
        return "Solve step by step.\nFinal answer: " + t
    return call_fn


def test_agreement_arm_is_off():
    # solve says "41"; declared key "41" (_norm-equal) but verifier wants
    # "42" -> under R6 Variant A this passed via the agreement arm; under
    # R7a-strict it must not.
    ok, passes, k = gi._key_consistent(
        STRICT_ITEM, seq_call(["41"]), "test/gen", "k", 1)
    assert (ok, passes, k) == (False, 0, 3)


def test_verifier_only_still_counts():
    ok, passes, k = gi._key_consistent(
        PASS_ITEM, seq_call(["42"]), "test/gen", "k", 1)
    assert (ok, passes, k) == (True, 3, 3)
