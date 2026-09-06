"""Unit tests for the shadow A/B replay harness. Synthetic 5-row frame with
hand-computed expectations — no model calls, no parquet, no network."""
import sys
from importlib import util as ilu
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = ilu.spec_from_file_location("ab007", REPO / "experiments" / "007_shadow_ab_eval.py")
ab = ilu.module_from_spec(_spec)
_spec.loader.exec_module(ab)  # experiments/ has no __init__.py


@pytest.fixture
def frame():
    return pd.DataFrame({
        "prompt": [f"p{i}" for i in range(5)],
        "strong_correct": [1, 1, 0, 0, 1],
        "weak_correct":   [0, 1, 1, 0, 0],
        "cost_s": [10.0] * 5,
        "cost_w": [1.0] * 5,
    })

DECISIONS = np.array(["strong", "weak", "strong", "weak", "strong"])
WEAK = np.array(["weak"] * 5)


def test_router_policy(frame):
    r = ab.simulate(frame, DECISIONS)
    assert r["acc"] == pytest.approx(0.6)          # rows 0,1,4 correct
    assert r["frac_strong"] == pytest.approx(0.6)
    assert r["cost_mean"] == pytest.approx(6.4)    # (3*10 + 2*1) / 5
    assert r["n"] == 5


def test_always_arms(frame):
    s = ab.simulate(frame, np.array(["strong"] * 5))
    w = ab.simulate(frame, WEAK)
    assert s["acc"] == pytest.approx(0.6) and s["cost_mean"] == pytest.approx(10.0)
    assert w["acc"] == pytest.approx(0.4) and w["cost_mean"] == pytest.approx(1.0)


def test_oracle(frame):
    assert ab.oracle_acc(frame) == pytest.approx(0.8)  # per-row max: 1,1,1,0,1


def test_random_seeded_reproducible(frame):
    d1 = ab.random_decisions(frame, frac=0.6, seed=7)
    d2 = ab.random_decisions(frame, frac=0.6, seed=7)
    assert list(d1) == list(d2)
    assert 0.4 <= (d1 == "strong").mean() <= 0.8   # small-n tolerance


def test_cost_parity_frac():
    # random cost = f*10 + (1-f)*1 ; match 6.4  ->  f = 0.6
    assert ab.cost_parity_frac(10.0, 1.0, 6.4) == pytest.approx(0.6)


def test_paired_bootstrap_contains_point(frame):
    r = ab.simulate(frame, DECISIONS)
    w = ab.simulate(frame, WEAK)
    lo, hi = ab.paired_bootstrap_delta(frame, DECISIONS, WEAK, n_boot=2000, seed=1)
    point = r["acc"] - w["acc"]
    assert lo <= point <= hi
