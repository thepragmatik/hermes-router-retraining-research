# Feature Specification: Bayesian Semantic Performance Memory

**Feature Branch:** `103-bayesian-semantic-memory`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** historical/public measured outcomes for Stage 0; Idea 101 improves current-traffic memory.

## Problem

The project already falsified semantic-cluster routing. That failure does not rule out semantics as an **evidence retrieval coordinate system**. This feature retrieves similar *measured historical outcomes*, estimates local model success/marginal gain, and uses hierarchical Bayesian shrinkage so sparse neighborhoods do not produce overconfident routes.

The output is not `cluster_id -> model`. It is a posterior such as:

- local success probability by model;
- local strong-over-cheap rescue probability;
- uncertainty interval;
- effective neighborhood support;
- OOD/support score.

Low-support requests back off toward task/global priors or conservative routing.

## User Stories

### Story 1 — Retrieve relevant measured history

Given a request, retrieve semantically/capability-similar historical rows with measured model outcomes and explain the support used for the estimate.

### Story 2 — Shrink sparse neighborhoods

If only a few neighbors exist, use hierarchical partial pooling rather than raw kNN percentages.

### Story 3 — Remain stable under paraphrase

Semantically equivalent paraphrases should retrieve overlapping evidence and produce similar posterior estimates even when wording changes.

### Story 4 — Abstain OOD

When the request is outside memory support, emit low support and fall back rather than confidently routing from distant neighbors.

## Requirements

- **FR-001:** Semantics MUST retrieve measured outcomes; fixed cluster→model assignment is forbidden.
- **FR-002:** Store provenance for every memory row: dataset/source, model/revision, outcome definition, cost snapshot, timestamp/domain, evidence fidelity.
- **FR-003:** Retrieval MUST expose neighbor ids, distances/similarities, effective sample size, task/capability labels where available.
- **FR-004:** Implement a raw kNN outcome baseline and at least one hierarchical/shrinkage estimator.
- **FR-005:** The primary posterior target should align with routing utility: per-model success and/or model-to-model marginal gain, not semantic class.
- **FR-006:** Sparse local estimates MUST shrink toward a task-family prior and then a global prior.
- **FR-007:** Cross-dataset/model-pair records may be transfer priors but must not silently mix as exact-pair truth.
- **FR-008:** OOD/support diagnostics MUST be explicit and usable as a fallback condition.
- **FR-009:** External data must retain a local-only control at matched local-label budget.
- **FR-010:** Evaluate end-to-end routing/cost as well as probabilistic calibration.
- **FR-011:** Test paraphrase and surface-form robustness.
- **FR-012:** RouterBench test remains sealed.

## Statistical Model

Start with a pragmatic empirical-Bayes model rather than full MCMC.

For binary success of model `m` in task family `g`:

- global prior: `p_m ~ Beta(α0_m, β0_m)`;
- task prior centered on global with learned/effective strength `κ_g`;
- local neighborhood contributes similarity-weighted successes/failures;
- posterior pseudo-counts combine task prior + local weighted evidence.

For marginal gain `D = Q_b - Q_a`, maintain weighted local counts of pair states (`a_only`, `b_only`, `both`, `neither`) or a shrinkage regression on gain.

Similarity weights may use `w_i = exp(-d_i / T)` or rank-decay, with `T/k` selected only on train CV. Report effective sample size `n_eff=(Σw)^2/Σw²`.

Capability decomposition may be added as an explicit structured key/feature if it improves retrieval robustness. Do not use an LLM-generated capability label as truth without measuring stability.

## Stage 0 — Cheapest Falsification

Train-only leave-group-out/CV experiment:

Compare:

1. global prior only;
2. task-family prior only;
3. raw semantic kNN measured outcomes;
4. hierarchical/shrunk semantic memory;
5. historical V1/BGE score as control where applicable.

Gate:

- hierarchical memory must improve held-out log loss/Brier or pairwise gain ranking over raw kNN and task-prior controls on >=8/10 seeds/folds, **and**
- when converted to a routing policy, must achieve >= **0.5pp quality gain at approximately matched cost**, >= **3% relative cost reduction at matched quality**, or another preregistered material gain on the train-derived holdout; **or** materially improve OOD/high-value miss handling without >0.2pp quality loss;
- paraphrase perturbations must not increase route-flip rate by >10pp relative to unperturbed nearest-neighbor uncertainty without a corresponding support drop;
- low-support/OOD rows must show worse calibration/error than high-support rows in the expected direction; otherwise the support measure is not informative.

If raw kNN helps but Bayesian shrinkage does not, keep the simpler kNN memory and mark the Bayesian component killed. If neither helps, kill semantic performance memory rather than changing embeddings repeatedly.

## Data Sources

Priority:

1. local train-safe exact-pair outcomes;
2. 101 real outcomes once available;
3. compatible public routing matrices for robustness/transfer controls;
4. synthetic only as low-fidelity prior, never immediate truth.

## Expected Benefits

- turns real routing history into reusable local evidence;
- naturally adapts to recurring task patterns without global retraining;
- supplies uncertainty/support features to 102/105/106;
- can detect model-pair drift locally;
- preserves semantic routing benefits without repeating failed clustering.

## Stackability / Exclusivity

- Stackable with 101, 102, 105, 106 and 107.
- 104 can be combined only after error-overlap analysis; if both rank the same cases, keep the cheaper one.
- Mutually exclusive with semantic cluster→fixed route as the production mechanism.
- Capability decomposition and plain embedding retrieval are alternative retrieval representations within this spec; promote only the one that wins frozen ablations.