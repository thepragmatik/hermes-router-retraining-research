# Tasks: Bayesian Semantic Performance Memory

## Phase 0 — Freeze

- [ ] T001 Read constitution, spec, plan, semantic-signal prereg, ContextualRouter research notes, and prior failed cluster evidence.
- [ ] T002 Write `results/103/PREREG.md` freezing train folds, embedding version, `k` grid, decay grid, prior strengths, support rule, routing-cost grid and perturbation set.
- [ ] T003 Record hashes/provenance and assert test split is untouched.

## Phase 1 — $0 retrieval baselines

- [ ] T010 Reuse/reproduce frozen BGE embeddings and build train-only neighbor index.
- [ ] T011 Implement global-prior and task-prior baselines.
- [ ] T012 Implement raw kNN measured-outcome estimator with `n_eff` and distance diagnostics.
- [ ] T013 Implement empirical-Bayes/hierarchical shrinkage posterior.
- [ ] T014 Add per-neighbor provenance and pair/model revision checks.
- [ ] T015 Run train-CV probabilistic evaluation (Brier/log loss/calibration/gain ranking).
- [ ] T016 Convert each estimator to the same simple cost-aware routing diagnostic and emit frontier.

## Phase 2 — robustness and support

- [ ] T020 Build semantic-preserving paraphrase/format/distractor perturbation fixtures from train-only prompts.
- [ ] T021 Measure neighbor overlap, posterior delta, route flip and support response.
- [ ] T022 Test deliberately OOD/low-support examples and verify posterior backs off to priors.
- [ ] T023 Plot/measure error vs distance and `n_eff`; decide whether support signal is useful.

## Stage-0 decision

- [ ] T030 Apply frozen gates. If neither raw kNN nor shrinkage helps, mark `KILLED` and stop.
- [ ] T031 If raw kNN helps but shrinkage does not, mark `KNN_ONLY`; remove unnecessary Bayesian complexity.
- [ ] T032 If shrinkage passes, mark `SEMANTIC_MEMORY_PASS` and freeze winning hyperparameters.

## Phase 3 — capability decomposition (conditional)

Only after a semantic memory baseline shows signal.

- [ ] T040 Define a minimal capability schema using deterministic metadata first.
- [ ] T041 Add capability-aware retrieval/partial pooling as one ablation.
- [ ] T042 If any LLM-based decomposition is used, measure label stability across paraphrases/repeats before qualification.
- [ ] T043 Retain capability decomposition only if it improves held-out frontier/calibration beyond plain memory.

## Phase 4 — external and live history (conditional)

- [ ] T050 Add provenance-separated public routing data as a transfer prior; preserve local-only control.
- [ ] T051 Reject raw pooling if model-pair/label semantics are incompatible.
- [ ] T052 When 101 data exists, add current-traffic memory with temporal/version partitions and drift handling.

## Phase 5 — handoff

- [ ] T060 Write `STAGE0_REPORT.md`, retrieval diagnostics and frontier CSV.
- [ ] T061 Update roadmap and component ledgers.
- [ ] T062 Document whether 103 should feed 102/105/106 and what support field is authoritative.
- [ ] T063 Choose `KILLED | KNN_ONLY | SEMANTIC_MEMORY_PASS | QUALIFIED_FEATURE`.

## Spend

Stage 0 is $0. Do not buy LLM capability labels or new embedding APIs before the frozen retrieval mechanism passes.