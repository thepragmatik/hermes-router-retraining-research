# LIVE_PREREG — Idea 101 Phases 2–5 (Live Shadow-Telemetry Plumbing)

**Frozen:** 2026-09-08 (UTC), before any Phase-2 implementation code. This file
freezes the implementation contract for tasks T030–T063. Stage-0
(`STAGE0_PASS`, commit 307beda) is the precondition and is untouched. No gate
below may be weakened after results are seen; deviations require a
CORRECTION_LOG entry here **before** the affected run/test is executed.

Scope guard: all work on branch `101-counterfactual-shadow-telemetry` in
`/Users/rath/src/idea-worktrees/101-counterfactual-shadow-telemetry` only. The
launchd production service `com.rath.router-shadow-v1` (127.0.0.1:8765) is
**never contacted, bound, restarted, or deployed to**; production deploy is the
orchestrator's job after merge. Spend **$0**. RouterBench test split sealed
(membership 3,678 from the split table only; the 0-shot pickle is never loaded).

## 1. Storage choice (T030) — JSONL, frozen

**Choice: append-only JSONL** (`evidence/telemetry/decisions.jsonl` +
`evidence/telemetry/outcomes.jsonl`), not SQLite/WAL.

Justification (recorded as required by the plan's Stage-1 clause):

- Expected write concurrency: one. Both wired paths (CLI single invocation,
  HTTP service `ThreadingHTTPServer` with a single `/route` POST handler) are
  best modeled as a single-process, sequential-append research daemon. The
  HTTP handler serializes logging on a process-wide lock, so even concurrent
  requests do not produce interleaved appends.
- Volume: Stage-1 gates need >=1,000 events; realistic shadow volume is
  orders of magnitude below warehouse scale. Per-record size ~700 bytes.
- JSONL appends are crash-analyzable by construction (one JSON object per
  line, trailing partial line discarded on read), recoverable with plain text
  tooling, and match the existing `evidence/shadow/shadow_log.jsonl` precedent.
- SQLite/WAL buys cross-process transactional concurrency and indexed joins
  we do not need at this volume; it adds a binary artifact to the evidence
  tree that is harder to audit than text. The plan explicitly prefers the
  simpler option when sufficient; it is sufficient here.
- Corruption recovery is tested (trailing partial line discarded; corrupt
  lines quarantined by the readers) rather than assumed.

Atomicity: single `write()` of one fully-serialized line under a process-wide
`threading.Lock`; per-record failure increments a visible counter and never
propagates to the route response (best-effort contract, FR/constitution).

## 2. Schemas (T031/T032) — frozen

`schema_version = "1.0.0"` for both ledgers. All hashes are hex strings.

### DecisionEvent (JSONL row)

| field | type | notes |
|---|---|---|
| `schema_version` | str | "1.0.0" |
| `event_id` | str | uuid4 hex, unique per event (constitution IV; closes G1's placeholder `prompt_id=0`) |
| `ts` | str | ISO-8601 UTC |
| `session_id_hash` | str/null | sha256(caller session_id)[:12] when caller supplies one, else null |
| `message_id_hash` | str/null | sha256(caller message_id)[:12] when caller supplies one, else null |
| `prompt_hash` | str | sha256(prompt text utf-8)[:12] — content hash, never text (closes G3) |
| `traffic_stratum` | str | caller-supplied or "unknown"; free-form, defaults "unknown" |
| `router_id` | str | "router_v1" |
| `router_version` | str | "router-v1-frozen" |
| `representation_version` | str | "bge-small-en-v1.5" |
| `policy_id` | str | "v1-threshold-0.30" |
| `policy_config_hash` | str | sha256 of the frozen policy config string `{"policy_id":"v1-threshold-0.30","threshold":0.3}` |
| `action_set` | list | ["weak","strong"] |
| `chosen_action` | str | "weak"/"strong" |
| `chosen_propensity` | float/null | null iff deterministic (mode "disabled" or non-randomized); float in (0,1] when randomized |
| `action_probabilities` | dict/null | full distribution {action: prob} when randomized, else null |
| `scores` | dict | {"confidence": float} — V1's p_strong; reproduces the policy with the threshold |
| `model_provider_revision` | dict | {"weak": {"model_id","provider","revision"}, "strong": {...}} from config `telemetry.models` |
| `price_snapshot_id` | str | "historical-frozen-2026-09" (constant for shadow stage) |
| `exploration_mode` | str | "disabled" (Phase 3 paths are always deterministic V1) |
| `eligibility_reason` | str | why this event got its mode; "not_eligible_no_exploration" default |
| `log_overhead_ms` | float/null | measured decision-log append latency (T036 instrumentation); null when unmeasured |
| `prompt_id` | int | 0 — legacy compatibility field, constant; identity moved to event_id |

The legacy response/ledger key `prompt_id: 0` is retained **only** in the
response shape for backwards compatibility (tests assert it) and as a constant
placeholder in the ledger marked for deprecation; the join identity is
`event_id`. The disabled path logs **no** decision event (no route happened).

### OutcomeEvent (JSONL row)

| field | type | notes |
|---|---|---|
| `schema_version` | str | "1.0.0" |
| `outcome_id` | str | uuid4 hex, unique per outcome row |
| `event_id` | str | join key to decisions ledger (exactly-one semantics) |
| `outcome_ts` | str | ISO-8601 UTC |
| `outcome_type` | str | "routed_answer_correct" (the only type in this feature) |
| `outcome_value` | float | 0.0/1.0 correctness |
| `outcome_scale` | str | "binary_0_1" |
| `provenance_class` | str | one of `task_native, human_acceptance, randomized_model_outcome, benchmark, judge, synthetic, unknown` (FR-006 fidelity classes) |
| `evaluator_id` | str | who produced it, e.g. "fixture", "human", "llm_judge" |
| `evaluator_version` | str | free-form |
| `finality` | str | `provisional`/`final`/`superseded` |
| `metadata` | dict | whitelisted small keys only; **no prompt text, no free-form user text** |
| `supersedes_outcome_id` | str/null | set when finality="superseded" |
| `log_overhead_ms` | float/null | measured outcome append latency; null when unmeasured |

Join rule (T032): deterministic reconciliation — group outcomes by `event_id`,
order by (`outcome_ts`, `outcome_id`), apply `finality` precedence
`final > superseded > provisional` (ties broken by later ts), emit per-event
status `joined` (exactly one final/provisional outcome), `ambiguous` (>1
final or >1 distinct non-superseded outcome chains), `unjoined` (decision
event with no outcome), `orphan` (outcome with no decision event).

## 3. Stage-1 gate thresholds — copied verbatim from spec.md lines 109–118

On >=1,000 test/replay/service events:

- **G1'** >=99.9% valid unique event ids;
- **G2'** 100% action/model/router version provenance;
- **G3'** 100% propensities present for randomized events;
- **G4'** >=99% join success for fixture outcomes;
- **G5'** 0 raw prompt text in the decision ledger unless an explicit separate privacy-approved artifact is used;
- **G6'** service-side logging parity verified.

Measured on the Stage-1 evidence stream (fixture-driven service/CLI traffic,
>=1,000 events; see §5). A gate passes only on the measured number; if any
gate fails, the terminal verdict is the failing-gate word, not a narrative.

## 4. Test matrix (T033/T034/T043/T054)

| # | test | asserts |
|---|---|---|
| A1 | duplicate outcome fixture | duplicate (same outcome_id) rows collapse to one join; distinct outcome_id same event → resolved by finality precedence |
| A2 | late outcome fixture | late-arriving (after first join) updates resolve deterministically, never reassign to a different decision |
| A3 | provisional→final | provisional superseded by final for the same event; final stays |
| A4 | contradictory outcomes | two non-superseded finals → `ambiguous`, surfaced in quality report |
| A5 | raw-prompt leakage | no ledger row, error, or report echoes any fixture prompt text |
| A6 | repo grep PII sweep | grep fixture/telemetry logs for fixture prompt strings → 0 hits |
| A7 | schema drift | a row missing a required field or with wrong type is quarantined + counted, not silently accepted |
| A8 | kill switch | config `enabled: false`/missing → disabled response, model never loaded, no decision event logged |
| A9 | threshold drift | threshold != 0.30 → CLI exit 2 / HTTP 500, no event logged |
| A10 | config missing | fail closed to disabled |
| A11 | logging I/O failure | read-only log dir → route still succeeds (HTTP 200/CLI exit 0), error counter > 0, health endpoint shows it |
| A12 | restart | new process appends to the same JSONL without clobber; all prior rows still readable |
| A13 | concurrent requests | parallel POSTs: all succeed, all logged, exactly one line per event, no interleaving |
| A14 | CLI/service parity | same prompt → same decision/confidence/threshold on both paths; both ledgers carry identical provenance fields |
| A15 | exploration disabled default | mode resolves "disabled" for every config; realized alternate-action rate 0; propensities null on all events |
| A16 | seeded epsilon randomization | in test harness only: realized rate within tolerance of configured epsilon, exact propensities logged, all randomized events carry propensities |
| A17 | rate/spend caps | sentinel rate cap and spend-cap hook trigger fail-closed at the configured bounds |
| A18 | 10k-event simulation | >=10,000 simulated events: realized exploration rate matches configured probability; 100% of randomized events carry propensities |

Load test (T036): >=1,000 sequential decision-event appends (plus the parity
stream to >=1,000 total) with per-append wall-clock; report p50/p95 logging
overhead. Target (spec NFR): p95 < 5 ms locally excluding fsync/network.

## 5. Stage-1 evidence stream construction

The 1,000+ events are **local fixture traffic only** ($0, no external calls):
prompts drawn from a fixed list of short synthetic strings (never RouterBench
content); decisions produced by the actual frozen V1 engine on the actual
service/CLI paths (torch inference is local/free); outcomes are synthetic
fixture labels (`provenance_class="synthetic"`, `evaluator_id="fixture"`) so
G4' measures the join machinery, not any real model quality. The stream
exercises: CLI path, HTTP service path, duplicate prompts (hash stability),
distinct prompts (unique ids), session/message hash joins, disabled/kill-switch
and error-counter paths (logged as aggregates, not fake events).

## 6. Port discipline

All test servers bind `127.0.0.1` on ports **>= 8766** (default test port
8899). Binding 8765 anywhere in code or tests is forbidden — 8765 is the
production launchd service port. The production service is never contacted.

## 7. Rollback

Pure git rollback: `git revert` of the Phase-2/3 commits on this branch +
orchestrator-side `launchctl kickstart -k` restart of
`com.rath.router-shadow-v1` after merge (restart is orchestrator-only).
The logger is best-effort by construction: reverting the wrapper commits
restores the pre-101 behavior exactly (service routes without logging).
Kill switch (`router.enabled: false` in `router_config.yaml`) stops all
routing without a deploy; logging failure never breaks routing (tested A11).

## 8. Model/provider/revision map (FR-004)

For the shadow stage the ledger records the V1 pair from
`router_config.yaml` → `telemetry.models` (added by this feature; defaults
frozen here): `weak` = `{"model_id": "gpt-4o-mini-2024-07-18", "provider":
"openai", "revision": "2024-07-18"}`, `strong` = `{"model_id":
"gpt-4o-2024-11-20", "provider": "openai", "revision": "2024-11-20"}`. These
are the historical frozen RouterBench-pair identifiers recorded as
`price_snapshot_id = "historical-frozen-2026-09"` metadata; they describe the
pair V1 was trained on and are never called (no paid calls exist on this
path). Current-id refresh is a Stage-2 live-gate prerequisite, out of scope
here and flagged in telemetry/README limitations.

## 9. Spend

$0. No model API calls anywhere in Phases 2–5; the only inference is the
local frozen V1 torch model on fixture prompts (free, already installed).
No new dependencies: stdlib + PyYAML (+ pytest 8.4.2 for tests).

## 10. CORRECTION_LOG (deviations from this prereg; each recorded before the
affected test/report consumed results)

- **C-1 (join supersede semantics, recorded before the affected tests ran in
  their final form):** §2's join rule said finality precedence
  `final > superseded > provisional` applied to the STORED finality of each
  row. In an append-only ledger a superseded row cannot be rewritten to carry
  `finality: "superseded"` retroactively, so supersession is implemented
  **by reference**: any row whose `outcome_id` appears in another row's
  `supersedes_outcome_id` is dead regardless of its stored finality. Same
  frozen outcome (exactly-one live final per event); the mechanism is
  reference-based, matching the append-only discipline. Duplicate outcomes
  sharing an outcome chain resolve via this rule; two live finals with NO
  supersession link remain `ambiguous` (T033 fixture A1 asserts this).
  Also: join units are per-UNIQUE decision `event_id` (a duplicated
  decision row is one join unit, not two) — duplicate decision appends count
  once in the quality report's join stats and once in the duplicate-id count.
- **C-1b (outcome metadata whitelist):** `note` removed from the metadata
  whitelist (T034 review: a free-text-bearing key is a PII surface).
  Whitelist frozen as `("source", "fixture")` — controlled vocabulary only.
  Recorded before the affected validation test ran.
- **C-2 (service concurrency guard):** the plan did not specify model-load
  behavior under concurrent requests. Observed: simultaneous first /route
  requests raced the lazy torch/encoder import inside `router_v1.route`,
  killing handler threads mid-import (RemoteDisconnected bursts). Fix at the
  wrapper level only (no `router_v1/` change): the service performs a
  single-threaded model warmup BEFORE accepting traffic and serializes
  `route()` calls under a process-wide `ROUTE_LOCK`. Recorded here because
  the prereg's test matrix (A13) exercised concurrency before this guard
  existed; the fix precedes the passing A13 run.
- **C-3 (G3' propensity gate scope):** spec line 114 requires "100%
  propensities present for randomized events". In the Stage-1 evidence stream
  ALL events are deterministic (`exploration_mode="disabled"`, zero
  randomized events), so the gate measures 100% propensity coverage over an
  EMPTY randomized set (vacuous). The property itself is proven by the Phase-4
  10k simulation (every randomized event carries a propensity in (0,1]) and
  by schema-level refusal (`validate_decision` rejects randomized events
  without propensities). Recorded here rather than silently redefining G3'.
