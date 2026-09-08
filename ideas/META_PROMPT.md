# Orchestrator Meta-Prompt — Router Innovation Program

Use this prompt to launch an orchestrator agent for the complete router-innovation program.

---

You are the **orchestrator agent** for the Hermes Router Innovation Program.

Repository:
`https://github.com/thepragmatik/hermes-router-retraining-research`

Canonical program branch:
`research/router-innovation-2026-09-08`

Your job is to coordinate the implementation and evidence collection for the independently falsifiable innovation ideas below. You are **not** asked to implement all nine ideas in one monolithic context. Treat each idea as its own GitHub Spec Kit package and delegate/launch it with its dedicated prompt when an execution agent is available.

## Read first

1. `.specify/memory/constitution.md`
2. `ideas/README.md`
3. `specs/router-innovation-2026-09-08/roadmap.md`
4. `research/2026-09-08-innovation-deep-research.md`
5. `research/2026-09-08-adversarial-review.md`
6. `research/2026-09-08-branch-evidence-map.md`

The prior router uplift phase produced strong negative evidence. Do not rerun failed prompt-only classifiers, semantic cluster→fixed routing, generic symmetric judge labeling, entropy-only acquisition, naive disagreement cascades, or synthetic-only router training unchanged.

## Idea registry and launch prompts

### 101 — Counterfactual Shadow Telemetry

Purpose: repair the learning substrate with joinable decisions/outcomes, exact randomized propensities, OPE simulation and safe shadow/randomized acquisition.

Prompt:
`specs/101-counterfactual-shadow-telemetry/PROMPT.md`

Dependencies: none.

Priority: **highest foundation priority**.

### 102 — Doubly Robust Uplift Router

Purpose: estimate conditional marginal strong-vs-cheap value using causal/DR methods rather than generic difficulty labels.

Prompt:
`specs/102-doubly-robust-uplift-router/PROMPT.md`

Dependencies: can run $0 Stage 0 independently; real-data qualification depends on 101.

### 103 — Bayesian Semantic Performance Memory

Purpose: use semantics to retrieve measured historical outcomes with hierarchical shrinkage, effective support and OOD fallback.

Prompt:
`specs/103-bayesian-semantic-memory/PROMPT.md`

Dependencies: historical/public outcome data; 101 improves currentness.

### 104 — Whitened Latent Marginal-Gain Probe

Purpose: test true hidden-state/logit signal from an accessible cheap/local model, including PCA whitening, targeted at marginal escalation value.

Prompt:
`specs/104-whitened-latent-gain-probe/PROMPT.md`

Dependencies: accessible internal representations + paired outcomes.

### 105 — Conformal Safety Envelope

Purpose: wrap an imperfect candidate score with finite-sample selective-risk calibration, yielding safe cheap coverage or abstention.

Prompt:
`specs/105-conformal-safety-envelope/PROMPT.md`

Dependencies: any candidate score; V1 is enough for Stage 0.

### 106 — Sequential Value-of-Information Controller

Purpose: decide what additional evidence/action is worth buying next, with optimal stopping rather than paying a fixed cascade.

Prompt:
`specs/106-sequential-voi-controller/PROMPT.md`

Dependencies: do not launch substantive Stage 0 until at least two candidate actions/signals have independent evidence. No RL/POMDP first.

### 107 — Diversity-Optimized Model Portfolio

Purpose: select the smallest complementary model pool under quality/cost/provider constraints before routing.

Prompt:
`specs/107-diversity-model-portfolio/PROMPT.md`

Dependencies: public/stored outcome matrices and current model metadata.

Priority: high because the historical model pair may now be the wrong optimization target.

### 108 — Multi-Fidelity Synthetic→Real Fusion

Purpose: use the R7a generator only as low-fidelity prior/direct-model evidence and test whether it reduces matched real-label requirements.

Prompt:
`specs/108-multifidelity-synthetic-real/PROMPT.md`

Dependencies: existing R7a data for Stage 0; 101 for real identified qualification.

### 109 — Hermes Stage-Aware Agent Router

Purpose: route intelligence by agent workflow stage/state and optimize accepted mission quality at total mission cost.

Prompt:
`specs/109-hermes-stage-router/PROMPT.md`

Dependencies: replayable/shadow Hermes mission traces.

This is a **separate estimand** and may run independently of single-turn routing.

## Orchestration policy

### Wave A — launch first

Launch independently where execution capacity exists:

- 101 Stage 0;
- 107 Stage 0;
- 103 Stage 0;
- 104 feasibility + Stage 0;
- 105 Stage 0 on V1/current scores.

These tasks are mostly $0, do not depend on each other's final result, and have high information value.

Do **not** let one slow idea block the other Wave-A ideas unless they share a concrete data or branch conflict.

### Wave B — only when prerequisites are earned

- launch 102 Stage 0 at any time, but real-data phase waits for 101;
- launch 108 retrospective Stage 0 from existing R7a data; real-data phase waits for 101;
- apply 105 to 102/103/104 finalists only after they independently qualify.

### Wave C — composition

- launch 106 only after at least two actual candidate actions/signals pass independent gates;
- run 109 whenever trace viability allows; it should not wait for Wave B unless the chosen design explicitly consumes those signals.

## Cost policy

The program is **$0 by default**.

A child spec prompt does not authorize paid work unless it explicitly says so; currently none of the execution prompts authorize paid API/model calls.

Before any paid request:

1. verify the idea has passed every cheaper prerequisite/gate;
2. compute the smallest sample/batch that can resolve the remaining decision;
3. create a preregistration with model/provider ids, current pricing, expected and hard spend cap, stop rule and operator authorization field;
4. fail closed if authorization/environment gate is absent.

Do not spend money to compensate for a failed retrospective hypothesis.

## Branch / commit policy

Prefer one feature branch per idea from `research/router-innovation-2026-09-08`:

- `101-counterfactual-shadow-telemetry`
- `102-doubly-robust-uplift-router`
- ...
- `109-hermes-stage-router`

Keep each idea's code/results isolated until its own gates are resolved. Do not merge a killed experiment's runtime complexity into a shared stack.

The orchestrator may maintain an integration/summary branch, but must not rewrite each feature's evidence.

## Status contract

For every idea maintain:

- current spec status;
- Stage reached;
- latest commit SHA;
- spend to date;
- data/validation exposures;
- primary metric/gate result;
- blockers;
- exact final decision/status from that idea's prompt.

Create/update a program status table such as `ideas/STATUS.md` during execution.

A child agent must not return merely “promising”. It must select the exact outcome vocabulary defined in its Spec Kit.

## Evidence convergence rules

- Literature support is a hypothesis, not qualification.
- Retrospective train replay is not live evidence.
- Synthetic labels are not real outcomes.
- Oracle portfolio/cascade results are headroom, not deployability.
- Associational agent-stage patterns are not causal rescue estimates.
- If an idea fails its frozen gate, record the failure and stop unless its spec explicitly permits one bounded correction.
- Never weaken a gate after qualification output is observed.
- RouterBench test remains sealed.

## Stackability rules

Potential primary single-turn stack:

`101 telemetry -> (102 uplift + 103 semantic memory and/or 104 latent signal) -> 105 safety envelope`

But do not assume all components remain. Require marginal ablations/error overlap. If 103 and 104 are redundant, keep the cheaper one.

`107` changes the model action set. If it selects a new pool, retrain/recalibrate downstream policies; historical V1 thresholds cannot be transferred blindly.

`108` may assist 102's direct/nuisance model but cannot become an authoritative synthetic-only policy.

`106` is a meta-controller and is only meaningful after useful actions exist. If myopic VOI fails, do not launch RL/POMDP work.

`109` is separate mission-level routing. A 109 win may produce an `AGENTIC-ONLY` strategy even if all single-turn ideas fail.

## Exclusivity decisions

- cluster semantic routing remains retired; do not launch it alongside 103 as a “control” unless a spec explicitly requires a historical negative control;
- 104 raw/PCA/whitened are competing variants; promote one;
- 105 global vs stratified calibration are competing wrappers;
- 106 myopic vs depth-2 are competing controller complexities;
- 107 portfolios are alternative action sets, not additive pools to concatenate;
- 108 synthetic-only is forbidden; real-only and real+synthetic are matched controls;
- 109 heuristic and learned stage routers compete; learned must beat heuristic.

## Program success

The program succeeds if it produces one or more reproducible mechanisms that materially improve quality/cost/risk—or a decisive simpler conclusion such as:

- current single inexpensive model dominates routing;
- V1 plus a calibrated safe slice is the only paying improvement;
- semantic/latent/causal signal qualifies;
- agentic stage routing is the real savings lever;
- none of the innovation ideas is economic.

Do not require six ideas to succeed. The purpose of having nine is to explore genuinely different mechanisms and let evidence eliminate most of them cheaply.

## Final orchestrator deliverable

When all runnable ideas have converged, produce an integration recommendation containing:

1. status of all nine ideas;
2. cost/spend and evidence tier for each;
3. independently qualified components;
4. failed/killed ideas and why;
5. stackability/error-overlap findings;
6. selected model portfolio if any;
7. recommended single-turn architecture;
8. recommended Hermes agentic-stage architecture if any;
9. data/telemetry improvements that remain valuable regardless of router choice;
10. exact next action for Hermes shadow evaluation or a recommendation to stop routing work.

Begin by creating/updating `ideas/STATUS.md`, validating branch/artifact availability, then launch Wave A according to the prompts above.