# Implementation Plan: Hermes Stage-Aware Agent Router

## Goal

Determine whether model intelligence should be purchased at **specific agent stages/states** rather than selected once for an entire mission or prompt.

## Constitution Check

- separate agentic estimand;
- trace-quality gate before modeling;
- simple heuristics before learned policy;
- total mission cost/retries are primary economics;
- causal claims require paired/randomized/propensity evidence;
- no RL first;
- privacy-sensitive trajectory fields minimized.

## Suggested Layout

```text
experiments/109/
  trace_schema.py
  inventory.py
  stage_features.py
  heuristics.py
  replay.py
  learned_policy.py
  evaluate.py
results/109/
  PREREG.md
  trace_quality.json
  stage_value.csv
  heuristic_report.md
  mission_frontier.csv
```

## Trace Audit

Before any router work:

1. enumerate trace sources/versions;
2. validate mission/step ordering and model identity;
3. quantify stage/tool/test/failure-field coverage;
4. classify outcome fidelity;
5. measure mission/task diversity;
6. check whether alternate-model/paired/randomized data exists.

If the minimum Stage-0 trace gates fail, write the missing telemetry contract rather than manufacture stage labels.

## Stage Taxonomy

Prefer deterministic event-derived categories:

- plan/replan;
- read/search/context acquisition;
- transform/edit/code generation;
- tool call;
- test/build/verification;
- recovery after failure;
- synthesis/review;
- final/high-impact commit/response.

Allow `unknown`. Do not force every step into a guessed semantic category.

## Feature Engineering

Cheap runtime features only:

- current stage;
- last N tool/test statuses;
- consecutive failures;
- repeated action/file/tool pattern;
- elapsed steps/cost/tokens;
- context-size bucket;
- current diff/file count where available;
- OOD/tool familiarity signal;
- previous model tiers/switch count.

No future success, final grade or post-hoc human analysis may enter runtime features.

## Baselines

- all cheapest eligible model;
- all frontier/strong;
- fixed model chosen at mission start;
- existing Hermes default policy;
- simple stage heuristics;
- learned stage policy only after heuristic headroom.

Charge context transfer and switching overhead consistently.

## Stage-0 Analysis

### Trace viability

Run exact spec gates. If insufficient, produce a telemetry gap report and stop.

### Value concentration

Where counterfactual evidence exists, estimate strong-vs-cheap marginal value by stage/state. Where it does not, label findings `associational` and use them only to propose heuristic shadow tests.

Use hierarchical partial pooling for stage/task rescue rates if sample sizes differ strongly; avoid tiny-stage raw percentages.

### Heuristic policies

Freeze <=5 interpretable rules based on pre-analysis evidence. Example rules should include cooldown/hysteresis to avoid tier thrashing.

Evaluate by replay when paired outcomes permit; otherwise shadow the policy decision without changing execution and collect identified evidence before causal promotion.

## Learned Policy

Conditional on heuristic materiality:

- start with regularized logistic/GBDT classifier for incremental strong value;
- target stage-level rescue/utility, not final mission success alone;
- incorporate mission-state history summary;
- use OPE/DR if 101-like propensity logs exist;
- compare directly to best heuristic.

## Statistics

- mission is the resampling unit for bootstrap, not individual steps;
- report task-family and mission-length strata;
- report policy switch counts and strong-call contribution;
- avoid treating correlated steps as independent observations;
- use temporal holdout if trace volume supports it.

## Cost Plan

- Stage-0 trace inventory/heuristic replay: $0.
- No duplicate model executions authorized by this plan.
- If paired counterfactual coverage is missing, quantify the smallest safe shadow-dual/randomized stage sample needed and request it via a separate prereg, preferably integrated with 101 telemetry.

## Kill Logic

- insufficient trace data => `TRACE_DATA_INSUFFICIENT`, not speculative model training;
- no stage value concentration => kill learned stage router;
- heuristic cannot beat fixed mission model => kill complexity;
- learned policy does not beat heuristic => keep heuristic;
- switching overhead erases savings => simplify/cooldown or kill;
- benefit exists only on one narrow mission type => label domain-specific rather than global.

## Deliverables

- trace schema/quality report;
- stage-value table with causal-vs-associational labels;
- heuristic prereg + results;
- optional learned-policy results;
- mission-level frontier;
- status `TRACE_DATA_INSUFFICIENT | KILLED | HEURISTIC_PASS | LEARNED_PASS | QUALIFIED_AGENTIC`.