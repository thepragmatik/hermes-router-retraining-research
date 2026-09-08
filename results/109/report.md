# Report — Idea 109 Hermes Stage-Aware Agent Router — Stage 0A Trace Viability Check

## Terminal status

**`TRACE_DATA_INSUFFICIENT`**

This is the spec-defined SUCCESS for Stage 0A (spec tasks T004: "If trace gates fail, write an exact telemetry gap contract and mark `TRACE_DATA_INSUFFICIENT`; stop policy modeling"). Idea 109 is BLOCKED on identified telemetry, not KILLED — `KILLED` requires the policy phases to run and show no headroom, and spec/tasks forbid policy modeling after failed Stage 0A gates.

## What was run

- Read authority files in mandated order: `.specify/memory/constitution.md`, `specs/109-hermes-stage-router/spec.md`, `plan.md`, `tasks.md`, `PROMPT.md` (verbatim, in-worktree).
- Preregistered the audit BEFORE the verdict: `results/109/PREREG.md` froze the trace-source inventory, schema/outcome-fidelity definitions, spec Stage 0A gates verbatim, decision rule, baselines, and bootstrap unit (commit 66b6f26).
- Audited the single known trace source against the frozen gates; inventoried and ruled out other candidate surfaces; wrote `results/109/trace_quality.json` (commit 613ff8b).
- Wrote the telemetry-gap contract `results/109/TELEMETRY_GAP_CONTRACT.md` (commit 2adf4c0).

## Audit result (frozen gates)

| Gate | Requirement | Measured | Verdict |
|---|---|---|---|
| G-A | >=100 completed missions OR >=500 stage decisions across >=3 mission/task types | 0 missions, 0 stage decisions, 0 task types | FAIL |
| G-B | >=95% steps with model id, step order, usable stage features | 0% (schema: 7 flat keys, no step/stage fields) | FAIL |
| G-C | final outcome for >=80% missions or provenance'd proxy | 0% outcome fields | FAIL |
| G-D | retries/tool/test outcomes sufficiently logged | 0 such fields | FAIL |
| Join-key floor (constitution IV) | stable join key or content hash | `prompt_id` hardcoded 0 (1 distinct value); no hash | FAIL |

Trace source: `~/src/hermes-router-retraining-research/evidence/shadow/shadow_log.jsonl`, 69 rows (sha256 `56c7060c4998f4be0c9905145944959e0548bad52e1e074ef177b08e0d97c7a8`), ts span 2026-09-06T09:25:39Z → 2026-09-08, 65 strong / 4 weak, engine `v1_mf_router`/`router-v1-frozen`, mode shadow. All rows are CLI-era health/probe traffic on one distinct prompt. Prior gap memo (`git show feat/generator-pivot-r0:results/V1_BASELINE_GAPS.md`, G1–G5) confirmed exactly; +1 row since its 68-by-baseline count (one more probe row), gaps unchanged. Other surfaces ruled out: launchd service `com.rath.router-shadow-v1` logs (operational only — memo G2 confirmed: production path never logs), `/Users/rath/src` jsonl/log sweep (no mission/step traces; gen_factory = single-turn synthetic, different estimand), RouterBench sealed/not loaded (FR-012).

## Task coverage

- T001 — DONE: constitution/spec/plan/tasks/PROMPT read; trace docs + all candidate sources inventoried.
- T002 — DONE: `results/109/PREREG.md` frozen and committed (66b6f26) BEFORE any audit number was consumed.
- T003 — DONE: `results/109/trace_quality.json` — all gates + join-key floor FAIL with measured detail; verdict `TRACE_DATA_INSUFFICIENT` (613ff8b).
- T004 — DONE: `results/109/TELEMETRY_GAP_CONTRACT.md` — 7 measured gaps (C1–C7), binding future schema, smallest 101-integrated collection plan, frozen re-audit gates; policy modeling stopped (2adf4c0).
- T010–T013, T020–T023, T030–T034, T040–T043, T050–T053 — NOT EXECUTED (conditional phases; blocked by T004 per spec tasks: "stop policy modeling"). T053's status-choice leg is satisfied by this report.

## Spend and integrity

$0.00 total — no paid API/model calls, no duplicate model execution, no interactive browsers. Prereg commit predates report commits. No gate relaxed after results; no stage outcome invented; specs/ folder untouched (`git status` clean, no modifications to `specs/109-hermes-stage-router/`); `ideas/STATUS.md` untouched.

## Revival condition

Re-run this same preregistered audit (gates frozen in `results/109/PREREG.md`, not re-derived) against a trace surface built per `results/109/TELEMETRY_GAP_CONTRACT.md` (101-integrated, identified, outcome-joinable). Pass ALL gates → proceed to 0B value concentration.
