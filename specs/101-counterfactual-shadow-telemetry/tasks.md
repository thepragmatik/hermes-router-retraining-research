# Tasks: Counterfactual Shadow Telemetry

Tasks are ordered by **cheapest falsification first**. Do not skip ahead because later tasks are more interesting.

## Phase 0 — Freeze experiment contract

- [ ] T001 Read `.specify/memory/constitution.md`, this spec, plan, branch evidence map, and `results/V1_BASELINE_GAPS.md` from the generator branch history.
- [ ] T002 Create `results/101/PREREG.md` freezing: train-only source, action set, simulation seeds, logging policy, target policies, OPE estimators, support thresholds, Stage-0 gates.
- [ ] T003 Record hashes/revisions for all train/full-information artifacts. Assert RouterBench test is never loaded.

## Phase 1 — $0 simulator and schemas

- [ ] T010 Define versioned `DecisionEvent` and `OutcomeEvent` dataclasses/Pydantic-like validators without adding a heavyweight dependency unless already present.
- [ ] T011 Implement deterministic event-id and privacy-safe hash helpers for fixtures; keep production hash key external.
- [ ] T012 Implement logging-policy simulator with an epsilon-mixture that guarantees nonzero support for eligible actions.
- [ ] T013 Add invariant tests: action membership, probability sum, chosen propensity exactness, no zero propensity for sampled actions.
- [ ] T014 Implement full-information truth evaluator completely separate from the hidden-feedback OPE path.
- [ ] T015 Implement IPS and self-normalized IPS.
- [ ] T016 Implement cross-fitted DR with the simplest adequate outcome model first (regularized linear/logistic or existing router feature model).
- [ ] T017 Implement one robust heavy-weight variant (SWITCH-DR or frozen clipping) plus ESS/overlap diagnostics.
- [ ] T018 Add corrupted/missing propensity tests that must fail loudly.
- [ ] T019 Run Stage-0 simulation across frozen seeds and write `STAGE0_OPE.json/md`.

### Phase-1 stop gate

- [ ] T020 Compare Stage-0 output to spec gates. If it fails, permit only the single preregistered diagnostic correction. Re-run once. If it still fails, mark `KILLED` and stop; do not touch live shadow code.

## Phase 2 — Local telemetry plumbing

Only if Stage 0 passes.

- [ ] T030 Choose JSONL vs SQLite/WAL using expected write concurrency; document the decision and why the simpler option is sufficient.
- [ ] T031 Implement append-only decision logger with schema/version validation and visible error counter.
- [ ] T032 Implement append-only outcome writer and deterministic join/reconciliation report.
- [ ] T033 Add duplicate, late, provisional/final, contradictory-outcome fixtures.
- [ ] T034 Add raw-prompt leakage tests and a repo-level grep/PII test for fixture logs.
- [ ] T035 Add data-quality report: unique ids, missing provenance, missing propensity, unjoined outcomes, ambiguous joins, schema drift.
- [ ] T036 Load-test >=1,000 local events; measure logging p50/p95 overhead.

## Phase 3 — Shadow-service parity

- [ ] T040 Wire the *same* logger into HTTP `/route` and CLI paths; do not modify `router_v1/` model code.
- [ ] T041 Replace hardcoded placeholder ids with event ids/caller join fields while preserving backwards-compatible response shape if needed.
- [ ] T042 Verify service-side traffic creates logs; CLI/service parity test must pass.
- [ ] T043 Test kill switch, missing config, threshold-drift guard, logging I/O failure, service restart and concurrent requests.
- [ ] T044 Produce `STAGE1_DATA_QUALITY.md`; require all Stage-1 gates before any exploration work.

## Phase 4 — Exploration dry-run

- [ ] T050 Implement eligibility rules as deterministic, testable predicates.
- [ ] T051 Implement modes `disabled`, `shadow_dual`, `randomized_sentinel`; default `disabled`.
- [ ] T052 Implement seeded epsilon randomization with exact logged propensity.
- [ ] T053 Implement rate cap, per-run spend cap hooks, allowed actions, traffic exclusions and kill switch.
- [ ] T054 Add 10k-event simulation test proving realized exploration rate is consistent with configured probability and all randomized events contain propensities.
- [ ] T055 Draft, but do not execute, `experiments/101-live-exploration-prereg.md` with explicit operator approval fields.

## Phase 5 — Documentation and handoff

- [ ] T060 Update the innovation roadmap status for 101.
- [ ] T061 Add commands, data contracts, limitations, and estimator assumptions to a concise README in this spec folder if implementation needs it.
- [ ] T062 Record which downstream specs are unblocked: 102 and 108 only after real joinable outcome data exists.
- [ ] T063 Commit final decision: `KILLED`, `STAGE0_PASS`, `SHADOW_READY`, or `LIVE_ELIGIBLE` with evidence links.

## Cost discipline

No task above Phase 4 authorizes paid calls. A live exploration run is a separate operator decision. If a task can be answered by the simulator or fixtures, do that instead of buying model output.