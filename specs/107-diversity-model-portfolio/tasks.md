# Tasks: Diversity-Optimized Model Portfolio

## Phase 0 — Freeze and current snapshot

- [ ] T001 Read constitution, spec, plan, P0/P5 results and dataset guide.
- [ ] T002 Create `results/107/PREREG.md` freezing candidate data sources, eligibility filters, pool-size limit, objectives, marginal gates and realizability method.
- [ ] T003 Refresh current model/provider/pricing snapshot with source timestamps; do not rely on historical GPT-4/Mistral availability.
- [ ] T004 Assert RouterBench test remains sealed.

## Phase 1 — $0 matrix analysis

- [ ] T010 Load local train-safe outcome matrix and at least one compatible public routing matrix where available.
- [ ] T011 Normalize outcome/cost semantics without pretending incompatible metrics are identical.
- [ ] T012 Apply provider/privacy/capability eligibility before optimization.
- [ ] T013 Compute pairwise co-failure, unique successes, conditional rescue and incremental cost per rescue.
- [ ] T014 Implement brute-force subsets <=3 where feasible.
- [ ] T015 Implement cost-aware greedy/lazy-greedy selection and validate against brute force.
- [ ] T016 Emit quality/cost/size portfolio frontier.

## Stage-0 portfolio gate

- [ ] T020 Apply model marginal-contribution and portfolio gates.
- [ ] T021 Remove redundant models even if globally strong.
- [ ] T022 If one model dominates routing economics, mark `SINGLE_MODEL_PIVOT` and stop adding models.

## Phase 2 — realizability

- [ ] T030 Freeze the simplest available runtime-visible router proxy.
- [ ] T031 Measure fraction of oracle portfolio gain captured and net cost after routing overhead.
- [ ] T032 If <35% oracle gain is realizable, mark `ORACLE_ONLY_PORTFOLIO`; do not promote runtime complexity.
- [ ] T033 If 103/102 later qualify, rerun realizability as a separate ablation without changing selected portfolio on the same evaluation slice.

## Phase 3 — robustness

- [ ] T040 Bootstrap task rows/families and report selection frequency.
- [ ] T041 Stress current prices and remove one model at a time.
- [ ] T042 Check result on a second compatible dataset/task mix where possible.
- [ ] T043 Run basic provider/model unavailability fallback analysis.

## Phase 4 — handoff

- [ ] T050 Write current model snapshot, complementarity table, portfolio frontier and realizability report.
- [ ] T051 Update roadmap and flag downstream specs requiring recalibration if pool changes.
- [ ] T052 Choose `KILLED | SINGLE_MODEL_PIVOT | ORACLE_ONLY_PORTFOLIO | PORTFOLIO_PASS | QUALIFIED_POOL`.

## Spend

No broad new model evaluation is authorized. If public/stored matrices reveal a specific missing comparison with high decision value, quantify the minimum pilot and request a separate operator cap.