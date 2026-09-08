import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
import generate_items as gi


def test_key_consistent_handles_none_solve_text():
    """Regression R5 live-run crash: real caller can return None (empty
    reply); _key_consistent must count it as a non-pass, not crash."""
    v = {"type": "numeric_tol", "value": 5}
    ok, passes, k = gi._key_consistent(
        {"question": "Q?", "verifier": v},
        lambda m, p, k2, s: None, "m", "k", 0)
    assert ok is False and passes == 0 and k == 3
