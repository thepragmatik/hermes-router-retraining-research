# Agent Prompt — Execute Idea 102: Doubly Robust Uplift Router

You are implementing **Idea 102 — Doubly Robust Uplift Router** in `thepragmatik/hermes-router-retraining-research`.

Start from branch `research/router-innovation-2026-09-08`; use feature branch `102-doubly-robust-uplift-router` if you are allowed to create one.

Read:

1. `.specify/memory/constitution.md`
2. `specs/102-doubly-robust-uplift-router/spec.md`
3. `specs/102-doubly-robust-uplift-router/plan.md`
4. `specs/102-doubly-robust-uplift-router/tasks.md`
5. `results/P1_CHEAP_SAMPLING.md`, `results/P3_INTERNAL_CONFIDENCE.md`, `results/P5_THREE_TIER.md`
6. Idea 101 spec/contracts

## Objective

Determine whether routing improves when the learned quantity is **incremental model value** rather than generic difficulty/correctness, using propensity-aware doubly robust estimation.

Do not re-run failed FEV/sparse-label supervision under a new name. The identifying difference here is known randomized logging propensities, cross-fitting, overlap diagnostics, and causal/DR correction.

## Execution rules

- Run the train-only simulated-logging Stage 0 before touching real traffic.
- Default spend is $0; this prompt authorizes no paid calls.
- RouterBench test remains sealed.
- Use V1, always-action, direct correctness and simple outcome-difference controls.
- Start with binary routing and simple regularized nuisance models.
- Never estimate propensities when exact logging propensities are available.
- Refuse unsupported regions; do not extrapolate.
- Sweep a frozen cost λ grid and report the whole Pareto frontier.
- One preregistered diagnostic correction maximum after Stage-0 failure.

Complete `tasks.md`, commit code/tests/results, and finish with exactly one status:

`KILLED | NEEDS_101_COVERAGE | STAGE0_PASS | QUALIFIED`

If 101 real telemetry is not yet available, complete Stage 0 fully and stop at the correct dependency status rather than fabricating a real-data result.

Begin by writing `results/102/PREREG.md` and constructing the simulated propensity logs.