# Implementation Plan: Sequential Value-of-Information Controller

## Goal

Test whether adaptive action ordering/stopping beats paying for a fixed cascade, using the simplest sequential decision model that can answer the question.

## Constitution Check

- train-only replay first;
- no RL first;
- each action must have independent evidence;
- V1/fixed-cascade controls mandatory;
- total cost includes every purchased action;
- future/counterfactual outcomes excluded from state;
- identified telemetry required for later real-data learning.

## Suggested Layout

```text
experiments/106/
  replay_env.py
  action_models.py
  voi.py
  policies.py
  evaluate.py
results/106/
  PREREG.md
  stage0_report.md
  action_value.csv
  trajectories.jsonl
```

## Stage-0 Replay Environment

Define one row/request as an episode. The environment stores full outcomes for evaluation but exposes only outcomes of actions purchased by the policy.

State schema:

- immutable request features;
- current answer/evidence summaries;
- action-history bitset;
- cumulative monetary cost;
- cumulative latency proxy;
- support/risk state;
- available-action mask.

Action result schema:

- observed quality/evidence;
- cost;
- latency;
- failure/unavailable flag;
- next-state features.

The policy implementation must not receive hidden full-information labels.

## Action Selection

Start with at most three nonterminal actions. Candidate order is evidence-driven, not fixed by this spec.

### Myopic model

For each action `a`, fit expected incremental terminal utility conditional on current state. Choose action with highest positive `E[ΔU|s,a] - cost_penalty`; otherwise stop.

Use simple ridge/logistic/GBDT only if already available; prefer interpretable models. Cross-fit action-value predictions.

### Depth-2 extension

Only if myopic passes Stage 0. Approximate one further lookahead using cached action models/dynamic programming. No policy-gradient training.

## Baselines

- V1/base;
- best fixed cascade using same actions;
- fixed cheapest-to-expensive ladder;
- best single extra action;
- oracle sequence diagnostic.

Ensure all baselines are charged identical action costs.

## Economics

Terminal utility should be reported both as raw quality/cost pairs and a λ-adjusted scalar for frozen λ grid. A policy cannot win solely because one arbitrary λ was favorable.

Latency can be a secondary penalty; report quality/cost frontier even if latency weights are uncertain.

## Statistics

- deterministic train-derived holdout;
- >=10 folds/seeds when model fitting varies;
- paired bootstrap policy deltas;
- action-value calibration bins;
- policy action-frequency and stop-depth distributions;
- per-task-family regret vs best fixed/oracle.

## Cost Plan

Stage 0 uses stored actions/outcomes: $0. If a candidate action lacks stored outcomes, do not generate them until a simple upper-bound calculation shows it could matter and an operator approves the smallest pilot.

## Kill Logic

- myopic fails materiality => kill 106; no RL rescue attempt;
- myopic degenerates to fixed cascade and offers no benefit => use fixed policy, kill controller complexity;
- depth-2 adds no material benefit => keep myopic;
- action-value model unstable/unsupported => remove that action or back off;
- 105 safety constraint turns most actions unavailable => recompute economics honestly, not bypass safety.

## Real-Data Extension

Only after 101 provides identified logs. Use OPE/DR action-value estimation for partially observed actions. Do not train sequential policy from deterministic historical logs as though all action outcomes were observed.

## Deliverables

- replay environment with hidden-counterfactual tests;
- action-value models and policy traces;
- fixed-vs-VOI frontier;
- decision outcome `KILLED | FIXED_POLICY_WINS | MYOPIC_PASS | DEPTH2_PASS | QUALIFIED_CONTROLLER`.