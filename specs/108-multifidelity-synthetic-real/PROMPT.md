# Agent Prompt — Execute Idea 108: Multi-Fidelity Synthetic→Real Fusion

Implement **Idea 108 — Multi-Fidelity Synthetic→Real Fusion** from `research/router-innovation-2026-09-08`.

Read the constitution; this folder's `spec.md`, `plan.md`, `tasks.md`; `GENERATOR_PREREG.md` on the generator branch; the branch evidence map; and Idea 101/102 contracts.

## Objective

Find out whether the R7a generator can **reduce real-label requirements** when treated as low-fidelity evidence, while real outcomes remain authoritative.

## Rules

- Synthetic labels are never ground truth for promotion.
- Preserve provenance/fidelity in schema and training code.
- Always compare to a real-only control using the exact same real rows.
- Stage 0 uses existing data and $0 spend; do not scale the generator first.
- Qualification is on real held-out outcomes only.
- Synthetic data may shape the direct/outcome model; propensity correction/value must come from real logged outcomes.
- If fusion hurts real performance, kill it regardless of synthetic metrics.
- If R7a only helps as a weak prior, record that rather than promoting a synthetic router.
- No new generation/API spend is authorized.
- RouterBench test remains sealed.

Complete tasks and end with:

`KILLED | LOW_FIDELITY_PRIOR_ONLY | SAMPLE_EFFICIENCY_PASS | QUALIFIED_FUSION`

Begin with provenance validation, shift diagnostics and `results/108/PREREG.md`.