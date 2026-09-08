# Tasks: Multi-Fidelity Synthetic→Real Fusion

## Phase 0 — Freeze provenance and budgets

- [ ] T001 Read constitution, spec, plan, generator branch R4–R7a evidence and 101/102 contracts.
- [ ] T002 Create `results/108/PREREG.md` freezing synthetic source/version, real train rows, budget percentages, seeds, fusion arms, synthetic-weight grid, metrics and gates.
- [ ] T003 Build provenance manifest for every source; assert no synthetic row can be loaded as `real` through schema validation.
- [ ] T004 Assert sealed test untouched.

## Phase 1 — $0 shift audit

- [ ] T010 Load R7a strict synthetic rows and compatible train-safe real outcomes.
- [ ] T011 Produce task/embedding/label/pair-state/verifier-format shift diagnostics.
- [ ] T012 Build deliberate known-bias low-fidelity simulator for code-path validation.
- [ ] T013 Freeze matched real-row samples for every real-label budget.

## Phase 2 — fusion controls

- [ ] T020 Train real-only control at every budget.
- [ ] T021 Train synthetic-only diagnostic; label it non-promotable in reports/code.
- [ ] T022 Train synthetic-pretrain→real-update arm.
- [ ] T023 Train weighted-joint arm using frozen synthetic weights.
- [ ] T024 If propensity simulation/101 data is available, train synthetic-assisted direct model with real DR correction.
- [ ] T025 Evaluate every arm on the same real held-out rows.

## Stage-0 gate

- [ ] T030 Plot real-label-budget curves and calculate real-label saving at frozen target utility.
- [ ] T031 Run paired/seed uncertainty analysis and exact matched-real-only comparison.
- [ ] T032 If fusion fails at >=3/5 budgets or does not save >=25% real labels/materially improve frontier, mark `KILLED`.
- [ ] T033 If synthetic helps as initialization but not final policy, mark `LOW_FIDELITY_PRIOR_ONLY` and stop scaling.

## Phase 3 — real identified data (conditional)

- [ ] T040 When 101 data exists, freeze temporal windows and minimum propensity support.
- [ ] T041 Fit matched real-only and fusion direct/nuisance models.
- [ ] T042 Evaluate/correct using real observed propensity-weighted/DR terms only.
- [ ] T043 Report source-specific calibration and any degradation under current traffic.

## Phase 4 — scale decision (conditional)

- [ ] T050 Only after transfer passes, estimate marginal value of additional synthetic labels.
- [ ] T051 If more generation is justified, draft a separate spend prereg with exact batch size/cap and R7a strict config.
- [ ] T052 Re-audit a random key sample for every new generator version/batch family.

## Phase 5 — handoff

- [ ] T060 Write shift report, budget curves and Stage-0/real-data report.
- [ ] T061 Update roadmap/component ledgers and document whether 108 feeds 102.
- [ ] T062 Choose `KILLED | LOW_FIDELITY_PRIOR_ONLY | SAMPLE_EFFICIENCY_PASS | QUALIFIED_FUSION`.

## Spend

Existing data first. This prompt authorizes no new generator or model spend.