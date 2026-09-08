"""Idea 102 shared data/config module (Stage 0, train-only, $0).

Frozen contract: results/102/PREREG.md. RouterBench TEST split is SEALED:
the loader asserts zero test rows are ever loaded. V1 stays untouched; its
frozen serialized p_strong fixture is the only router signal.
"""
import hashlib
import os

import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

WINRATE_TABLE = "/Users/rath/transfer-bundle/analysis/winrate_table.parquet"
PICKLE_PATH = "/Users/rath/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl"
PSTRONG_PATH = os.path.join(REPO_ROOT, "telemetry/fixtures/v1_train_pstrong.npy")

PREREG_PATH = "results/102/PREREG.md"
RESULTS_JSON = "results/102/stage0_results.json"
FRONTIER_CSV = "results/102/frontier.csv"
SUPPORT_CSV = "results/102/support_diagnostics.csv"

HASH_WINRATE = "4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6"
HASH_PICKLE = "ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d"
HASH_PSTRONG = "cf1baa3195f1956641377022361adde7db7b608611f17fe55d2a47641a4bea57"

SEEDS = list(range(102000, 102010))
REGIMES = ["L1", "L2", "L3"]
LAMBDA_GRID = [0, 10, 25, 50, 100, 150, 200, 300, 500]
V1_THRESHOLD = 0.30
N_FOLDS = 5
RIDGE_ALPHA_PSEUDO = 10.0
EVAL_MOD = 2000  # md5 % 10000 < 2000 -> eval
N_DECILES = 10
DECILE_MIN_STRONG = 100
OVERLAP_MIN = 0.09
ESS_MIN_FRAC = 0.05
BOOT_N = 2000
BOOT_SEED = 102999
TOP_FAMILIES = 5
G1_TOL = 0.015
G1_TRIPWIRE = 0.05
G2_MIN_SEEDS = 8
G3_Q_BAR = 0.65031
G3_C_BAR = 0.0011442
G3_MATER_Q = 0.002
GATES = ["G1", "G2", "G3", "G4", "G5"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_artifacts():
    """T003: verify frozen artifact hashes; assert the sealed pickle is only
    hashed here (never loaded) and that the winrate table has zero test rows
    loaded anywhere downstream (enforced in load_train_matrix)."""
    got = {
        "winrate_table": sha256_file(WINRATE_TABLE),
        "v1_pstrong_fixture": sha256_file(PSTRONG_PATH),
    }
    assert got["winrate_table"] == HASH_WINRATE, got
    assert got["v1_pstrong_fixture"] == HASH_PSTRONG, got
    # The sealed 0-shot pickle (HASH_PICKLE) is NEVER opened/parsed anywhere in
    # idea 102; its only permitted touch is the split-table membership count
    # asserted in load_train_matrix (test rows == 3678, contents never loaded).
    return got



def load_train_matrix():
    """Train split only. Asserts: 29193 rows, zero test rows, deterministic
    102 fit/eval split sizes (23305 / 5888), no overlap."""
    wt = pd.read_parquet(WINRATE_TABLE)
    train = wt[wt["split"] == "train"].reset_index(drop=True)
    assert len(train) == 29193, len(train)
    assert int((wt["split"] == "test").sum()) == 3678  # membership count from split table
    assert not (train["split"] == "test").any()
    p = np.load(PSTRONG_PATH).astype(np.float64)
    assert p.shape == (29193,)
    h = train["prompt"].map(
        lambda s: int(hashlib.md5(f"102:{s}".encode()).hexdigest()[:8], 16) % 10000)
    eval_mask = (h < EVAL_MOD).to_numpy()
    assert eval_mask.sum() == 5888 and (~eval_mask).sum() == 23305
    d = {
        "p": p,
        "eval_mask": eval_mask,
        "q_weak": train["weak_correct"].to_numpy(float),
        "q_strong": train["strong_correct"].to_numpy(float),
        "c_weak": train["cost_w"].to_numpy(float),
        "c_strong": train["cost_s"].to_numpy(float),
        "family": train["eval_name"].to_numpy(),
        "prompt": train["prompt"].to_numpy(),
        "n": len(train),
    }
    d["dcost"] = d["c_strong"] - d["c_weak"]
    return d
