# Agent Prompt — Execute Idea 107: Diversity-Optimized Model Portfolio

Implement **Idea 107 — Diversity-Optimized Model Portfolio** from branch `research/router-innovation-2026-09-08`.

Read the constitution, then this folder's `spec.md`, `plan.md`, `tasks.md`, plus `results/P0_MODEL_POOL.md`, `results/P5_THREE_TIER.md`, and `DATASETS.md`.

## Objective

Determine whether we are solving the wrong routing problem because the model pool is poorly chosen. Select the **smallest complementary current pool**, not the highest-scoring collection of models.

## Rules

- Refresh current ids/prices/provider/privacy constraints at execution time.
- Use stored/public outcome matrices before buying new evaluations.
- Compute unique rescue/co-failure, not only aggregate accuracy.
- Default promoted pool size <=3.
- Verify greedy selection against brute force when feasible.
- Oracle portfolio quality is only headroom; run a simple realizability test before promotion.
- If one current inexpensive model dominates, recommend a single-model pivot rather than preserving routing for its own sake.
- If oracle diversity is unreachable by simple routing, label it honestly and stop.
- Any changed model pool invalidates old router thresholds and requires recalibration downstream.
- RouterBench test remains sealed; no paid calls are authorized.

Complete all tasks and end with:

`KILLED | SINGLE_MODEL_PIVOT | ORACLE_ONLY_PORTFOLIO | PORTFOLIO_PASS | QUALIFIED_POOL`

Begin with the current model snapshot and `results/107/PREREG.md`.