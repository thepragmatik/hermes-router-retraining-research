#!/usr/bin/env python3
"""Idea 108 Stage 0 — T004: sealed test assertion.

The only permitted test touch is the split-table membership count.
Test row CONTENT is never loaded, inspected, embedded, or deduplicated.
"""
import json
import os

import pandas as pd

WINRATE = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")

EXPECTED = {"train": 29193, "test": 3678, "val": 3626}


def main():
    counts = pd.read_parquet(WINRATE, columns=["split"])["split"].value_counts().to_dict()
    counts = {k: int(v) for k, v in counts.items()}
    seal = {"split_membership_counts": counts, "expected": EXPECTED,
            "ok": counts == EXPECTED}
    print(json.dumps(seal))
    assert seal["ok"], "sealed split membership counts drifted"


if __name__ == "__main__":
    main()
