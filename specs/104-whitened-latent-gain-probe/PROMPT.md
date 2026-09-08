# Agent Prompt — Execute Idea 104: Whitened Latent Marginal-Gain Probe

Implement **Idea 104 — Whitened Latent Marginal-Gain Probe** from branch `research/router-innovation-2026-09-08`.

Read the constitution, then this folder's `spec.md`, `plan.md`, `tasks.md`, and `results/P3_INTERNAL_CONFIDENCE.md`.

## Objective

Test the genuinely untested information source from the prior mission: true hidden-state/logit representations from the cheap/local model, targeting **marginal escalation value**, with PCA whitening as a low-cost geometric correction.

## Rules

- This is not a rerun of P3 response-shape features.
- Confirm hidden states/logits are actually accessible before building anything else.
- Default spend is $0; no paid labels/calls are authorized.
- Freeze model revision, tokenizer/template, layers and token summaries before extraction.
- Fit PCA/whitening only inside training folds.
- Use linear/ridge/logistic probes before any nonlinear model.
- Compare prompt BGE, logit-only, raw, PCA and whitened variants.
- Select by end-to-end routing economics, not AUROC alone.
- If raw/PCA wins, keep it and kill whitening.
- If representation extraction makes serving materially slower, count that cost and kill runtime use if necessary.
- RouterBench test remains sealed.

Complete the package tasks and end with exactly one status:

`KILLED | REPRESENTATION_BLOCKED | RAW_OR_PCA_PASS | WHITENED_PASS | QUALIFIED_FEATURE`

Begin with feasibility and `results/104/PREREG.md`; do not start by training a deep probe.