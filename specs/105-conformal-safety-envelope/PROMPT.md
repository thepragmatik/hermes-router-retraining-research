# Agent Prompt — Execute Idea 105: Conformal Safety Envelope

Implement **Idea 105 — Conformal Safety Envelope** from `research/router-innovation-2026-09-08`.

Read the constitution, then this folder's `spec.md`, `plan.md`, `tasks.md` and the documentation for V1/any already-qualified candidate score.

## Objective

Find out how much traffic can be routed cheaply while controlling a frozen, explicitly defined risk—without pretending the wrapper makes the underlying score smarter.

## Rules

- Use a dedicated calibration split; never train/tune the candidate score on calibration rows.
- Freeze the risk event, α, δ and split before evaluation.
- Start with V1 and a simple finite-sample nested-threshold method.
- If no threshold is safe, return `NO_SAFE_COVERAGE`; do not relax α after seeing results.
- Report coverage, held-out risk, bound, cost saving and frontier-call change.
- Formal guarantees are conditional on stated assumptions; do not claim them under arbitrary distribution shift.
- Test coarse stratification only after the global method and remove it if it does not pay.
- Default spend is $0; no paid calls are authorized.
- RouterBench test remains sealed.

Complete all applicable tasks and end with:

`KILLED | V1_SAFE_SLICE | CANDIDATE_SAFE_SLICE | QUALIFIED_WRAPPER`

Begin with `results/105/PREREG.md` and the exact risk definition.