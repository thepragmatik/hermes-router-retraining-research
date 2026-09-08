# Tasks: Doubly Robust Uplift Router

## Phase 0 — Freeze

- [ ] T001 Read constitution, spec, plan, P1/P3/P5 negative results, and Idea 101 contracts.
- [ ] T002 Create `results/102/PREREG.md` freezing pair, quality metric, train split, logging regimes, seeds, λ grid, feature sets, nuisance models, support and clipping rules.
- [ ] T003 Assert sealed test is not loaded and record artifact hashes.

## Phase 1 — $0 causal replay

- [ ] T010 Build simulated propensity logs from full-information train rows using at least three logging regimes.
- [ ] T011 Implement V1/always-action/direct-correctness/T-learner controls.
- [ ] T012 Implement cross-fitted nuisance outcome models.
- [ ] T013 Implement DR pseudo-outcome or orthogonal learner using exact simulated propensities.
- [ ] T014 Add weight/ESS/overlap diagnostics and explicit unsupported fallback.
- [ ] T015 Sweep the frozen λ grid and emit policy frontiers.
- [ ] T016 Run >=10 seeds and write seed-level results.
- [ ] T017 Compute oracle-capture fraction, paired bootstrap deltas, and treatment-effect decile diagnostics.
- [ ] T018 Run adversarial support tests: skewed logging, zero-overlap stratum, corrupted propensity.

## Stage-0 gate

- [ ] T020 Evaluate the exact spec gates. One preregistered diagnostic correction maximum. If fail, mark `KILLED` and stop.
- [ ] T021 If method works only with broad exploration, mark `NEEDS_101_COVERAGE` and quantify required action support/ESS.

## Phase 2 — Real telemetry adapter

Only after 101 produces suitable records.

- [ ] T030 Add loader for 101 decision/outcome schemas.
- [ ] T031 Validate propensities, evidence provenance, temporal ordering and outcome finality before training.
- [ ] T032 Freeze real-data train/calibration/qualification windows and minimum ESS.
- [ ] T033 Fit the same Stage-0-selected estimator; do not search a new model family on the qualification window.
- [ ] T034 Compare against the contemporaneous base policy with DR/OPE uncertainty and any available direct shadow truth.
- [ ] T035 Produce real-data frontier and task/traffic-stratum breakdown.

## Phase 3 — Candidate integration ablations

- [ ] T040 If 103 qualifies, add semantic-memory posterior/support as features and rerun the frozen ablation.
- [ ] T041 If 104 qualifies, add latent features and rerun separately.
- [ ] T042 Measure overlap/redundancy; retain only features that move end-to-end frontier.
- [ ] T043 Optionally wrap finalist with 105; do not credit 105's safety coverage as ranking uplift.

## Phase 4 — Handoff

- [ ] T050 Write `results/102/STAGE0_REPORT.md` and optional `REAL_DATA_REPORT.md`.
- [ ] T051 Update `frontier.csv`, component/effect ledgers and roadmap status.
- [ ] T052 Document exact estimand, assumptions, unsupported strata, feature version, model revisions and price snapshot.
- [ ] T053 Choose outcome `KILLED | NEEDS_101_COVERAGE | STAGE0_PASS | QUALIFIED`.

## Spend

No paid calls are authorized by these tasks. New exploration/model calls require a separate 101/operator preregistration.