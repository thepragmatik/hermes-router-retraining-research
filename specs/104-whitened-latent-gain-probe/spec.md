# Feature Specification: Whitened Latent Marginal-Gain Probe

**Feature Branch:** `104-whitened-latent-gain-probe`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation

## Problem

The project's earlier “answer-aware confidence” experiment did **not** test true model internals: RouterBench stored text responses but no hidden states or token log-probabilities. That means a materially different information source remains untested.

This idea extracts frozen hidden-state/logit features from the actual cheap/local model and tests whether a small, whitened linear probe can predict **marginal benefit of escalation** better than prompt embeddings or response-shape features.

The key research hypothesis is that latent representations contain useful functional uncertainty but are highly anisotropic. PCA whitening or related covariance normalization may make a simple probe more effective than a larger head on raw embeddings.

## User Stories

### Story 1 — Prove latent separability cheaply

As a researcher, I want to determine whether hidden-state features contain out-of-fold signal about model marginal gain before spending effort on a full runtime router.

### Story 2 — Compare raw vs whitened representations

As an operator, I want evidence that whitening/low-dimensional geometry adds value beyond ordinary prompt embeddings, response length/log-prob summaries, and raw hidden states.

### Story 3 — Keep runtime overhead small

If the signal exists, I want a probe that reuses an already-running local model forward pass and adds negligible memory/latency.

### Story 4 — Know when the signal is task-specific

The system must identify task families where latent confidence is uninformative or miscalibrated rather than forcing one global probe.

## Requirements

- **FR-001:** Stage 0 MUST use true hidden-state/logit outputs from an accessible local/cheap model; stored-response shape features do not count as this experiment.
- **FR-002:** Target SHOULD be pairwise marginal quality gain or escalation utility. Weak correctness may be reported only as a diagnostic.
- **FR-003:** Compare raw hidden features, PCA-reduced features, PCA-whitened features, prompt embedding baseline, and simple logit/entropy summaries where available.
- **FR-004:** Fit linear/logistic/ridge probes first. A nonlinear MLP is forbidden until linear/whitened signal passes Stage 0.
- **FR-005:** PCA/whitening MUST be fit only on training folds; no holdout leakage.
- **FR-006:** Layer/token selection MUST use a small frozen candidate set, not an exhaustive post-hoc search.
- **FR-007:** Report dimensionality, explained variance, covariance condition number/an\-isotropy diagnostics and whitening stability.
- **FR-008:** Report task-family performance and drop/abstain for families where the signal is not useful.
- **FR-009:** The final decision is based on end-to-end routing/cost, not AUROC alone.
- **FR-010:** Model revision/tokenizer/template changes MUST invalidate or explicitly recalibrate the probe.
- **FR-011:** RouterBench test remains sealed.

## Representation Contract

Start with a small set of runtime-cheap summaries:

- final prompt token hidden state before generation;
- final generated-token hidden state or mean of last N generated-token states;
- one intermediate layer + final layer, selected a priori;
- token log-prob mean/min/variance, entropy or margin summaries where model API exposes them;
- response-length/termination controls.

Do not store full token-by-layer activations for the whole corpus unless needed; stream summaries to disk to keep cost/storage bounded.

### Whitening

For training matrix `H`, fit PCA on train fold only. Evaluate:

1. raw standardized H;
2. PCA projection retaining a frozen variance fraction or dimensions grid (e.g. 16/32/64);
3. whitened PCA `Z = (H-μ) V Λ^{-1/2}` with eigenvalue floor.

Regularize tiny eigenvalues; record floor. Whitening transform is part of the probe version.

## Stage 0 — Cheapest Falsification

Use a local model and train-only paired outcome dataset where both cheap and comparator outcomes are known or can be reproduced locally/stored.

The idea survives only if:

- whitened latent probe improves pairwise-gain AUPRC/AUROC over prompt-embedding and logit-only baselines by at least **0.03 absolute** on the primary metric in >=8/10 folds/seeds, **or** produces a program-material end-to-end frontier gain despite smaller classifier delta;
- the gain survives task-stratified analysis and is not entirely one tiny family;
- a simple cost-aware policy using the probe achieves >= **0.5pp quality gain at matched cost** or >= **3% relative cost reduction at matched quality** on the train-derived holdout, or captures >=35% of a relevant oracle uplift under the same action pair;
- whitening is at least as stable as raw latent features across seeds and model-batch order.

If hidden states help but whitening does not, keep the simpler raw/PCA probe. If only prompt embedding wins, kill the latent idea.

## Stage 1 — Runtime Feasibility

Measure incremental overhead when the cheap model is already being run:

- feature extraction p50/p95;
- extra memory;
- serialization/storage if logging;
- probe latency.

Target: probe + summary extraction adds < **5%** to local-model wall-clock latency or < **10 ms** per request, whichever is more realistic for the environment; if not, calculate whether quality/cost savings still justify it.

## Failure Modes

- model internals unavailable from serving stack;
- hidden representation changes with quantization/template/revision;
- whitening amplifies low-variance noise;
- probe learns length/task identity instead of gain;
- target labels are stochastic single draws;
- latent signal works on factual tasks but not math/code;
- runtime extraction forces a slower serving path.

## Expected Benefit

If successful, this provides a genuinely new answer-aware signal that exists before a second expensive model call and could capture uncertainty invisible to prompt embeddings.

## Stackability / Exclusivity

- Can feed 102 as a feature/nuisance signal, 105 for calibrated abstention, or 106 as an evidence state.
- Must be compared against 103 semantic memory for overlap; do not keep both if decisions are redundant.
- Raw, PCA and whitened representations are mutually exclusive promoted variants; retain the simplest winner.
- A high-capacity nonlinear latent router is explicitly deferred until this low-cost probe demonstrates legs.