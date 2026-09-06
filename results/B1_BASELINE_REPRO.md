# B1 — Baseline reproduction (historical v1 router + endpoints)

**Date:** 2026-09-06 · **Spend:** $0 · **Data:** validation split only (test SEALED, never loaded) · Script: `experiments/b1_baseline_repro.py` · Raw output: `results/B1_BASELINE_REPRO_raw.txt`

All six frozen metrics from the R5 program reproduce **exactly** (abs diff 0.0000
on every metric, inside the ±0.005/0.02 tolerances):

| metric | recorded | measured |
|---|---|---|
| weak acc (val, n=3626) | 0.2289 | 0.2289 |
| strong acc | 0.6448 | 0.6448 |
| always-strong APGR (v1 reference) | 0.6459 | 0.6459 |
| v1 routed acc @ threshold 0.30 | 0.6395 | 0.6395 |
| v1 frac_strong | 0.7686 | 0.7686 |
| v1 PGR | 0.9874 | 0.9874 |

**BASELINE_REPRO: PASS.** Method note (recorded for reproducibility): APGR is the
trapezoid of PGR over the ascending **call-fraction** axis (per
`~/transfer-bundle/analysis/eval_apgr.py`), not over the threshold axis; the
first implementation integrated over the threshold axis and read 0.6096, which
was a metric-definition bug, not a data problem (fixed in the same commit).

Baselines now established for the pivot mission (added to `results/frontier.csv`
in the P0 step):

- always weak: acc 0.2289
- always strong (simulated from stored labels): acc 0.6448, APGR 0.6459
- router v1 (tag `router-v1-frozen`) @ 0.30: acc 0.6395, frac_strong 0.7686, PGR 0.9874

These are the anchors P0/P1/P2 must beat on end-to-end economics.
