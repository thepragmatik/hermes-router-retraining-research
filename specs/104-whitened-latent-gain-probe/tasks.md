# Tasks: Whitened Latent Marginal-Gain Probe

## Phase 0 — Freeze and feasibility

- [ ] T001 Read constitution, spec, plan and `results/P3_INTERNAL_CONFIDENCE.md` to preserve the distinction from the prior stored-response experiment.
- [ ] T002 Confirm an accessible local/cheap model exposes hidden states/logits without paid API calls; otherwise record `REPRESENTATION_BLOCKED` and stop.
- [ ] T003 Write `results/104/PREREG.md` freezing model revision, template, layers, token summaries, PCA dimensions, target pair, folds, seeds, baselines and gates.
- [ ] T004 Record hashes and assert sealed test is untouched.

## Phase 1 — Compact representation capture

- [ ] T010 Implement streaming latent-summary extraction; avoid full activation dumps.
- [ ] T011 Capture prompt BGE, logit/entropy and response-shape controls on the exact same rows.
- [ ] T012 Add row-join, no-label-leakage and label-shuffle tests.
- [ ] T013 Measure covariance spectrum/condition number/an\-isotropy for each frozen layer summary.

## Phase 2 — $0 probe experiment

- [ ] T020 Implement raw standardized linear probe.
- [ ] T021 Implement fold-local PCA probe.
- [ ] T022 Implement fold-local whitened PCA with eigenvalue floor.
- [ ] T023 Run frozen dimension/layer grid using train-only CV.
- [ ] T024 Evaluate pairwise-gain metric, task-family metrics, calibration and task-only baseline.
- [ ] T025 Convert each winning score to the same frozen cost-aware routing policy and report frontier/oracle-capture.
- [ ] T026 Run >=2 seeds where generation/capture is stochastic and paired bootstrap policy deltas.

## Stage-0 decision

- [ ] T030 Apply spec gates without retuning.
- [ ] T031 If latent signal fails, mark `KILLED` and stop.
- [ ] T032 If raw/PCA wins and whitening does not, mark `RAW_OR_PCA_PASS` and delete whitening from the promoted design.
- [ ] T033 If whitened wins, freeze transform/probe version and mark `WHITENED_PASS`.

## Phase 3 — runtime feasibility

- [ ] T040 Benchmark base model generation vs latent capture + transform + probe.
- [ ] T041 Measure memory/storage overhead and test batch/concurrency behavior.
- [ ] T042 Verify model/template/revision mismatch causes a loud compatibility failure.
- [ ] T043 Run paraphrase/format perturbation and task-stratified calibration checks.

## Phase 4 — integration ablation

- [ ] T050 If 102 exists, add latent signal as one feature family and measure marginal frontier value.
- [ ] T051 If 103 exists, measure route/error overlap with semantic memory; keep both only if complementary.
- [ ] T052 Optionally calibrate with 105; report safety benefit separately from ranking gain.

## Phase 5 — handoff

- [ ] T060 Write Stage-0 and runtime reports; commit transform metadata.
- [ ] T061 Update roadmap/component ledgers.
- [ ] T062 Choose `KILLED | REPRESENTATION_BLOCKED | RAW_OR_PCA_PASS | WHITENED_PASS | QUALIFIED_FEATURE`.

## Spend

This prompt authorizes no paid labels or remote inference. If missing paired outcomes are the sole blocker after representation signal is established, quantify the minimum required sample before requesting operator spend.