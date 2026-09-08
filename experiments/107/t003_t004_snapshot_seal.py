#!/usr/bin/env python3
"""Idea 107 Stage 0 — T003/T004: snapshot refresh (offline, repo-docs only) + seal assertion."""
import json
import os

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(".")  # worktree root expected as cwd; keep simple

wr = pd.read_parquet(os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet"))
n_test = int((wr.split == "test").sum())
seal = {"sealed_test_rows": n_test, "expected": 3678, "ok": n_test == 3678}
print(json.dumps(seal))
assert seal["ok"], "sealed test count mismatch"

snap = {
    "snapshot_date": "2026-09-08",
    "source": ("existing repo docs/results ONLY (offline): costs/model_prices.json (empty), "
               "results/P0_MODEL_POOL.md, research/2026-09-08-innovation-deep-research.md. "
               "No network metadata fetch performed; matches the hard constraint that the "
               "current-model/pricing refresh means metadata lookup from existing repo "
               "docs/results only."),
    "current_pool_note": ("No current-model measured outcome matrix exists in-repo. The only "
                          "measured outcome matrix is the historical RouterBench train pool. "
                          "Stage 0 therefore runs on the historical stored pool as "
                          "selection-method evidence, labeled historical/domain-specific; "
                          "current deployment claims are out of scope without a real pilot "
                          "(FR-010/FR-011)."),
    "repo_price_snapshot": json.load(open("costs/model_prices.json")),
}
with open("results/107/model_snapshot.json", "w") as f:
    json.dump(snap, f, indent=1)
print("model_snapshot.json written")
