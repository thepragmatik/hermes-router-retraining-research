# Pivot development / qualification protocol (FROZEN 2026-09-06)

This file freezes how the stackable-routing pivot mission may touch labeled data.
It exists because the historical validation split has been consulted by multiple
prior experiments (phase0 exp000–013 and the R5 router program); it is therefore
no longer a clean tuning surface.

## Development data

All iterative work (signal design, threshold selection, ablations, stack composition)
uses ONLY:

1. the hash-defined **train split** (29,193 rows of
   `~/transfer-bundle/analysis/winrate_table.parquet`; source
   `~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl`,
   sha256 `ba4f77f1…`), via
2. train-only cross-validation, or
3. a **deterministic train-derived pivot holdout**: seed 42, 15% of train rows,
   selected by md5(prompt) hash bucketing (deterministic across runs and machines),
   recorded here as the official pivot-holdout for all P1–P5 experiments.

No experiment may tune against the historical validation split. The validation
split (3,626 rows) is reserved exclusively for **finalists and milestone
qualification**.

## Qualification (validation) exposure rules

1. A validation exposure requires a **preregistration** written first:
   hypothesis, metric, threshold, and the exact operating point to be measured,
   filed under `experiments/` (or appended to an existing prereg) BEFORE any
   validation row is loaded.
2. Every exposure is logged in `MISSION_LOG.md` (validation-exposures table) at
   exposure time, with the preregistered threshold.
3. Thresholds are never moved after seeing qualification results. A failed gate
   kills or amends the hypothesis; it is never retuned into a pass.
4. The RouterBench **test split (3,678 rows) is SEALED**: never load, dedupe
   against, score, or use it indirectly. All data-loading code must assert
   `split != "test"` (and the winrate table must show zero test rows loaded).

## Router V1 reference (tag `router-v1-frozen`)

- `router_v1/` is READ-ONLY. Experiments may import `route.route()` and read the
  checkpoint; they may never write into that directory.
- V1's frozen operating point (threshold 0.30; val routed acc 0.6395,
  frac_strong 0.7686, PGR 0.9874) is a **fixed baseline**, not a tuning target.
- The P3/P4 trust layers must show marginal value **over V1**, not over a random
  or naive gate, for the marginal-value gate to be honest.
- Any retrain (e.g. for a new cheap tier selected by P0) is a NEW preregistered
  experiment producing a NEW tagged artifact. The prior judge-label v2 retrain
  FAILED its gate (auto-reverted); do not repeat it unchanged.

## Ledger duties

- Every evaluated operating point appends a row to `results/frontier.csv`.
- Every layer decision (keep/kill) appends to `results/component_effects.csv`.
- Overlap measurements append to `results/error_overlap.csv`.
- Spend (actual or estimated) is recorded in `MISSION_LOG.md`; paid runs require
  `SPEND_GO=1` and stay under the $5 mission cap.
