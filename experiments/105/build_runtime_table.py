#!/usr/bin/env python3
"""Idea 105: build the runtime envelope artifact (telemetry/envelope_config.json).

Deterministic, no free parameters. Frozen per results/105/ENVELOPE_DEPLOY_PREREG.md:
- deployment threshold per alpha = MAX over the 10 Stage-0 fold-qualified thresholds
  (conservative intersection of the fold acceptance sets);
- producing fold's (m_cal, k_cal, cp_ub) embedded for stdlib CP re-verification at load;
- KS reference = seed-0 calibration slice of the RUNTIME score s_runtime = 1 - round(p, 4),
  embedded verbatim (pure JSON floats; no prompt text, no raw data rows).

Verifies BEFORE writing: the recomputed fold table reproduces the committed
results/105/coverage_risk_global.csv exactly (threshold equality on every row), the
deployment row's CP upper bound <= alpha, and all artifact hashes match the frozen preregs.
Run from the repo root:  python3 experiments/105/build_runtime_table.py
"""
import ast
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from scipy import stats as sps  # build-time only; runtime module is stdlib-only

WINRATE = "/Users/rath/transfer-bundle/analysis/winrate_table.parquet"
PROBS = os.path.join(REPO, "results", "v1_train_probs.npy")
CSV = os.path.join(REPO, "results", "105", "coverage_risk_global.csv")
OUT = os.path.join(REPO, "telemetry", "envelope_config.json")
CALIBRATE_SRC = os.path.join(REPO, "experiments", "105", "calibrate.py")
DRIFT_SRC = os.path.join(REPO, "experiments", "105", "drift.py")

PREREG_HASHES = {
    WINRATE: "4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6",
    PROBS: "dfbe974ecadb93e8f2b78ebb5f87b33d6ae9c108b48b903a4c433dd5b017e1af",
    os.path.join(REPO, "router_v1", "mf_router.pt"):
        "db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7",
}
ALPHAS = [0.01, 0.025, 0.05]
DELTA = 0.05
DEPLOYED_ALPHA = 0.01
KS_WINDOW = 500
KS_P = 0.01
BASE_COMMIT = "9571381"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_stage0_calibrate():
    """Extract the exact calibrate() function from the committed Stage-0 source.

    calibrate.py has no __main__ guard (its pipeline runs top-level), so it cannot
    be imported directly; ast-extraction of the function source reproduces it
    byte-for-byte with zero transcription.
    """
    src = open(CALIBRATE_SRC).read()
    tree = ast.parse(src)
    delta = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "DELTA":
            delta = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name == "calibrate":
            seg = ast.get_source_segment(src, node)
            ns = {"np": np, "sps": sps, "DELTA": delta}
            exec(compile(seg, CALIBRATE_SRC, "exec"), ns)
            return ns["calibrate"]
    raise RuntimeError("calibrate() not found in " + CALIBRATE_SRC)


def main():
    for path, want in PREREG_HASHES.items():
        got = sha256(path)
        assert got == want, f"hash mismatch {path}: {got} != {want}"
    print("artifact hashes verified (winrate table, train probs, mf_router.pt)")

    calibrate = load_stage0_calibrate()

    p = np.load(PROBS)  # float32, Stage-0 convention: s = 1 - p in float32
    assert p.dtype == np.float32 and p.shape == (29193,)
    wt = pd.read_parquet(WINRATE)
    tr = wt[wt["split"] == "train"].reset_index(drop=True)
    assert len(tr) == 29193
    sc = tr["strong_correct"].values.astype(np.int8)
    wc = tr["weak_correct"].values.astype(np.int8)
    risk = ((wc == 0) & (sc == 1)).astype(int)  # frozen risk event
    s = 1.0 - p  # float32, exactly as Stage-0 computed it
    n = len(p)

    # Re-derive all 30 fold rows; verify against the committed CSV.
    csv = pd.read_csv(CSV)
    assert len(csv) == 30 and csv.threshold.notna().all()
    fold_rows = {}
    for seed in range(10):
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n)
        cal_idx = perm[: int(0.4 * n)]
        for alpha in ALPHAS:
            thr, cov_cal, ub = calibrate(s[cal_idx], risk[cal_idx], alpha)
            # exact count of calibration rows in the acceptance set
            m_cal = int((s[cal_idx] >= thr).sum())
            k_cal = int(risk[cal_idx][s[cal_idx] >= thr].sum())
            row = csv[(csv.seed == seed) & (np.isclose(csv.alpha, alpha))]
            assert len(row) == 1
            assert thr == float(row.threshold.iloc[0]), \
                f"threshold drift seed={seed} alpha={alpha}: {thr} vs {row.threshold.iloc[0]}"
            assert abs(cov_cal - float(row.cov_cal.iloc[0])) < 1e-12
            assert abs(ub - float(row.cp_ub.iloc[0])) < 1e-12
            fold_rows[(seed, alpha)] = dict(threshold=thr, m_cal=m_cal, k_cal=k_cal,
                                            cp_ub=ub, cov_cal=cov_cal)
    print("fold table reproduced from raw artifacts == committed CSV (all 30 rows exact)")

    # Deployment table: MAX fold-qualified threshold per alpha (conservative).
    table = []
    for alpha in ALPHAS:
        best_seed = max(range(10), key=lambda sd: fold_rows[(sd, alpha)]["threshold"])
        fr = fold_rows[(best_seed, alpha)]
        assert fr["cp_ub"] <= alpha, f"producing fold CP ub {fr['cp_ub']} > alpha {alpha}"
        # stdlib-equivalent CP duality cross-check (build-time, scipy):
        # P(Bin(m_cal, alpha) >= k_cal+1) >= 1-delta  <=>  CP ub <= alpha
        duality = float(sps.binom.sf(fr["k_cal"], fr["m_cal"], alpha))
        assert duality >= 1 - DELTA, f"CP duality failed alpha={alpha}: {duality}"
        table.append(dict(alpha=alpha, threshold=fr["threshold"],
                          producing_seed=best_seed, m_cal=fr["m_cal"],
                          k_cal=fr["k_cal"], cp_ub=fr["cp_ub"],
                          cov_cal=fr["cov_cal"], cp_duality_p=duality))
        print(f"alpha={alpha}: deploy threshold {fr['threshold']!r} (seed {best_seed}, "
              f"m_cal={fr['m_cal']}, k_cal={fr['k_cal']}, cp_ub={fr['cp_ub']:.6f}, "
              f"duality_p={duality:.4f})")

    # KS reference: seed-0 calibration slice of the RUNTIME score.
    p64 = p.astype(np.float64)
    rng0 = np.random.default_rng(0)
    perm0 = rng0.permutation(n)
    cal0 = perm0[: int(0.4 * n)]
    ks_ref = [1.0 - round(float(x), 4) for x in p64[cal0]]
    assert len(ks_ref) == 11677 and all(0.0 <= v <= 1.0 for v in ks_ref)

    cfg = {
        "component": "idea-105-conformal-safety-envelope",
        "version": "envelope-v1-stage0",
        "built_from_commit": BASE_COMMIT,
        "deployed_alpha": DEPLOYED_ALPHA,
        "delta": DELTA,
        "score_definition": "s_runtime = 1 - round(p_strong_wins, 4); accept iff s_runtime >= threshold",
        "decision_rule": "record-only shadow verdict; never overrides the raw V1 decision",
        "table": table,
        "ks_detector": {
            "reference_source": "seed-0 calibration slice of s_runtime (train rows)",
            "reference_n": len(ks_ref),
            "window_size": KS_WINDOW,
            "fire_p": KS_P,
            "reference": ks_ref,
        },
        "risk_breach": {"window": 200, "quantile": 0.95, "armed": True,
                        "note": "inert in this deploy: no in-process label source"},
        "provenance": {
            "stage0_prereg": "results/105/PREREG.md",
            "stage0_report": "results/105/STAGE0_REPORT.md",
            "deploy_prereg": "results/105/ENVELOPE_DEPLOY_PREREG.md",
            "stage0_csv": "results/105/coverage_risk_global.csv",
            "v1_train_probs_sha256": PREREG_HASHES[PROBS],
            "mf_router_pt_sha256": PREREG_HASHES[
                os.path.join(REPO, "router_v1", "mf_router.pt")],
            "winrate_table_sha256": PREREG_HASHES[WINRATE],
            "calibrate_source": "experiments/105/calibrate.py (ast-extracted verbatim)",
        },
    }
    with open(OUT, "w") as f:
        json.dump(cfg, f, sort_keys=True, indent=1)
    print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")
    print("sha256:", sha256(OUT))


if __name__ == "__main__":
    main()
