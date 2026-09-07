"""RED-first tests for gen_factory verifiers (Task 3a, $0, pure-local)."""
import os, sys
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

from verifiers import run_verifier  # noqa: E402


def test_exact_match_pass():
    v = {"type": "exact_match", "value": "Paris"}
    assert run_verifier(v, "The capital of France is Paris.\nFinal answer: Paris") is True


def test_exact_match_fail():
    v = {"type": "exact_match", "value": "Paris"}
    assert run_verifier(v, "Final answer: London") is False


def test_exact_match_case_and_whitespace_normalized():
    v = {"type": "exact_match", "value": "New York"}
    assert run_verifier(v, "final answer:   new   YORK") is True


def test_exact_match_final_answer_region_not_full_text():
    # value appears only in an EARLIER line; the final-answer region is
    # the text after the last "final answer" marker and must not see it.
    v = {"type": "exact_match", "value": "Paris"}
    assert run_verifier(v, "Paris is mentioned here\nFinal answer: London") is False


def test_exact_match_last_line_region_fallback():
    v = {"type": "exact_match", "value": "42"}
    # no marker: last non-empty line is the region
    assert run_verifier(v, "Let me think...\nThe answer is 42") is True
    # value only in earlier text, last line lacks it
    assert run_verifier(v, "42 was an option\nthe answer is something else") is False


def test_numeric_default_tol():
    v = {"type": "numeric_tol", "value": 3.14159}
    assert run_verifier(v, "pi is approximately 3.14159") is True
    # |3.14 - 3.14159| = 0.00159 > default 1e-6
    assert run_verifier(v, "pi is approximately 3.14") is False


def test_numeric_explicit_tol():
    v = {"type": "numeric_tol", "value": 100, "tol": 0.5}
    assert run_verifier(v, "the total is 100.4 units") is True
    assert run_verifier(v, "the total is 101 units") is False


def test_numeric_first_number_wins():
    v = {"type": "numeric_tol", "value": 5, "tol": 1e-6}
    assert run_verifier(v, "I considered 5 options and picked option 9") is True
    v2 = {"type": "numeric_tol", "value": 9, "tol": 1e-6}
    assert run_verifier(v2, "I considered 5 options and picked option 9") is False


def test_numeric_string_value_accepted():
    v = {"type": "numeric_tol", "value": "3.14159"}
    assert run_verifier(v, "pi ~ 3.14159") is True


def test_malformed_answer_returns_false_not_raise():
    assert run_verifier({"type": "numeric_tol", "value": 1}, "") is False
    assert run_verifier({"type": "numeric_tol", "value": 1},
                        "no numbers here at all") is False
    assert run_verifier({"type": "exact_match", "value": "x"}, None) is False


def test_non_string_verifier_value_exact_match_false():
    assert run_verifier({"type": "exact_match", "value": 123},
                        "Final answer: 123") is False
    assert run_verifier({"type": "exact_match", "value": {"a": 1}},
                        "Final answer: x") is False
    assert run_verifier({"type": "exact_match", "value": None},
                        "Final answer: x") is False


def test_numeric_bool_value_false():
    assert run_verifier({"type": "numeric_tol", "value": True}, "1") is False


def test_bad_verifier_shapes_false():
    assert run_verifier(None, "x") is False
    assert run_verifier("exact_match", "x") is False
    assert run_verifier({"type": "regex_magic", "value": "x"}, "x") is False
    assert run_verifier({"type": "numeric_tol"}, "1") is False  # missing value
    assert run_verifier({"type": "numeric_tol", "value": 1, "tol": "abc"},
                        "1") is False  # bad tol


def test_empty_value_exact_match_false():
    assert run_verifier({"type": "exact_match", "value": ""}, "anything") is False
    assert run_verifier({"type": "exact_match", "value": "   "}, "anything") is False
