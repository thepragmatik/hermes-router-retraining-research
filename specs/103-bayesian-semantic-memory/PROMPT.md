# Agent Prompt — Execute Idea 103: Bayesian Semantic Performance Memory

Implement **Idea 103 — Bayesian Semantic Performance Memory** from branch `research/router-innovation-2026-09-08`.

Read:

1. `.specify/memory/constitution.md`
2. `specs/103-bayesian-semantic-memory/spec.md`
3. `specs/103-bayesian-semantic-memory/plan.md`
4. `specs/103-bayesian-semantic-memory/tasks.md`
5. `experiments/005-semantic-signal-ablation-prereg.md`
6. `research/2026-09-08-innovation-deep-research.md`
7. `research/2026-09-08-adversarial-review.md`

## Objective

Test whether semantics can improve routing by retrieving **measured local outcomes with uncertainty**, not by assigning a model to a semantic cluster.

## Rules

- Do not implement KMeans/cluster→fixed model routing.
- Reuse frozen BGE embeddings first; do not turn this into an embedding bake-off.
- Stage 0 is train-only and $0.
- Implement global prior, task prior, raw kNN and hierarchical/shrunk memory controls.
- Report neighbor provenance, effective support and OOD behavior.
- Low support must back off; it must not extrapolate confidently.
- Preserve local-only controls if external data is introduced.
- Test paraphrase/surface-form robustness and adversarial cost perturbations.
- If raw kNN wins, keep it and delete unnecessary Bayesian machinery.
- If retrieval itself fails, kill the idea rather than searching for progressively larger embeddings.

Complete all applicable tasks and commit measured results. End with exactly one status:

`KILLED | KNN_ONLY | SEMANTIC_MEMORY_PASS | QUALIFIED_FEATURE`

Begin with `results/103/PREREG.md` and the frozen BGE train-only neighbor index.