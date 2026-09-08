# Tasks: Hermes Stage-Aware Agent Router

## Phase 0 — Trace viability

- [ ] T001 Read constitution, spec, plan and available Hermes trace/log documentation.
- [ ] T002 Create `results/109/PREREG.md` freezing trace sources, stage schema, outcome fidelity, minimum sample gates, baselines and bootstrap unit.
- [ ] T003 Inventory missions/steps/model ids/tool/test fields/outcomes and write `trace_quality.json`.
- [ ] T004 If trace gates fail, write an exact telemetry gap contract and mark `TRACE_DATA_INSUFFICIENT`; stop policy modeling.

## Phase 1 — Stage/state construction

- [ ] T010 Implement deterministic stage taxonomy with `unknown` fallback.
- [ ] T011 Implement runtime-visible history features: failures, retries, repeated actions, cost/tokens, context, switch count.
- [ ] T012 Add leakage tests proving final outcome/future steps are absent from policy state.
- [ ] T013 Quantify stage/task/support counts and apply hierarchical shrinkage for descriptive rates where useful.

## Phase 2 — Value concentration

- [ ] T020 Label each comparison as causal/paired/randomized vs associational.
- [ ] T021 Estimate strong-call rescue/utility by stage/state with mission-clustered uncertainty.
- [ ] T022 Identify whether any stage meets the preregistered concentration criterion.
- [ ] T023 If no stage has material headroom, mark `KILLED` and stop.

## Phase 3 — Simple heuristics

- [ ] T030 Preregister <=5 transparent stage rules and cooldown/hysteresis behavior before scoring.
- [ ] T031 Implement all-cheap/all-strong/fixed-mission/default controls.
- [ ] T032 Replay/shadow heuristic policies where evidence permits; charge switching/context-transfer cost.
- [ ] T033 Bootstrap by mission and report success, cost, retries, strong calls, switch count and task strata.
- [ ] T034 Apply heuristic gate. If fail, mark `KILLED`; do not train a learned router.

## Phase 4 — Learned stage policy (conditional)

- [ ] T040 Fit a simple regularized stage-value model on train-safe/identified data.
- [ ] T041 If propensities exist, use OPE/DR-compatible evaluation; otherwise keep claim descriptive/shadow-only.
- [ ] T042 Compare directly against best heuristic on mission-level frontier.
- [ ] T043 Retain learned policy only if it materially beats heuristic after switching/maintenance cost.

## Phase 5 — robustness and handoff

- [ ] T050 Test long/short missions and multiple task types separately.
- [ ] T051 Stress repeated-failure loops, OOD tools and cost-forcing prompt patterns.
- [ ] T052 Write heuristic/learned reports and mission frontier.
- [ ] T053 Update roadmap and choose `TRACE_DATA_INSUFFICIENT | KILLED | HEURISTIC_PASS | LEARNED_PASS | QUALIFIED_AGENTIC`.

## Spend

No duplicate/paid model execution is authorized. If counterfactual stage coverage is missing, specify the smallest 101-compatible shadow/randomized collection plan for operator review.