# Feature Specification: Hermes Stage-Aware Agent Router

**Feature Branch:** `109-hermes-stage-router`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** replayable or shadow Hermes mission traces with stage/state/outcome information.

## Problem

Single-turn routing asks whether one prompt deserves a strong model. Hermes is an agent: a mission may include planning, file reading, tool calls, coding, testing, failure recovery, synthesis and final review. Expensive intelligence may be valuable only at certain **workflow stages or state transitions**.

This feature changes the unit of routing from “whole prompt” to **agent step / workflow stage**. It tests whether strong-model calls can be concentrated at high-value moments while cheap models handle routine steps.

Success here does not validate RouterBench routing, and RouterBench success does not validate this feature.

## User Stories

### Story 1 — Identify where strong calls actually help

As a researcher, measure which mission states/stages receive the largest marginal benefit from stronger intelligence.

### Story 2 — Start with simple stage rules

As an operator, test transparent heuristics such as “escalate after repeated test failure” before training a learned stage router.

### Story 3 — Reduce wasted strong turns

If strong calls during routine reads/tool formatting rarely change mission outcomes, keep those stages cheap.

### Story 4 — Escalate recovery/high-impact decisions

When the mission is stuck, repeatedly failing, entering unfamiliar/OOD tool use, or making a consequential final decision, selectively buy stronger intelligence if evidence shows it helps.

## Trace Contract

Minimum per step:

- `mission_id`, `step_id`, timestamp;
- stage/state label or raw event features;
- prompt/context-size summaries (privacy-safe where needed);
- model/action used and model revision;
- tool invoked/result status;
- test/build/lint result where available;
- retry/no-progress indicators;
- cumulative tokens/cost/latency;
- final mission success/acceptance and outcome provenance;
- link to parent/previous step.

For counterfactual learning, exact action propensities or paired/shadow alternate outcomes are required; otherwise analysis remains descriptive/heuristic.

## Candidate Stage Features

Use deterministic/runtime-visible signals first:

- stage type: planning/read/edit/tool/test/review/final;
- number of recent failed tool/test attempts;
- no-progress/repeated-action count;
- context length/token budget;
- unfamiliar tool/domain/OOD support;
- code/test status;
- changed-file count/risk indicators;
- prior model tier and recent escalation history;
- time/cost already spent.

Do not feed the final mission outcome or future steps into the router state.

## Requirements

- **FR-001:** Stage 0 MUST inventory and validate trace quality before learning a policy.
- **FR-002:** Compare all-cheap, all-strong/frontier, fixed mission-level model, V1-like per-prompt baseline where meaningful, and simple stage heuristics.
- **FR-003:** First policy MUST be rule/score-based or simple contextual model. No deep RL first.
- **FR-004:** Primary metric is accepted mission success/quality at total mission cost, including retries and wasted loops.
- **FR-005:** Report strong-call contribution by stage and whether strong calls actually rescue missions/steps.
- **FR-006:** If counterfactual alternate model outcomes are not observed, causal claims MUST be restricted; use randomized/shadow design for later qualification.
- **FR-007:** High-risk/security-sensitive stage rules may force strong review independently of economic routing and must be reported separately.
- **FR-008:** Stage labels/features MUST be reproducible from runtime events; subjective post-hoc labels cannot be the only input.
- **FR-009:** Policy MUST include hysteresis/cooldown or other guard against rapid model thrashing if multiple switches are allowed.
- **FR-010:** Model-switch latency/context-transfer cost MUST be included.
- **FR-011:** Evaluate mission-level robustness across task types and long/short missions.
- **FR-012:** Single-turn RouterBench test remains sealed and is not the qualification set for this feature.

## Stage 0 — Cheapest Falsification

### 0A Trace viability

On existing Hermes traces, require:

- >= **100 completed missions** or enough steps to produce >=500 stage decisions across at least 3 mission/task types; otherwise report `TRACE_DATA_INSUFFICIENT`;
- >=95% steps with model id, step order and usable stage/runtime features;
- final outcome available for >=80% missions or a clearly defined proxy with provenance;
- retries/tool/test outcomes sufficiently logged to identify progress/failure states.

### 0B Descriptive value concentration

Before training, estimate whether expensive calls are concentrated in potentially high-value stages. Compare strong-vs-cheap outcomes only where paired/randomized evidence exists; otherwise report associations.

Proceed to policy tests only if at least one stage/state has >= **2x** the observed rescue/utility rate or a clearly material mission-impact difference relative to routine stages, with enough support to test.

### 0C Simple heuristic replay/shadow test

Examples to preregister:

- strong for initial planning only;
- strong after 2 consecutive test/tool failures;
- strong for final high-impact review;
- cheap for routine read/transform steps;
- combinations with cooldown.

Idea survives if a simple stage policy achieves >= **10% relative total model-cost reduction at matched mission success**, or >= **3pp mission success improvement at <=10% extra cost**, versus the best fixed mission-level baseline, with uncertainty/replication across task types.

If no simple stage policy shows headroom, kill learned stage routing. If simple rules win materially, a learned policy is optional and must beat them.

## Learned Policy (conditional)

Only after simple headroom:

- regularized logistic/GBDT/contextual policy for “strong value at this stage”;
- sequential/hysteresis state features;
- if real randomized action logs exist, use 101-style OPE/DR estimation;
- no RL until a clearly documented long-horizon residual gap remains after simple policy.

## Expected Benefit

Potentially large mission-level savings because the agent can reserve frontier intelligence for planning/recovery/review rather than paying it on every routine step. Also improves telemetry by making expensive-step contribution observable.

## Stackability / Exclusivity

- Separate estimand from 102–108; can coexist operationally with them.
- 105-style safety envelope can wrap stage decisions if calibrated on stage data.
- 106 VOI concepts may later govern stage actions, but do not combine until 109 simple stage routing passes.
- Fixed heuristic vs learned stage router are alternative promoted policies; prefer heuristic if statistically/economically equivalent.
- A success here may justify `AGENTIC-ONLY PIVOT` even if single-turn router innovation fails.