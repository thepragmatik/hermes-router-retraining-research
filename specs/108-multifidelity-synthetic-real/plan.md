# Implementation Plan: Multi-Fidelity Synthetic→Real Fusion

## Goal

Test whether the R7a generator can reduce *real* supervision requirements when treated as low-fidelity evidence and corrected/calibrated by real outcomes.

## Constitution Check

- synthetic never equals real truth;
- matched real-only control always present;
- real held-out evaluation required;
- 101 propensities required for deployment OPE claims;
- generator spend gated and deferred until retrospective transfer passes;
- test split sealed.

## Suggested Layout

```text
experiments/108/
  build_multifidelity.py
  shift_diagnostics.py
  train_direct.py
  fusion.py
  evaluate.py
results/108/
  PREREG.md
  stage0_report.md
  budget_curve.csv
  shift_report.json
```

## Stage-0 Data Design

Build two complementary tests if data permits:

### A. Real generator transfer test

Use existing R7a strict synthetic rows from `feat/generator-pivot-r0` and train-safe real rows. Deduplicate against train/validation according to project policy without touching test contents.

### B. Known-bias simulator

From full-information train rows, create a low-fidelity label process with controlled corruption/domain skew. This validates that fusion code can benefit from useful low-fidelity signal but reject/downweight harmful signal.

## Real-Label Budget Protocol

Freeze the exact real row samples/seeds for each budget (e.g. 0.5/1/2/5/10%). Every arm at a budget gets the *same real rows*.

Arms:

1. real-only direct model;
2. synthetic-only diagnostic;
3. synthetic pretrain → real update;
4. weighted joint model;
5. synthetic-assisted direct model + real DR correction if compatible propensity simulation is used.

Start with small regularized models and existing router features. Do not fine-tune an LLM in Stage 0.

## Synthetic Weighting

Use a tiny frozen grid for `w_syn`, chosen only on train development folds. Consider task/fidelity-specific weights only after global weighting shows value.

If a hierarchical prior is used, freeze prior strength similarly.

## Shift Diagnostics

Compute before model fitting:

- task-family proportions;
- embedding distance / nearest-neighbor support;
- label prevalence;
- pair-state prevalence;
- verifier/key-type distributions;
- answer format/length;
- source-specific calibration.

Diagnostics are descriptive at first. Do not dynamically reweight based on qualification outcomes.

## Statistics

- >=10 fixed real-budget samples/seeds where feasible;
- paired comparisons using identical real rows;
- bootstrap policy utility on real held-out rows;
- plot gain vs real-label budget and estimate real-label saving at fixed target;
- report synthetic-only-to-real generalization gap.

## Cost Plan

- Existing R7a rows + real train rows: $0 API spend.
- Stage 0 must pass before generating another 2k synthetic corpus.
- If Stage 0 passes and more synthetic data has expected value, estimate marginal benefit per 1k synthetic labels and request the smallest operator-approved batch.
- Generator cost, manual key audits and maintenance count in refresh economics.

## Real Telemetry Extension

Once 101 data exists:

- separate temporal train/calibration/qualification windows;
- use synthetic data only in direct/nuisance model;
- use real propensity-logged outcomes for correction/evaluation;
- keep a matched real-only DR control.

## Kill Logic

- fusion fails matched real-only control => kill;
- synthetic-only looks good but transfer is poor => kill promotion, retain generator only for test fixtures;
- benefit only at high real budgets and does not pay generator/maintenance cost => kill economic use;
- R7a source proves too narrow => do not broaden generator until a source-diversity hypothesis is preregistered;
- source weighting becomes unstable across seeds => prefer real-only.

## Deliverables

- multi-fidelity dataset/provenance loader;
- shift report;
- real-label budget curves;
- source ablations;
- status `KILLED | LOW_FIDELITY_PRIOR_ONLY | SAMPLE_EFFICIENCY_PASS | QUALIFIED_FUSION`.