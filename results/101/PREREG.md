# PREREG — Idea 101 Stage 0 (Counterfactual Shadow Telemetry)

**Frozen:** 2026-09-08 (before any pipeline code ran). Stage-0 contract only; no gate
below may be weakened after results are seen.

## Data source (train-only, full-information)

- Frozen split: `/Users/rath/transfer-bundle/analysis/winrate_table.parquet`
  sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`
  (29193 train / 3626 val / 3678 test). **TEST SPLIT IS SEALED — never loaded.**
  The 0-shot RouterBench pickle
  (`routerbench_0shot.pkl`, sha256 `ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d`)
  is used ONLY for split-table membership verification (row counts), never for
  test rows.
- Full-information matrix: frozen winrate table `train` split columns
  `strong_correct`, `weak_correct` (0/1 outcomes) with `cost_s`, `cost_w`.
- Router feature: frozen V1 engine (`router_v1/`, threshold 0.30, untouched)
  scores `p_strong` on all 29193 train rows; serialized to
  `telemetry/fixtures/v1_train_pstrong.npy`
  sha256 `cf1baa3195f1956641377022361adde7db7b608611f17fe55d2a47641a4bea57`.
  V1 train full-information value: acc 0.6411, frac_strong 0.7681.

## Action set

`{weak, strong}` (two actions), utility for Stage 0 = **accuracy** (quality units).

## Simulation seeds

10 deterministic seeds: `101000..101009` (numpy default_rng(seed)).

## Logging policies (same for all seeds; one sampled action per row)

Epsilon-mixture of the V1 policy (deterministic at threshold 0.30) and uniform
over the action set; every action gets support on every row:

- `p(a|x) = 0.80 * V1(a|x) + 0.20 * 0.5` (epsilon = 0.20)
- chosen action sampled from that distribution; **exact** chosen propensity stored.

## Target policies

1. `V1` — deterministic frozen V1 (threshold 0.30).
2. `V1_hi` — materially different threshold policy (threshold 0.50).
3. `always_weak` — degenerate random-baseline policy.

## OPE estimators (frozen)

- IPS (unclipped, unnormalized primary).
- Self-normalized IPS (diagnostic only).
- DR (cross-fitted, 5-fold, ridge outcome model on the single scalar feature
  `p_strong`, one-hot action).
- SWITCH-DR with frozen preregistered bound `M = 20`: weights above 20 are
  replaced by the direct-model contribution for those rows (SWITCH rule,
  lambda=1 for clipped rows).
- 95% CIs: normal approximation with plugged-in variance for IPS; same for
  SWITCH-DR on the weights actually used. No data-dependent clipping.

## Support / overlap diagnostics (frozen thresholds)

Target policy flagged `INSUFFICIENT_SUPPORT` if any fires:

- min target action probability over rows where target chooses it < 1e-6;
- ESS/n < 0.01 for the primary estimator;
- max importance weight > 50 (with estimator = IPS/DR rather than SWITCH-DR);
- target action coverage (rows where logging chose a target-supported action
  with nonzero target prob) < 5% of rows.

## Stage-0 gates (frozen; >=3 target policies, 10 seeds)

- G1 (ordering): OPE (primary estimator = SWITCH-DR on weights; IPS tie-break)
  ranks the 3 target policies correctly vs full-information truth in >= 9/10 seeds.
- G2 (accuracy): for V1 and for V1_hi: mean absolute policy-value error <= 0.015
  quality units, OR the 95% CI contains full-info truth in >= 90% of seeds.
- G3 (support): a synthetic zero/near-zero-overlap target must be flagged
  `INSUFFICIENT_SUPPORT` in 10/10 seeds.
- G4 (propensity integrity): deliberately corrupted and missing propensities
  must cause loud test failures, not silent estimates.

## Bounded correction clause (preregistered in advance)

Exactly one diagnostic correction is permitted if G1/G2 fail: replace the
primary estimator with the other preregistered robust variant (SWITCH-DR
bounds M=20 <-> IPS with self-normalization diagnostic), selected from the
first-run diagnostics (ESS, max weight quantiles). No other change. If gates
still fail, terminal status = `KILLED`.

## Spend

$0. No model inference, paid or free; historical stored matrix only.
