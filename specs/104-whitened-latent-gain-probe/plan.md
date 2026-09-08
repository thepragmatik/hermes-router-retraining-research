# Implementation Plan: Whitened Latent Marginal-Gain Probe

## Goal

Prove or falsify whether true local-model internals contain useful, cheap signal for escalation value, and whether whitening makes that signal easier to exploit with a tiny probe.

## Constitution Check

- materially new information source versus failed P3;
- test split sealed;
- train-only representation selection;
- linear probe before nonlinear complexity;
- end-to-end economics decide promotion;
- model/version drift explicitly invalidates probe.

## Suggested Layout

```text
experiments/104/
  capture_latents.py
  summarize_latents.py
  fit_probe.py
  evaluate_probe.py
  runtime_bench.py
results/104/
  PREREG.md
  separability.json
  stage0_report.md
  runtime_report.md
artifacts/104/
  pca.npz
  probe.*
  metadata.json
```

## Data Strategy

Stage 0 must avoid expensive paired generation if existing train/public outcomes can be joined to prompts that can be run through an accessible local model for representations. The representation model and the historical outcome model need not be identical only if the spec is explicitly reframed as a representation-transfer test; preferred path is the same cheap model intended for routing.

If paired comparator outcomes are missing, use a small existing public matrix before authorizing new remote labels.

## Capture

Freeze before extraction:

- model id/revision/quantization;
- tokenizer/chat template;
- candidate layers (max 3);
- token positions/summaries;
- generation settings if generated-token states are required;
- dimensionality grid;
- target pair/outcome definition.

Stream compact float16/float32 summaries. Do not retain full activations unless a measured need appears.

## Probe Matrix

Controls:

1. prompt BGE baseline;
2. response-shape/logit summaries;
3. raw hidden summary;
4. PCA hidden summary;
5. whitened PCA summary;
6. optional prompt + winning latent summary.

Use regularized linear/logistic/ridge models with nested/train-only CV for regularization.

## Leakage Controls

- fit scaler/PCA/whitening per training fold;
- ensure target/correctness/action labels never enter representation capture;
- hash row ids before joining features/outcomes;
- add a label-shuffle test that must collapse to chance;
- test task-only baseline to quantify task-identity leakage.

## Statistics

- 5- or 10-fold train-only CV with >=2 seeds if stochastic generation is involved;
- paired bootstrap on held-out policy deltas;
- report family-level metrics, calibration and error overlap;
- compare confidence intervals of raw vs whitened variants;
- historical validation only for one preregistered finalist.

## Runtime Path

Prefer extracting summaries from the same forward/generation call already performed by the cheap model. If serving API cannot expose states, test an in-process/local serving path before redesigning infrastructure.

Runtime benchmark should separate:

- base generation;
- latent summary extraction;
- PCA transform;
- probe inference;
- logging/serialization.

## Cost Plan

- Representation extraction from local model: $0 API spend; record compute time.
- No paid strong labels until Stage-0 separability is promising and missing labels are the only blocker.
- If new paired labels are required, first perform a power/sample-size calculation and request a separate operator cap.

## Kill Logic

- no latent improvement over prompt/logit controls => kill;
- hidden states help but whitening hurts => promote raw/PCA, kill whitening only;
- signal only reflects task id and vanishes within task => kill as general router feature, optionally retain task-specific diagnostic;
- runtime overhead dominates savings => kill runtime use even if classifier metric improves;
- serving stack cannot expose states cheaply => mark `REPRESENTATION_BLOCKED`, not a model failure.

## Deliverables

- capture/probe code and leakage tests;
- frozen transform/probe metadata;
- Stage-0 separability + policy report;
- runtime benchmark;
- status `KILLED | REPRESENTATION_BLOCKED | RAW_OR_PCA_PASS | WHITENED_PASS | QUALIFIED_FEATURE`.