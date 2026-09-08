# Implementation Plan: Diversity-Optimized Model Portfolio

## Goal

Identify whether selecting a small, complementary, current model pool is a larger lever than another router architecture change.

## Constitution Check

- selection from measured outcome matrices;
- no indiscriminate model growth;
- current prices/availability refreshed;
- oracle complementarity separated from realizable routing;
- V1/historical pool only compared on compatible data;
- $0/public-data first;
- test split sealed.

## Suggested Layout

```text
experiments/107/
  load_matrices.py
  eligibility.py
  complementarity.py
  select_portfolio.py
  realizability.py
results/107/
  PREREG.md
  model_snapshot.json
  complementarity.csv
  portfolio_frontier.csv
  stage0_report.md
```

## Data Sources

Preferred Stage-0 order:

1. local train-safe historical matrix for method sanity;
2. RoutingCompendium/LLMRouterBench or other pre-collected current-ish routing matrices;
3. real 101 outcomes when enough current models have shared traffic coverage.

Do not buy a broad new evaluation matrix before public/stored data demonstrates that portfolio selection itself produces useful structure.

## Current Model Snapshot

At execution time record:

- canonical model id/revision;
- provider;
- input/output/cache pricing;
- context limit;
- tool/structured-output support;
- privacy/ZDR suitability;
- availability date/source.

Filter ineligible models before optimization.

## Objective and Search

Freeze at least two interpretable objectives:

- quality coverage under pool-size constraint;
- cost-adjusted coverage or minimum cost at target oracle quality.

For small candidate pools brute-force all subsets of size <=3. Implement greedy selection and verify it against brute force. For larger pools use cost-aware lazy greedy and validate on a reduced candidate subset.

## Realizability Test

A selected pool must be tested with a cheap router proxy using only runtime-visible signals. Preferred order:

1. simple per-task best-model policy where task id is legitimately known;
2. 103 semantic performance memory if available;
3. simple pairwise regularized router with the same feature budget as V1;
4. 102 causal policy when identified data exists.

Do not use oracle correctness to claim deployability.

## Stability / Sensitivity

- bootstrap rows/task families;
- vary cost assumptions within plausible current price ranges;
- leave one task family out;
- test model removal/revision;
- report how often the selected set changes.

A portfolio that changes completely under tiny price noise is operationally fragile and should be simplified.

## Cost Plan

- public/stored matrices: $0 API spend;
- model price lookup: $0 public data;
- new shared evaluation calls only after an upper-bound/power calculation shows the exact missing matrix entries and operator approves a small cap.

## Kill Logic

- no <=3 model pool materially beats best single/reference => kill portfolio complexity;
- selected extra models add < marginal gate => remove them;
- oracle gain exists but simple routing cannot capture >=35% => `ORACLE_ONLY_PORTFOLIO`;
- public result fails on local/current distribution => treat as transfer evidence only;
- provider/privacy constraints eliminate a model => recompute selection, never silently substitute.

## Deliverables

- current model snapshot;
- complementarity matrix;
- greedy vs brute-force validation;
- portfolio frontier and stability report;
- realizability report;
- status `KILLED | SINGLE_MODEL_PIVOT | ORACLE_ONLY_PORTFOLIO | PORTFOLIO_PASS | QUALIFIED_POOL`.