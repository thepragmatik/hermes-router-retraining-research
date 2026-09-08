# Tasks: Conformal Safety Envelope

## Phase 0 — Freeze

- [ ] T001 Read constitution, spec, plan and current candidate score documentation.
- [ ] T002 Define and freeze the exact routing risk event in `results/105/PREREG.md`.
- [ ] T003 Freeze fit/calibration/evaluation splits, target risks α, confidence δ, minimum calibration size, candidate scores, and optional coarse strata.
- [ ] T004 Record data/model hashes; assert test split sealed.

## Phase 1 — Global $0 envelope

- [ ] T010 Implement nested score-threshold acceptance sets.
- [ ] T011 Implement exact one-sided binomial or selected conformal risk bound with unit tests against known examples.
- [ ] T012 Implement `NO_SAFE_COVERAGE` behavior.
- [ ] T013 Evaluate V1 across all frozen folds/seeds; emit risk/coverage curves.
- [ ] T014 Evaluate strongest other already-qualified score without retuning that score.
- [ ] T015 Convert coverage to quality/cost/frontier-call economics.

## Stage-0 decision

- [ ] T020 Apply risk/coverage/economic gates exactly.
- [ ] T021 If no useful coverage, mark `KILLED` for current scores; do not weaken α after evaluation.
- [ ] T022 If V1 yields useful safe coverage, record `V1_SAFE_SLICE` even if no new score exists.

## Phase 2 — Stratified calibration (conditional)

- [ ] T030 Implement at most the preregistered coarse task/traffic strata.
- [ ] T031 Enforce minimum calibration size and global backoff.
- [ ] T032 Compare coverage/risk/economics against global envelope.
- [ ] T033 Remove stratification if it does not materially help.

## Phase 3 — Shift/adversarial stress

- [ ] T040 Run task-mix, OOD, paraphrase/format and score-shift fixtures.
- [ ] T041 Verify alarms/version invalidation reduce/disable the envelope rather than preserve a stale guarantee.
- [ ] T042 Test user-controlled suffix/prefix manipulations for cheap/expensive route forcing.

## Phase 4 — Integration

- [ ] T050 Wrap each independently qualified 102/103/104 score one at a time.
- [ ] T051 Report ranking gain separately from safety-envelope gain.
- [ ] T052 Do not stack multiple calibration wrappers; select one final envelope per score/policy.

## Phase 5 — Handoff

- [ ] T060 Write `STAGE0_REPORT.md` and `coverage_risk.csv`.
- [ ] T061 Document assumptions, exchangeability limitations, recalibration triggers and sample sizes.
- [ ] T062 Update roadmap and choose `KILLED | V1_SAFE_SLICE | CANDIDATE_SAFE_SLICE | QUALIFIED_WRAPPER`.

## Spend

No paid calls are authorized. This feature should reuse existing scores/outcomes.