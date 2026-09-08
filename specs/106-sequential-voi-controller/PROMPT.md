# Agent Prompt — Execute Idea 106: Sequential Value-of-Information Controller

Implement **Idea 106 — Sequential Value-of-Information Controller** from branch `research/router-innovation-2026-09-08`.

Read the constitution and this folder's `spec.md`, `plan.md`, `tasks.md`, then inspect only the already-qualified candidate actions/signals.

## Objective

Test whether an adaptive controller can save more than a fixed cascade by buying only the **next piece of evidence with positive expected value**.

## Hard rules

- Do not start with reinforcement learning, bandits or a POMDP.
- Stage 0 is a $0 hidden-counterfactual replay with at most three dynamic actions.
- Every action must have independent evidence before entering the controller.
- The policy must not see evaluator-only future/counterfactual correctness.
- Compare to the best fixed cascade with identical action costs.
- If myopic VOI fails, stop. Do not rescue the idea with deeper learning.
- If myopic collapses to a fixed sequence, use the fixed sequence and remove controller complexity.
- Respect 105 safety constraints if configured.
- RouterBench test remains sealed; no paid calls are authorized.

Complete `tasks.md` and end with exactly one status:

`KILLED | FIXED_POLICY_WINS | MYOPIC_PASS | DEPTH2_PASS | QUALIFIED_CONTROLLER`

Begin by inventorying which actions have enough evidence to be eligible and freezing `results/106/PREREG.md`.