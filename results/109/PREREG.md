# PREREG — Idea 109 Hermes Stage-Aware Agent Router — Stage 0A Trace Viability Check

**Frozen before audit verdict.** Idea: 109-hermes-stage-router. Branch: `109-hermes-stage-router`. Spend cap: $0 (no paid API/model calls, no interactive browsers; no duplicate model execution authorized by spec/tasks).

## Purpose

Execute spec Stage 0A (trace viability) only: inventory and quality-gate the available Hermes mission traces to decide whether agentic-stage routing (strong intelligence at specific workflow stages) has enough identified, outcome-joinable evidence to proceed to 0B value concentration / 0C heuristic tests. If gates fail, the deliverable is a telemetry-gap contract and terminal status `TRACE_DATA_INSUFFICIENT` — this is the spec-defined SUCCESS for Stage 0A, not a kill of the idea. No stage labels are manufactured, no policy modeling, no invented outcomes.

## Trace sources inventoried (frozen list)

1. `evidence/shadow/shadow_log.jsonl` (research repo `/Users/rath/src/hermes-router-retraining-research/`, worktree-shared read-only; sha256 at time of freeze: `56c7060c4998f4be0c9905145944959e0548bad52e1e074ef177b08e0d97c7a8`, 69 rows). This is the ONLY known Hermes decision/trace log; documented gap evidence G1–G5 in `results/V1_BASELINE_GAPS.md` (branch `feat/generator-pivot-r0`, read via `git show`).
2. Launchd shadow service `com.rath.router-shadow-v1` (127.0.0.1:8765): per gap memo G2 the production traffic path routes and returns only; it writes no decision log. Its error/stdout logs (`router-shadow-v1.err.log`, `router-shadow-v1.log`) are operational, not decision traces — checked only to confirm absence of decision records, never treated as traces.
3. No other Hermes mission/step trace source exists in `/Users/rath/src` (searched: `*.jsonl`, mission/trace/agentic log names). gen_factory ledgers/labels are single-turn synthetic supervision surfaces, not agent mission traces — out of scope for 109's estimand.
4. RouterBench is sealed and is NOT the qualification set (spec FR-012); not loaded, not deduplicated, not sampled.

## Stage schema / outcome fidelity definitions (frozen)

A trace is agentic-stage-viable only if it carries the spec Trace Contract minimum per step: mission_id, step_id, timestamp, stage/state label or raw event features, model/action + revision, tool/result status, test/build/lint result, retry/no-progress indicators, cumulative tokens/cost/latency, final mission success/acceptance + outcome provenance, parent/previous-step link. Outcome fidelity is classified per constitution VI (1 real accepted outcome … 6 synthetic); a record without any outcome join is observability, not training data (constitution IV).

## Minimum sample gates (frozen — spec Stage 0A verbatim)

- G-A: >= 100 completed missions, OR enough steps to produce >= 500 stage decisions, across >= 3 mission/task types.
- G-B: >= 95% of steps carry model id, step order, and usable stage/runtime features.
- G-C: final outcome available for >= 80% of missions, or a clearly defined proxy with provenance.
- G-D: retries/tool/test outcomes sufficiently logged to identify progress/failure states.
Plus constitution IV identifiability floor: stable join key or privacy-preserving content hash present.

Decision rule: ALL of G-A–G-D plus the join-key floor must pass => proceed to Stage 0B (`TRACES_VIABLE`); ANY fail => `TRACE_DATA_INSUFFICIENT` + telemetry-gap contract, stop policy modeling. No gate is relaxed after seeing results; a pass is not claimed from proxy definitions invented after the audit.

## Baselines (frozen for later phases, not run here)

Spec FR-002 set: all-cheap, all-strong/frontier, fixed mission-level model, V1-like per-prompt baseline, simple stage heuristics (<= 5 rules with cooldown/hysteresis). Bootstrap unit: mission (never individual correlated steps). These are recorded now so later phases cannot move them; they are not evaluated in this Stage 0A pass.

## Integrity

PREREG committed before trace_quality.json/report commits; prereg commit must predate report. $0 spend; no stage outcome invented; gates not relaxed. Terminal vocabulary exactly: `TRACE_DATA_INSUFFICIENT | KILLED | HEURISTIC_PASS | LEARNED_PASS | QUALIFIED_AGENTIC` (PROMPT.md) — this pass can only end in `TRACE_DATA_INSUFFICIENT` (spec tasks T004) or continuation vocabulary per spec (`TRACES_VIABLE` for a passing Stage 0A is reported as trace_quality.json `verdict`).
