# Implementation Plan: Bayesian Semantic Performance Memory

## Goal

Test semantics as a retrieval-and-uncertainty mechanism over **measured model outcomes**, with shrinkage for sparse neighborhoods.

## Constitution Check

- no cluster→fixed-model rerun;
- train-only Stage 0 and sealed test;
- external data separated by fidelity/pair;
- local-only control mandatory;
- uncertainty/support explicit;
- V1/simple priors mandatory controls;
- $0 first.

## Suggested Layout

```text
experiments/103/
  memory_index.py
  capability.py
  posterior.py
  evaluate.py
  perturb.py
results/103/
  PREREG.md
  stage0_report.md
  retrieval_diagnostics.json
  frontier.csv
```

Reuse frozen BGE embeddings first. Do not swap embeddings until the retrieval formulation itself is tested.

## Retrieval Design

### Baseline coordinate

Start with the existing BGE-small embedding to isolate the mechanism change from representation change. Build train-only nearest-neighbor indices.

### Optional capability decomposition

After the plain semantic-memory baseline is frozen, add a small structured representation such as task family, expected output type, tool/code/math/retrieval need, and context-length bucket. Prefer deterministic metadata where available. If LLM extraction is required, run a stability audit on repeated/paraphrased prompts before using it.

## Posterior Estimation

Implement three levels:

1. **Global prior** per model/pair.
2. **Task-family prior** with empirical-Bayes shrinkage to global.
3. **Local posterior** combining similarity-weighted outcome pseudo-counts with task prior.

For each query/model pair report:

- posterior mean;
- credible/uncertainty interval or bootstrap interval;
- `n_eff`;
- max/median neighbor distance;
- provenance composition;
- OOD/support flag.

A simple Beta-Binomial weighted pseudo-count implementation is preferred initially. For continuous quality, use weighted mean/variance with hierarchical ridge/shrinkage; do not jump to Bayesian neural networks.

## Hyperparameters

Freeze a small train-CV grid for:

- `k` (e.g. 8, 16, 32, 64);
- similarity temperature/decay;
- prior strength;
- support threshold.

Select on calibration/routing utility using development folds only. Do not tune on historical validation.

## Evaluation

### Probabilistic

- Brier/log loss for success probability;
- calibration curves;
- pairwise marginal-gain ranking;
- error vs `n_eff`/distance.

### Routing

Construct a simple cost-aware policy from posterior expected marginal gain. Compare with:

- global prior;
- task prior;
- raw kNN;
- V1/base.

The policy is diagnostic; this spec can qualify as a useful evidence feature even if 102 later makes the final policy.

### Robustness

Create semantic-preserving perturbations/paraphrases from existing train prompts without using sealed data. Measure:

- neighbor-set Jaccard overlap;
- posterior delta;
- route flip;
- whether unstable cases show reduced support.

Also test distractor prefixes/suffixes and formatting changes for adversarial cost manipulation.

## External Data

Use external routing matrices only after local Stage 0. Keep separate memory namespaces or provenance-aware priors. Compare:

- local-only;
- external-only diagnostic;
- local + external prior;
- local + external raw pooled (expected risky control).

External data survives only if it improves local held-out behavior at matched local-label budget.

## Cost Plan

- local embeddings/outcomes: $0;
- reuse cached embeddings when possible;
- capability labels: deterministic first; no paid LLM labeling by default;
- public data download/compute only when local mechanism passes.

## Kill / Rollback

- If retrieval adds no held-out value, kill; do not search many embedding models.
- If raw kNN wins and shrinkage adds no benefit, simplify to raw memory.
- If capability decomposition hurts or is unstable, remove it.
- If OOD/support does not correlate with error, do not use it as a safety signal.

## Deliverables

- memory/index code;
- posterior/shrinkage code;
- retrieval provenance schema;
- Stage-0 report with controls and perturbations;
- optional external robustness report;
- outcome `KILLED | KNN_ONLY | SEMANTIC_MEMORY_PASS | QUALIFIED_FEATURE`.