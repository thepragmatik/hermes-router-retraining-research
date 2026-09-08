# Feature Specification: Conformal Safety Envelope

**Feature Branch:** `105-conformal-safety-envelope`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** any candidate score/policy such as V1, 102, 103 or 104.

## Problem

A router score can be useful without being trustworthy everywhere. This feature adds a **selective-risk envelope**: accept cheap routing only where a calibrated procedure can bound or empirically control the risk of cheap decisions, and abstain/fall back elsewhere.

This feature does not create a better ranking signal. It asks a different question: **how much coverage can we safely take from a candidate score at a chosen error/risk target?**

The motivation is practical. Previous router experiments often failed because a broadly applied trigger had poor precision. A high-precision, partial-coverage wrapper may still create useful savings if it can reliably identify the safest subset.

## User Stories

### Story 1 — Calibrate cheap acceptance risk

As an operator, I want to set a target risk for cheap-routed requests and obtain a threshold/acceptance set using only a dedicated calibration split.

### Story 2 — Know the safe coverage

As a researcher, I want the system to report what fraction of traffic can be routed cheaply while meeting the calibrated risk target, rather than claiming a guarantee at arbitrary coverage.

### Story 3 — Abstain under shift/support failure

As an operator, I want the envelope to refuse its guarantee or fall back when the calibration population no longer resembles current traffic.

### Story 4 — Compare global and stratified calibration

As a researcher, I want to test whether coarse task/traffic strata improve useful coverage without creating tiny unreliable calibration buckets.

## Risk Definition

Primary binary risk for two-tier routing:

`R = 1{cheap decision causes an unacceptable quality loss relative to reference action}`

Examples, frozen per experiment:

- cheap answer incorrect while reference/strong is correct;
- quality loss exceeds a task-specific threshold;
- accepted cheap action fails an objective verifier.

Do not change risk definition after seeing calibration results.

## Requirements

- **FR-001:** Use a dedicated calibration split not used to train the underlying router score.
- **FR-002:** State the exact guarantee/claim and assumptions. Exchangeability-based conformal claims MUST NOT be presented as valid under arbitrary drift.
- **FR-003:** Implement a simple finite-sample risk-control baseline first: one-sided binomial/Clopper-Pearson or conformal risk control over a threshold family.
- **FR-004:** The method MUST output acceptance coverage, empirical risk, upper confidence/risk bound, calibration size and threshold.
- **FR-005:** If no threshold satisfies the target risk, output `NO_SAFE_COVERAGE`; never relax alpha automatically.
- **FR-006:** Compare global calibration with at most a few preregistered coarse/Mondrian strata when sample sizes support them.
- **FR-007:** Small strata MUST back off to global calibration.
- **FR-008:** Coverage and economic value MUST be reported; a perfectly safe 0.1% slice is not automatically useful.
- **FR-009:** Distribution-shift/support diagnostics MUST accompany any deployment claim.
- **FR-010:** Calibration MUST be rerun when model/router version, grader definition or major traffic distribution changes.
- **FR-011:** RouterBench test remains sealed.

## Stage 0 — Cheapest Falsification

Use train-only splits with a candidate score already available (V1 must be included). Partition train into fit/calibration/evaluation without touching historical validation.

Test target risk levels such as `α ∈ {0.01, 0.025, 0.05}` frozen in prereg. For each candidate score:

1. Fit/obtain score on fit data.
2. Select conformal/risk threshold on calibration only.
3. Measure held-out risk and coverage.
4. Repeat across deterministic folds/seeds.

The idea survives if at least one realistic target risk produces:

- empirical held-out risk <= target in at least **9/10 folds/seeds** or the stated finite-sample upper bound covers the target as designed;
- cheap acceptance coverage >= **10%** on at least one useful traffic population **or** >=5% with a program-material cost saving/high-value risk reduction;
- matched-quality total cost improves by >= **3% relative** versus the unwrapped conservative baseline or the wrapper materially reduces false-cheap/high-value misses at acceptable cost;
- shift/support alarms correctly deactivate or widen the envelope on preregistered synthetic drift tests.

If V1 has no useful safe coverage but another candidate does, 105 survives as a wrapper for that candidate. If no score yields useful coverage, kill the envelope for current data.

## Methods

Preferred first implementation:

- sort requests by candidate cheap-safety score;
- evaluate nested acceptance sets;
- use a one-sided finite-sample risk bound or conformal risk-control procedure to select the largest acceptance set satisfying target risk;
- optionally apply coarse task-family/Mondrian calibration if each stratum has enough calibration examples.

Avoid sophisticated conditional conformal/neural calibrators until the simple nested-set procedure demonstrates useful coverage.

## Drift Handling

Monitor calibration-relevant summaries:

- score distribution shift;
- semantic/support distance if 103 exists;
- task/traffic mix;
- model/router revision;
- observed risk on delayed outcomes.

Under drift, the safe action is to reduce/disable cheap acceptance and recalibrate, not extrapolate the guarantee.

## Expected Benefit

- converts an imperfect score into a high-precision selective routing policy;
- makes risk/coverage tradeoffs explicit;
- can wrap V1 or new candidate signals without retraining them;
- provides a principled abstention mechanism for 106/agentic routing.

## Stackability / Exclusivity

- Stackable wrapper for 102/103/104 and potentially 109.
- Does not receive credit for improving score ranking; report its value as risk-control/coverage.
- Global vs stratified calibration are alternative promoted configurations.
- Mutually exclusive with silently using the same calibration rows to tune the underlying score and calibrate the envelope.