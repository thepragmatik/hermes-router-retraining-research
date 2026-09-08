# Tasks: Sequential Value-of-Information Controller

## Phase 0 — Eligibility and freeze

- [ ] T001 Read constitution, spec, plan and results for any candidate actions/signals.
- [ ] T002 Inventory possible actions and exclude any with no independent evidence or no measurable outcome/cost.
- [ ] T003 Freeze max action set (<=3 dynamic actions), state features, utility/cost grid, replay split, seeds and Stage-0 gates in `results/106/PREREG.md`.
- [ ] T004 Assert sealed test untouched and hidden counterfactuals inaccessible to policy code.

## Phase 1 — $0 replay substrate

- [ ] T010 Implement replay environment with strict separation between policy-visible state and evaluator-only full outcomes.
- [ ] T011 Add action cost/latency accounting and unavailable-action handling.
- [ ] T012 Implement V1/base, best fixed cascade, cheapest-first ladder and single-action controls.
- [ ] T013 Add oracle diagnostic for headroom only.

## Phase 2 — Myopic VOI

- [ ] T020 Fit cross-fitted simple action incremental-utility models.
- [ ] T021 Implement positive-VOI action choice and explicit stop behavior.
- [ ] T022 Sweep frozen λ grid; log trajectories, action frequencies and costs.
- [ ] T023 Evaluate realized utility conditioned on predicted positive/negative VOI.
- [ ] T024 Run >=10 folds/seeds and paired bootstrap against best fixed cascade.

## Stage-0 decision

- [ ] T030 Apply frozen gates. If myopic fails, mark `KILLED` or `FIXED_POLICY_WINS`; stop—no RL.
- [ ] T031 If myopic passes, freeze it as the baseline for any depth-2 work.

## Phase 3 — Depth-2 (conditional)

- [ ] T040 Implement one extra lookahead using frozen action-value models/dynamic programming.
- [ ] T041 Compare to myopic on identical actions/costs.
- [ ] T042 Keep depth-2 only if material gain survives uncertainty; otherwise remove it.

## Phase 4 — Safety / real-data adapters

- [ ] T050 If 105 qualified, enforce its accept/fallback constraints and recompute frontier.
- [ ] T051 If 101 real logs exist, replace full-information action models with OPE/DR-compatible estimates; document support.
- [ ] T052 Run adversarial prompt/cost forcing perturbations on controller state inputs.

## Phase 5 — Handoff

- [ ] T060 Write Stage-0 report, action-value CSV and sample trajectories.
- [ ] T061 Record which actions actually contribute unique value.
- [ ] T062 Update roadmap and choose `KILLED | FIXED_POLICY_WINS | MYOPIC_PASS | DEPTH2_PASS | QUALIFIED_CONTROLLER`.

## Spend

No paid action acquisition is authorized. Missing action outcomes require a separate upper-bound justification and operator gate.