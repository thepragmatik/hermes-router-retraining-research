# Feature Specification: Doubly Robust Uplift Router

**Feature Branch:** `102-doubly-robust-uplift-router`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** Idea 101 for real-traffic claims; can be falsified first on train-only full-information replay.

## Problem

Previous router work largely learned absolute labels such as `needs_strong`, weak correctness, or proxies for answer quality. The deployment decision is different: **what is the expected incremental utility of choosing action B over action A for this request?**

This feature estimates conditional marginal gain / treatment effect using causal/off-policy methods with explicit propensities, then routes only when expected quality gain justifies incremental cost.

This is materially different from the failed sparse-label FEV experiment because it requires an identified data-generating process, cross-fitted nuisance models, overlap diagnostics, and doubly robust correction rather than treating sparse labels as ordinary supervised truth.

## Core Decision

For actions `a ∈ A`, estimate:

`U(a,x) = E[Q(a)|x] - λ * C(a,x) - ρ * Risk(a,x)`

For binary weak/strong routing:

`τ(x) = E[Q_strong - Q_weak | x]`

Choose strong when:

`τ_hat(x) > λ * (C_strong - C_weak) + risk_margin(x)`.

The implementation must expose the quality/cost frontier across λ rather than hiding one chosen threshold.

## User Stories

### Story 1 — Recover uplift from hidden counterfactuals

As a researcher, I want the method to recover useful marginal-gain structure when full-information train data is converted into propensity-logged partial feedback.

**Independent test:** simulate logging policies with known propensities, hide unchosen outcomes, train uplift estimators, and compare predicted policy value to full-information truth.

### Story 2 — Beat non-causal controls

As an operator, I want evidence that identified uplift learning beats simple controls such as V1, direct weak-correctness prediction, and a naive outcome model at matched information/cost.

### Story 3 — Refuse unsupported regions

As a researcher, I want the router to identify where treatment-effect estimates are extrapolating beyond logging-policy overlap rather than making confident strong/weak decisions.

### Story 4 — Update with real telemetry

Once Idea 101 produces valid joined outcomes and propensities, I want the exact same estimator interface to retrain from real/shadow data without changing the estimand.

## Requirements

- **FR-001:** Target must be marginal action utility/treatment effect, not generic difficulty.
- **FR-002:** Real-data training MUST require valid logging propensities for randomized events; deterministic data may enter only through supported direct-model components or clearly declared assumptions.
- **FR-003:** Nuisance models for outcome and propensity MUST use cross-fitting where they share evaluation rows with treatment-effect estimation.
- **FR-004:** Implement at least one doubly robust learner and one simpler comparator (`T-learner`, `S-learner`, direct gain model, or full-information oracle regression).
- **FR-005:** Binary two-action estimation is the first implementation. Multi-action generalized treatment effects are out of scope until binary value is demonstrated.
- **FR-006:** Importance weights MUST be diagnosed; clipping/shrinkage must be frozen before final evaluation.
- **FR-007:** The router MUST emit `uplift`, uncertainty/support diagnostics, expected incremental cost, and final utility score.
- **FR-008:** Unsupported regions MUST fall back to V1/conservative policy rather than extrapolate.
- **FR-009:** Cost λ MUST be swept to produce a Pareto curve; no single λ may be selected after seeing qualification results.
- **FR-010:** Evaluation MUST include end-to-end quality, cost, frontier-call fraction, selective support, and uncertainty—not only treatment-effect RMSE/AUROC.
- **FR-011:** External/synthetic data may initialize a direct outcome model but may not supply propensity correction or qualification truth.
- **FR-012:** RouterBench test remains sealed; historical validation is finalists-only.

## Candidate Estimators

Start simple:

1. **Cross-fitted T-learner:** `μ0(x), μ1(x)`; `τ=μ1-μ0`.
2. **DR pseudo-outcome learner:** construct an orthogonalized/doubly robust pseudo-outcome using logged treatment `A`, propensity `e(x)`, observed outcome `Y`, and cross-fitted outcome models.
3. Optional **R-learner** if overlap and sample size justify it.

Do not start with deep causal forests/neural meta-learners. Earn complexity only if simple orthogonal estimators show signal but underfit.

## Stage 0 — Cheapest Falsification

Use train-only full-information data with a deterministic pivot split. Simulate at least three logging policies ranging from broad to V1-skewed support. Hide counterfactual outcomes.

The idea survives Stage 0 only if all hold:

- DR policy-value estimate tracks full-information policy truth with absolute error <= **0.015** on at least 2/3 logging-policy regimes;
- treatment-effect ranking achieves positive and stable gain over the direct weak-correctness baseline on at least 8/10 seeds;
- a policy built from `τ_hat` captures at least **35% of the available oracle quality lift** at no more than **50% of the oracle's cost advantage lost**, or otherwise moves the quality/cost Pareto frontier by the program materiality gate;
- unsupported/poor-overlap regimes are correctly flagged instead of appearing as wins.

If the method only works under near-uniform exploration and collapses under realistic V1-skewed overlap, mark it `NEEDS_BETTER_COVERAGE`, not qualified.

## Stage 1 — Real-Data Eligibility

Requires Idea 101 Stage-1/2 data quality to pass and enough randomized/dual outcomes for effective sample size.

Qualification on real/shadow data requires:

- preregistered train/calibration/qualification windows;
- no post-hoc λ or clipping selection;
- policy improvement over V1 or current base with bootstrap/DR uncertainty;
- at least **5% relative runtime-cost reduction at matched quality**, **1pp quality gain at matched cost**, or another program-level materiality criterion;
- no major task-family regression or unsupported stratum silently routed cheap.

## Failure Modes

- overlap too weak for identifiable treatment effects;
- strong and weak quality labels use inconsistent graders;
- outcome model leakage from action/correctness fields;
- propensity model estimated where exact logging propensity should have been stored;
- apparent uplift driven by price changes rather than quality difference;
- large weights make estimates variance-dominated;
- conditional effects change after model/provider revision.

## Expected Benefit

If successful, this turns routing into a directly economic, causally aligned decision and can exploit the oracle headroom already observed in the repo without requiring a perfect correctness arbiter.

## Stackability / Exclusivity

- Stacks naturally with 101 telemetry, 103 semantic memory, 104 latent features, and 105 conformal fallback.
- 103/104 may be feature or nuisance-model inputs; they do not replace the causal correction.
- Mutually exclusive with promoting an uncorrected synthetic-only/direct classifier as the authoritative policy.
- Multi-action uplift should wait for 107 model-pool selection to keep the action set small.