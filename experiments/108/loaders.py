#!/usr/bin/env python3
"""Idea 108 Stage 0 — provenance/schema loaders (T003).

Fidelity tags are frozen in results/108/PREREG.md Section 1:
  synthetic_r7a — only from R7a batch jsonl files;
  benchmark     — only from winrate_table train rows.
A synthetic file loaded with any other target fidelity raises ProvenanceError:
a synthetic row cannot enter a real frame through these loaders (FR-001/FR-002).
"""
import json
import os

import numpy as np
import pandas as pd

WORKTREE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUTS = os.path.join(WORKTREE, "results", "108", "inputs")
WINRATE = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")

FID_SYN = "synthetic_r7a"
FID_REAL = "benchmark"
R7A_BATCH = "r7_b1788903723_47290"
EXPECTED_TEST_ROWS = 3678
EXPECTED_VAL_ROWS = 3626
EXPECTED_TRAIN_ROWS = 29193


class ProvenanceError(RuntimeError):
    """Raised when a load would cross the frozen fidelity boundary."""


def _assert_fidelity(file_kind: str, target: str):
    if file_kind == "synthetic" and target != FID_SYN:
        raise ProvenanceError(
            f"refusing to load synthetic rows as fidelity={target!r}; "
            f"synthetic rows may only carry fidelity={FID_SYN!r}"
        )
    if file_kind == "real" and target not in (FID_REAL,):
        raise ProvenanceError(
            f"refusing to tag real rows fidelity={target!r}"
        )


def load_synthetic(items_path=None, labels_path=None) -> pd.DataFrame:
    """Load R7a batch rows, tag fidelity=synthetic_r7a, assert batch id."""
    items_path = items_path or os.path.join(INPUTS, "items_batch7_r7a.jsonl")
    labels_path = labels_path or os.path.join(INPUTS, "labels_batch7_r7a.jsonl")
    it = pd.read_json(items_path, lines=True)
    lb = pd.read_json(labels_path, lines=True)
    if not set(it.item_id) == set(lb.item_id):
        raise ProvenanceError("items/labels item_id sets differ")
    if (it.batch_id != R7A_BATCH).any():
        raise ProvenanceError(f"unexpected batch_id; frozen source is {R7A_BATCH}")
    lb2 = lb.drop(columns=["question", "weak_ok", "strong_ok", "ts"], errors="ignore")
    m: pd.DataFrame = it.merge(lb2, on="item_id", suffixes=("", "_lb"))
    m["fidelity"] = FID_SYN
    m["y_syn"] = (m.label == "need_strong").astype(int)
    return m


def load_real_train(winrate_path=None) -> pd.DataFrame:
    """Load winrate TRAIN rows only, tag fidelity=benchmark (T010).

    TEST rows are never loaded (FR-012). VAL rows are never loaded (exposed).
    """
    wt = pd.read_parquet(winrate_path or WINRATE)
    n_test = int((wt.split == "test").sum())
    n_val = int((wt.split == "val").sum())
    tr = wt[wt.split == "train"].reset_index(drop=True)
    if len(tr) != EXPECTED_TRAIN_ROWS or n_test != EXPECTED_TEST_ROWS or n_val != EXPECTED_VAL_ROWS:
        raise ProvenanceError(
            f"row counts drifted: train={len(tr)} test={n_test} val={n_val}"
        )
    # y and tie bookkeeping (PREREG Section 2 + ERRATUM E1):
    # y = 1 iff need-strong (weak wrong, strong right); y = 0 iff weak strictly
    # better (weak right, strong wrong). R7a need_strong -> y=1 maps directly.
    need_strong = (tr.weak_correct == 0) & (tr.strong_correct == 1)
    weak_better = (tr.weak_correct == 1) & (tr.strong_correct == 0)
    y = pd.Series(np.nan, index=tr.index)
    y[need_strong] = 1.0
    y[weak_better] = 0.0
    tr["y"] = y
    tr["untied"] = tr.y.notna()
    tr["fidelity"] = FID_REAL
    return tr


def main():
    syn = load_synthetic()
    tr = load_real_train()
    print(json.dumps({
        "synthetic_rows": len(syn),
        "synthetic_label_counts": syn.label.value_counts().to_dict(),
        "synthetic_batch": R7A_BATCH,
        "real_train_rows": len(tr),
        "real_untied_rows": int(tr.untied.sum()),
        "real_y1_rate_untied": float(tr.loc[tr.untied, "y"].mean()),
        "fidelity_values_present": sorted(set(syn.fidelity) | set(tr.fidelity)),
    }, indent=1))


if __name__ == "__main__":
    main()
