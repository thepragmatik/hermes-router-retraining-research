"""V1 val operating-point reproduction (locked, from deployment_threshold.md).

Frozen 2026-09-04 numbers at threshold 0.30, n=3626:
  routed acc 0.6395 +/- 0.02 ; frac_strong 0.7686 +/- 0.02
Uses ONLY validation-split stored artifacts (mf_val_frame.parquet +
mf_val_probs.npy). The sealed test split is never read.
"""
import pathlib

import numpy as np
import pandas as pd
import pytest

VAL_FRAME = pathlib.Path.home() / "transfer-bundle/analysis/mf_val_frame.parquet"
VAL_PROBS = pathlib.Path.home() / "transfer-bundle/analysis/mf_val_probs.npy"

THRESHOLD = 0.30
TARGET_ACC = 0.6395
TARGET_FRAC_STRONG = 0.7686
TOL = 0.02


def test_v1_val_reproduction():
    if not VAL_FRAME.exists() or not VAL_PROBS.exists():
        pytest.skip("val artifacts not mounted")
    probs = np.load(VAL_PROBS)
    frame = pd.read_parquet(VAL_FRAME)
    assert len(frame) == len(probs), "frame/probs length mismatch"
    routed = np.where(probs >= THRESHOLD, frame.strong_correct, frame.weak_correct)
    acc = float(routed.mean())
    frac_strong = float((probs >= THRESHOLD).mean())
    assert abs(acc - TARGET_ACC) <= TOL, f"routed acc {acc:.4f} vs {TARGET_ACC}"
    assert abs(frac_strong - TARGET_FRAC_STRONG) <= TOL, (
        f"frac_strong {frac_strong:.4f} vs {TARGET_FRAC_STRONG}")
