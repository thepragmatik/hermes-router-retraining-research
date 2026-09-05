# Experiment 004 preregistration: one-sided judge labels / PU learning

**Spend:** $0  
**Purpose:** exploit the observed asymmetry of the existing judge rather than training on its false negatives as if they were clean labels.

## Empirical premise

From mission-provided aggregate rates, the existing judge labels imply approximately:

- precision(`judge says needs strong`) = **96.0%**;
- NPV(`judge says weak sufficient`) = **58.5%**.

See [`../evidence/judge-noise-derived-analysis.md`](../evidence/judge-noise-derived-analysis.md).

Therefore judge-positive rows are a plausible high-precision positive set, while judge-negative rows should be treated as **unlabeled** unless independently verified.

## Candidates

All use the existing v1 prompt embeddings and CPU-scale heads.

1. failed-v2 hard-label baseline (read-only reference; do not rerun if its recorded metrics are sufficient);
2. high-precision positive + unlabeled, simple weighted semi-supervised objective;
3. non-negative PU risk estimator using a train-only class-prior estimate;
4. task-stratified PU / propensity-adjusted variant with hierarchical shrinkage;
5. PU + deterministic `WEAK_CONFIRMED` negatives where a task-native verifier can certify weak correctness.

Reference for nnPU: [Kiryo et al., NeurIPS 2017](https://papers.nips.cc/paper/2017/hash/7cce53cf90577442771720a370c3c723-Abstract.html).

## Safeguards

- Do not assume SCAR: judge-positive selection is likely instance-dependent.
- Do not use the validation set to tune class priors or confidence cutoffs.
- Report task-wise positive coverage and contamination estimates.
- Keep a plain soft-posterior baseline; a complicated PU loss must beat it to justify itself.

## Gates

- viability: val APGR >= 0.55;
- useful rescue: >=0.60;
- replacement: >=0.6459.

A method that only improves classification accuracy but not APGR does not pass.
