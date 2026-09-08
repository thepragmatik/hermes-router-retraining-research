# Implementation Plan: Conformal Safety Envelope

## Goal

Determine whether a candidate router score can support useful **selective cheap coverage at controlled risk** without retraining the score.

## Constitution Check

- separate calibration split;
- assumptions stated explicitly;
- no claim under arbitrary drift;
- V1 control required;
- risk/coverage/economics, not only calibration metric;
- $0 train-only Stage 0;
- fail to conservative route when no safe threshold exists.

## Suggested Layout

```text
experiments/105/
  risk_definition.py
  calibrate.py
  evaluate.py
  drift.py
results/105/
  PREREG.md
  stage0_report.md
  coverage_risk.csv
```

## Data Protocol

For each deterministic fold:

- `fit`: score/model fitting where needed;
- `calibration`: threshold/risk control only;
- `evaluation`: untouched until threshold frozen.

Do not reuse calibration rows to select candidate score architecture or hyperparameters.

## Candidate Scores

Minimum:

1. V1 score;
2. strongest simple score already available from current branch;
3. 103/104/102 score only if those ideas pass independently.

No need to implement a new router inside this feature.

## Risk-Control Procedure

First implementation should use nested threshold sets and a one-sided finite-sample bound. Example:

1. define cheap-safety score `s(x)` where larger = safer;
2. enumerate frozen score thresholds derived from calibration ordering;
3. for each acceptance set compute observed failures `k/n`;
4. compute one-sided `(1-δ)` upper confidence bound for risk using exact binomial/Clopper-Pearson or the selected conformal risk-control bound;
5. select the largest coverage threshold whose upper bound <= target `α`.

Freeze `α`, `δ`, minimum calibration size and stratum rules in preregistration.

## Stratification

Test only after global baseline:

- coarse task family;
- maybe risk class or traffic type;
- minimum calibration sample per stratum.

If a stratum is too small, back off to global. Avoid many semantic micro-buckets.

## Drift Tests

Construct train-only synthetic shifts:

- task mix reweighting;
- score-distribution shift;
- paraphrase/format perturbations;
- OOD prompt subset;
- model-score perturbation/revision simulation.

The system should flag/reduce coverage when assumptions become implausible. Do not claim formal validity for the detector itself.

## Statistics

- at least 10 deterministic fold/seed replicates;
- report coverage distribution, held-out risk, upper bound, calibration size;
- paired bootstrap economic deltas where applicable;
- report target-risk violations individually, not averaged away.

## Cost Plan

Stage 0 is $0. Runtime cost is negligible score thresholding plus any support/drift feature already computed. If 103 support is required, count its cost separately rather than hiding it in 105.

## Kill Logic

- `NO_SAFE_COVERAGE` at all useful α => kill for that score;
- safe coverage <5–10% with trivial savings => kill operational use;
- risk violations systematic across folds => kill/revise guarantee, not threshold-search on holdout;
- stratification adds no coverage => keep global only;
- drift detector adds noise => remove it, retain conservative version invalidation rules.

## Deliverables

- calibration/evaluation code;
- explicit risk-definition module/documentation;
- risk/coverage curves;
- drift stress report;
- status `KILLED | V1_SAFE_SLICE | CANDIDATE_SAFE_SLICE | QUALIFIED_WRAPPER`.