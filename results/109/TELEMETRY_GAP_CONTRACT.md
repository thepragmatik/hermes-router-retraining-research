# Telemetry Gap Contract — Idea 109 Hermes Stage-Aware Agent Router

**Terminal status: `TRACE_DATA_INSUFFICIENT`** (prereg commit 66b6f26, trace_quality.json commit 613ff8b). All frozen Stage 0A gates (G-A–G-D + constitution IV join-key floor) failed. No policy modeling was run; no stage outcomes invented. This contract states exactly what identified telemetry idea 109 requires before Stage 0B/0C can run. It is a data contract, not authorization to spend.

## What the one existing trace source lacks (measured, 69 rows, sha256 56c7060c…97a8)

The `evidence/shadow/shadow_log.jsonl` schema is 7 flat keys (`prompt_id, decision, confidence, threshold, mode, engine, ts`). Confirmed gaps (consistent with `results/V1_BASELINE_GAPS.md` G1–G5 on `feat/generator-pivot-r0`):

- C1 no mission/step identity: no `mission_id`, `step_id`, parent/previous-step link; `prompt_id` hardcoded 0 → 1 distinct value.
- C2 no stage/state signal: no stage label or raw event features from which the plan's deterministic taxonomy (plan/read/transform/tool/test/recovery/review/final, `unknown` fallback) could be derived.
- C3 no outcome join: no routed answer, correctness, acceptance, or provenance → constitution VI fidelity class undefined; constitution IV: observability, not training data.
- C4 no progress/failure evidence: no tool invoked/result, test/build/lint status, retry/no-progress indicators.
- C5 no cost/latency accumulation: no cumulative tokens/cost/latency, no switch/transfer cost surface.
- C6 no content hash: cannot dedupe or join to prompts (G3).
- C7 no production decision log at all (G2): the only logged rows are CLI-era health/probe traffic on one distinct prompt — volume unrepresentative (G5).

## Required schema (binding for any future 109-eligible trace)

Per step, constitution IV minimum plus spec Trace Contract: `mission_id, step_id, ts, stage_or_event_features, model_action+revision, tool_invoked+result_status, test_build_lint_result, retry_no_progress_indicators, cumulative_tokens_cost_latency, content_hash (privacy-preserving, e.g. prompt_sha256[:12]), logging_propensity (when randomized), outcome_join_status+outcome_provenance, parent_step_link`. Final mission success/acceptance with provenance at mission level. Stage labels must be reproducible from runtime events (FR-008); outcome/provenance fields must distinguish observed factual outcomes from proxy/human/judge/synthetic (FR-006, constitution IV).

## Smallest sufficient collection plan (for operator review; $0 to design, capture cost TBD)

Integrate with idea 101 telemetry rather than a bespoke 109 pipeline (tasks.md Spend; plan: "preferably integrated with 101 telemetry"):

1. Close C1/C6/C7 first (101's fix directions): service-side logging parity with the CLI, real `prompt_id`/`session_id`/`message_id`, `prompt_sha256[:12]` — no text stored (PII surface rule).
2. Add C2/C4/C5 runtime event features: stage-derivable events, tool/test/retry status, cumulative tokens/cost. Capture on the shadow service decision path (identified, joinable by construction).
3. Outcome join (C3): mission acceptance + routed answer correctness on a sampled subset — a separate capture pipeline per the gap memo; smallest preregistered dual-evaluation sentinel share sized later against 101's rate/cap rules (bounded, propensities recorded, low-risk strata only).
4. Volume gate to re-audit against (frozen, spec 0A verbatim): >= 100 completed missions or >= 500 stage decisions across >= 3 mission/task types; >= 95% step feature coverage; >= 80% mission outcome coverage or provenance'd proxy; sufficient retry/tool/test logging. Re-run this same preregistered audit on the new surface — gates are not re-derived.

## Non-decisions recorded

Stage 0B (value concentration), 0C (heuristic prereg/scoring), and Phases 1–5 were NOT run — spec/tasks forbid policy modeling on failed Stage 0A. Idea 109 is not killed; it is BLOCKED on identified telemetry. `KILLED` would have required the policy phases to run and show no headroom.
