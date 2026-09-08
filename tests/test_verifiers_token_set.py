"""Task 2 (R4): token_set verifier type — normalized token-set overlap >= 0.8.
Additive; exact_match / numeric_tol behavior unchanged."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
from verifiers import run_verifier


def test_token_set_passes_paraphrase_order():
    v = {"type": "token_set", "value": "bears chase elephants",
         "threshold": 0.8}
    assert run_verifier(v, "Chase the bears and the elephants!") is True


def test_token_set_fails_disjoint():
    v = {"type": "token_set", "value": "bears chase elephants"}
    assert run_verifier(v, "cats sleep quietly") is False


def test_exact_match_still_strict():
    v = {"type": "exact_match", "value": "0.80"}
    assert run_verifier(v, "the final answer is 0.8") is False


def test_token_set_below_threshold_fails():
    v = {"type": "token_set", "value": "bears chase elephants quickly"}
    assert run_verifier(v, "bears chase elephants") is False


def test_token_set_empty_value_fails():
    v = {"type": "token_set", "value": "the and of it"}
    assert run_verifier(v, "anything at all") is False
