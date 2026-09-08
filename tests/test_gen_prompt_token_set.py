"""Task 4 (R4): GEN_PROMPT must carry the pre-registered verifier-preference
line (token_set for phrases, numeric_tol for numbers, exact_match for short
single tokens) so build_prompt output reaches the generator."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
import generate_items


def test_build_prompt_contains_token_set_preference():
    for seed in range(0, 30):
        assert "token_set" in generate_items.build_prompt(seed)


def test_prompt_preference_covers_all_three_types():
    p = generate_items.build_prompt(0)
    assert "numeric_tol" in p and "exact_match" in p
