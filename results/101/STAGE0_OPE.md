# Stage 0 OPE Reconstruction — Idea 101 (Counterfactual Shadow Telemetry)

**Run:** 2026-09-08 · **Prereg:** `results/101/PREREG.md` (frozen before code) · **Spend:** $0
**Terminal status: STAGE0_PASS** (no preregistered correction consumed)

## Design

Train-only full-information replay on the frozen winrate table
(`winrate_table.parquet` sha256 `4e58f024...963a6`, 29193 train rows; **test
split never loaded** — only its membership count 3678 from the split table, per
prereg). Actions `{weak, strong}`; utility = accuracy. Frozen V1 engine
(threshold 0.30, untouched) scored every train row (serialized
`telemetry/fixtures/v1_train_pstrong.npy`, sha256 `cf1baa31...bea57`).

Logging policy: epsilon-mixture `0.80·V1 + 0.20·uniform`, exact chosen
propensity stored, unchosen outcomes hidden from the OPE layer. Targets: V1,
V1_hi (threshold 0.50), always_weak. Estimators: IPS, SN-IPS, cross-fitted DR
(ridge interaction model, 5 folds), SWITCH-DR (preregistered M=20). 10
deterministic seeds 101000–101009.

## Full-information truth

| Policy | Truth (acc) |
|---|---|
| V1 | 0.6411 |
| V1_hi | 0.6022 |
| always_weak | 0.2167 |

## Gate results (all four PASS)

- **G1 ordering** — SWITCH-DR ranks V1 > V1_hi > always_weak correctly in
  **10/10** seeds (required ≥9).
- **G2 accuracy** — mean absolute error V1 **0.00059**, V1_hi **0.00306**
  (both ≤ 0.015). 95% SWITCH-DR CI contained truth in **10/10** seeds for both
  (≥90% required). Both branches of the OR satisfied.
- **G3 support** — synthetic zero-overlap target (strong only where
  p_strong<0.05, coverage 2.2%) flagged `INSUFFICIENT_SUPPORT` in **10/10**
  seeds (coverage + ESS fire); well-supported V1 never flagged.
- **G4 propensity integrity** — NaN propensity → `ValueError` (refusing OPE);
  zero propensity → `ValueError`; corrupted propensity (>1) → `ValueError`.
  All loud, no silent estimates.

## Diagnostics (seed 101000)

| Target | IPS | DR | SWITCH-DR | ESS/n | max\|w\| | clipped |
|---|---|---|---|---|---|---|
| V1 | 0.6421 | 0.6417 | 0.6417 | 0.900 | 1.11 | 0 |
| V1_hi | 0.6061 | 0.6044 | 0.6044 | 0.460 | 10.00 | 0 |
| always_weak | 0.2193 | 0.2208 | 0.2208 | 0.126 | 10.00 | 0 |

Weights are well-behaved under the ε=0.20 mixture (max |w| = 10 = 1/0.10 by
construction); no clipping was triggered. IPS alone already recovers ordering;
DR/SWITCH-DR reduce variance.

## Verdict

The logging schema (exact propensities, epsilon-mixture with guaranteed
support) plus IPS/DR/SWITCH-DR reconstructs known policy values, orderings,
intervals, and support diagnostics from train-only data at $0. Stage-0 gates
passed with wide margin; the preregistered single correction was not consumed.
Phase 2 (live telemetry plumbing) is unblocked by this spec's plan.
