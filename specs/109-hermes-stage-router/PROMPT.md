# Agent Prompt — Execute Idea 109: Hermes Stage-Aware Agent Router

Implement **Idea 109 — Hermes Stage-Aware Agent Router** from branch `research/router-innovation-2026-09-08`.

Read the constitution and this folder's `spec.md`, `plan.md`, `tasks.md`, then inspect available Hermes mission trace documentation/data.

## Objective

Test whether strong intelligence is valuable at particular **workflow stages/states**, allowing routine agent work to stay cheap while planning/recovery/review escalates when evidence supports it.

## Rules

- First audit trace quality. If data are insufficient, stop with a telemetry contract; do not invent stage outcomes.
- Primary metric is accepted mission success/quality at total mission cost, including retries and switching overhead.
- Distinguish causal/paired/randomized evidence from association.
- Start with transparent stage heuristics. Do not train a learned stage router unless heuristics show material headroom.
- If a learned model does not beat the best heuristic, keep the heuristic.
- Bootstrap by mission, not individual correlated steps.
- Add cooldown/hysteresis to prevent tier thrashing.
- No paid duplicate model runs are authorized by this prompt.
- RouterBench is not the qualification set for this idea.

Complete tasks and end with:

`TRACE_DATA_INSUFFICIENT | KILLED | HEURISTIC_PASS | LEARNED_PASS | QUALIFIED_AGENTIC`

Begin with the trace inventory and `results/109/PREREG.md`.