"""R7a prereg: the R6 Variant A string-agreement arm is REMOVED — solve
passes ONLY via the item's own verifier; >=2 of K=3 majority unchanged.
No network: fake call_fn."""
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import generate_items as gi  # noqa: E402

ITEM = {"question": "What is 3 + 3?", "answer": "6",
        "verifier": {"type": "exact_match", "value": "six"}}
# NOTE: _norm is text-only (no numeric canonicalization). The solve string
# "6" is _norm-equal to the declared key but the verifier FAILS on it
# ("six" != "6" under exact_match). Under R6 Variant A this passed via the
# agreement arm; under R7a-strict it must NOT pass.


def solve(text):
    return lambda m, p, k, s: "Solve step by step.\nFinal answer: " + text


def test_key_consistent_rejects_norm_equal_solve():
    # R7a: agreement arm removed — the _norm-equal solve no longer rescues
    # a verifier failure.
    ok, passes, k = gi._key_consistent(
        ITEM, solve("6"), "test/gen", "k", 1)
    assert (ok, passes, k) == (False, 0, 3)


def test_key_consistent_still_rejects_disagreeing_solves():
    ok, passes, k = gi._key_consistent(
        ITEM, solve("5"), "test/gen", "k", 1)
    assert (ok, passes, k) == (False, 0, 3)


def test_key_consistent_verifier_only_majority():
    # All 3 solves return the verifier-passing string "six".
    ok, passes, k = gi._key_consistent(
        ITEM, solve("six"), "test/gen", "k", 1)
    assert (ok, passes, k) == (True, 3, 3)
