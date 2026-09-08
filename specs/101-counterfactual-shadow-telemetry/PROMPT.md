# Agent Prompt — Execute Idea 101: Counterfactual Shadow Telemetry

You are the execution agent for **Idea 101 — Counterfactual Shadow Telemetry** in repository:

`https://github.com/thepragmatik/hermes-router-retraining-research`

Work on branch `research/router-innovation-2026-09-08` or create a feature branch from it named `101-counterfactual-shadow-telemetry`.

## Mission

Implement this idea to its evidence gates. Do not merely discuss it. The purpose is to repair the learning substrate so future routing policies can be evaluated from real/shadow traffic with joinable outcomes and statistically valid propensities.

Read in this order:

1. `.specify/memory/constitution.md`
2. `specs/101-counterfactual-shadow-telemetry/spec.md`
3. `specs/101-counterfactual-shadow-telemetry/plan.md`
4. `specs/101-counterfactual-shadow-telemetry/tasks.md`
5. `research/2026-09-08-branch-evidence-map.md`
6. `research/2026-09-08-adversarial-review.md`
7. branch evidence for the broken shadow logger, especially `results/V1_BASELINE_GAPS.md`

## Non-negotiable execution rule

**Do Stage 0 first.** Build the train-only logging-policy simulator and OPE reconstruction harness before modifying the live HTTP shadow service. If Stage 0 cannot reconstruct known policy values under the frozen gates, stop and mark the idea killed/blocked. Do not compensate by loosening gates or by collecting live traffic.

## Required behavior

- RouterBench test remains sealed.
- V1 weights/threshold remain untouched.
- Default spend is $0.
- No paid model calls are authorized by this prompt.
- Exact action propensities must be recorded for randomized events; never infer them after the fact.
- Outcome provenance must distinguish task-native/human/benchmark/judge/synthetic evidence.
- Raw prompt text is not required in the decision ledger.
- Prefer simple local storage and auditable epsilon exploration over new infrastructure or complex bandit algorithms.
- Live user-visible exploration is forbidden until Stage 0/1 pass and a separate operator-approved prereg exists.

## Deliverables

Complete the tasks in `tasks.md`, commit code/tests/results, and produce the required Stage-0/Stage-1 reports. Update the roadmap status and mission log with one clear outcome:

`KILLED | STAGE0_PASS | SHADOW_READY | LIVE_ELIGIBLE`

Do not stop at a design memo. If a prerequisite is missing, complete every $0 simulator/fixture task possible and document the exact blocker.

Begin now with `results/101/PREREG.md`, artifact hashes, and the full-information logging-policy simulator.