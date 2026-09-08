# Feature Specification: Sequential Value-of-Information Controller

**Feature Branch:** `106-sequential-voi-controller`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** at least two meaningful actions/evidence sources; useful inputs may come from 103/104/105/107.

## Problem

A fixed cascade asks a crude question: route weak or strong. A more useful decision may be **what is the cheapest next action worth buying given what we know now?** Examples: accept, obtain another cheap sample, run a deterministic verifier/tool, query a complementary cheap model, use a mid-tier, or escalate to frontier.

This feature treats routing as a sequential decision / optimal-stopping problem. It begins with a deliberately simple, myopic value-of-information (VOI) controller; sophisticated RL/POMDP methods are out of scope until the simple controller proves that sequential choice has economic headroom.

## Decision Model

State `s` contains only evidence already available at that point:

- prompt/task metadata;
- current model answer/outcome summaries;
- semantic-memory posterior/support if qualified;
- latent/internal confidence if qualified;
- verifier/tool results;
- actions already purchased;
- cumulative cost/latency;
- model/action availability.

For candidate next action `a`, approximate:

`VOI(a|s) = E[max_b U(b, s') | do(a), s] - max_b U(b,s) - Cost(a)`.

Execute the cheapest/most valuable action only when estimated VOI is positive; otherwise stop/accept/fallback according to risk policy.

## User Stories

### Story 1 — Decide whether another cheap action is worth buying

Given current evidence, estimate whether an additional cheap sample/verifier/model call has positive expected value versus accepting or escalating now.

### Story 2 — Stop early

If current evidence is already decisive, stop rather than following a fixed cascade that purchases unnecessary actions.

### Story 3 — Avoid expensive dead ends

If historical evidence shows an action rarely changes the final decision in this state, skip it and move directly to a better action or stop.

### Story 4 — Explain action economics

Every step should log expected value, action cost, realized result and stop reason for offline analysis.

## Requirements

- **FR-001:** Stage 0 MUST use a replay/simulation environment with known action outcomes and costs; no live adaptive controller first.
- **FR-002:** First implementation MUST be myopic/one-step or depth-2 dynamic programming. Deep RL is forbidden until this passes.
- **FR-003:** Include simple fixed-policy baselines: V1, best fixed cascade, always-frontier, and each single useful action policy.
- **FR-004:** Controller state MUST exclude future/counterfactual correctness.
- **FR-005:** Action-value models MUST be trained only from train-safe or identified historical data.
- **FR-006:** Costs must include inference, tool/verifier cost, switching overhead and latency penalty if relevant.
- **FR-007:** Stop/accept decisions MUST respect any 105 safety envelope when configured.
- **FR-008:** Action availability and failure must be modeled; unavailable actions cannot retain stale value estimates.
- **FR-009:** Output per decision: state version, available actions, estimated VOI, chosen action, cumulative cost, stop reason.
- **FR-010:** Evaluate action-frequency, quality, total cost, latency and regret against full-information oracle; not only classifier accuracy.
- **FR-011:** Each action must independently show some value or serve a required safety role before it enters the controller.
- **FR-012:** RouterBench test remains sealed.

## Stage 0 — Cheapest Falsification

Build a train-only replay environment from stored model outcomes and any objective verifier/action outputs. Restrict to at most 3 dynamic actions plus stop/frontier.

Compare:

1. best fixed cascade with same actions;
2. fixed action order with threshold stopping;
3. myopic VOI controller;
4. depth-2 DP/controller if myopic shows signal;
5. oracle action sequence diagnostic.

The idea survives if:

- myopic VOI beats the best fixed cascade by >= **3% relative total cost at matched quality** or >= **0.5pp quality at approximately matched cost** on train-derived holdout, or achieves another program-material improvement;
- it does not simply degenerate to one fixed action order on >95% of rows unless that fixed order itself is the economic winner;
- action-value calibration is directionally correct: states with positive estimated VOI have materially higher realized incremental utility than negative-VOI states;
- benefit survives >=8/10 seeds/folds and is not entirely oracle leakage.

If myopic fails, kill sequential control before trying RL. If myopic passes but depth-2 adds no value, keep myopic.

## Candidate Actions

Only actions with evidence should be considered, e.g.:

- accept current cheap answer;
- second sample from cheap model if repeated sampling has measured repair value;
- deterministic verifier/tool where coverage exists;
- query complementary model selected by 107;
- escalate to frontier;
- conservative abstain/fallback.

Do not include failed P1 disagreement trigger as an action rule; the controller may still purchase a second model only if its state-dependent value is learned from evidence.

## Statistics / Estimation

Start with simple regressions for action incremental utility, optionally using 103/104 features. Cross-fit if the same replay rows are used to learn and evaluate action values. If real logged partial feedback is later used, require 101/OPE-compatible estimation.

## Expected Benefit

A successful controller can stack several individually modest interventions without paying for all of them on every request, addressing the cost problem that killed prior fixed cascades.

## Stackability / Exclusivity

- Meta-policy over qualified signals/actions from 103–107.
- Should not be implemented before at least two actions have independent evidence.
- Myopic and depth-2 are alternative promoted policies; retain simpler if equivalent.
- Deep RL/POMDP is explicitly exclusive until the simple VOI controller passes and exposes a specific residual long-horizon gap.