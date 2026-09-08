# Implementation Plan: Doubly Robust Uplift Router

## Goal

Test whether a router trained to estimate **incremental action value** can capture useful strong-model rescue mass more efficiently than absolute-label classifiers.

## Constitution Check

- test split sealed;
- train-only Stage 0;
- V1 mandatory control;
- no paid calls before Stage 0 passes;
- exact logged propensities required for real-data causal claims;
- cost-adjusted utility is the deployment objective;
- unsupported regions must abstain/fallback.

## Suggested Layout

```text
experiments/102/
  build_simulated_logs.py
  nuisance_models.py
  dr_learner.py
  policy.py
  evaluate.py
  diagnostics.py
results/102/
  PREREG.md
  stage0_results.json
  stage0_report.md
  frontier.csv
```

Reuse 101 telemetry/OPE schemas when available.

## Data Protocol

### Stage 0

Use only train-safe full-information rows. Freeze:

- deterministic dev/holdout split;
- binary action pair;
- quality definition;
- per-row costs;
- logging-policy simulations;
- seeds;
- nuisance feature sets;
- clipping/support rules;
- λ grid.

Generate partial-feedback logs from the full matrix, then hide all counterfactual outcomes from the learner.

### Stage 1

Requires 101 records with valid chosen propensities and joined outcomes. Freeze temporal windows to avoid leakage from future outcomes.

## Estimation

### Baselines

1. V1/base policy.
2. Always-cheap / always-strong.
3. Direct weak-correctness classifier using the same feature budget.
4. T-learner outcome difference.
5. Full-information oracle diagnostic only.

### DR learner

For binary `A∈{0,1}`:

- fit cross-fitted `μ0(x), μ1(x)`;
- use exact `e(x)=P(A=1|x)` from simulator/logs where known;
- construct orthogonal DR pseudo-outcomes or use policy-value DR directly;
- fit a lightweight regularized model to predict `τ(x)`;
- produce uncertainty/support metadata.

Start with linear/logistic/ridge or shallow tree models. Do not introduce deep networks unless the simple learner passes signal tests but clearly underfits.

## Policy Construction

For each λ on a frozen grid:

`route_strong = τ_hat(x) - λ * Δcost(x) > margin(x)`.

`margin=0` for Stage 0 unless a preregistered uncertainty buffer is tested separately.

Generate a complete frontier rather than selecting one λ after qualification.

## Support Diagnostics

Record per row/stratum:

- logging action probability;
- overlap region;
- effective sample size;
- weight quantiles;
- fraction falling back to base policy.

The policy must fall back where support is insufficient.

## Statistics

- 10 deterministic simulation seeds minimum;
- paired bootstrap for policy quality/cost deltas;
- report seed dispersion;
- report uplift calibration by decile if feasible;
- estimate oracle-capture fraction only against train-safe oracle truth;
- historical validation only for a preregistered finalist.

## Cost Strategy

- Stage 0: $0.
- Stage 1: use already collected 101 data first.
- No new model calls simply to enlarge treatment-effect training unless a power/overlap analysis shows the exact missing coverage and the operator authorizes it.

## Adversarial Checks

- deliberately skew logging propensities to test estimator robustness;
- inject propensity corruption and require failure;
- remove overlap in a stratum and require fallback;
- perturb prompts/paraphrases to check policy instability if text embeddings are used;
- change cost λ without retraining to verify quality model and economic threshold are separated.

## Kill / Escalation Logic

Kill if Stage 0 gates fail after one preregistered diagnostic correction. Do not “save” the idea by changing the target to correctness or by using counterfactual labels directly.

If the estimator is sound but realistic support is inadequate, outcome is `NEEDS_101_COVERAGE`, not method failure.

If Stage 0 passes but 103/104 later provide better features, rerun only the same frozen estimator comparison with the new feature family as an ablation.

## Deliverables

- reproducible simulator + learner;
- `results/102/stage0_report.md`;
- machine-readable frontier;
- support/weight diagnostics;
- optional real-data report after 101;
- roadmap status: `KILLED | NEEDS_101_COVERAGE | STAGE0_PASS | QUALIFIED`.