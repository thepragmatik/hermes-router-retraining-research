# EDGE_REJECTION_PREREG — 101 edge-prompt rejection (frozen before code)

Preregistered BEFORE any implementation. Branch `fix/101-edge-prompt-rejection`
(worktree `/Users/rath/src/idea-worktrees/fix-edge`). This commit precedes all
code. Spend $0. No production contact; deploy is orchestrator-owned.

## Motivation (evidence)

`results/101/LIVE_VERIFICATION.md` § "Edge cases": the production service
currently routes and logs a decision for empty prompts, logging
`prompt_hash = e3b0c44298fc` (sha256("")). This is unintended. This prereg
freezes the exact new contract; no gate, envelope, threshold (0.30), or frozen
V1 internal changes.

## Frozen behavior contract — POST /route

Validation happens **immediately after payload parse**, BEFORE
config/kill-switch/threshold checks. Rationale: validation must precede any
state change and must not shadow the threshold-drift 500 or kill-switch paths
(a drifted-threshold request with an empty prompt still returns 500, not 400;
a disabled service with an empty prompt still returns 400, not "disabled" —
input validity is a property of the request, independent of service state).

For any prompt that fails validation the service returns, with NO model call
and NO telemetry/ledger write:

- HTTP status: **400**
- JSON body (frozen exact string): `{"error": "empty or missing prompt"}`

Validation rules (frozen):

| input | verdict |
|---|---|
| `"prompt": ""` | 400 |
| `"prompt": "   "` (whitespace-only) | 400 |
| prompt field absent | 400 |
| `"prompt": 123` (non-string) | 400 |
| `"prompt": null` | 400 |
| `"prompt": "valid text"` | unchanged 200 behavior |

The prompt is rejected when `not isinstance(prompt, str) or not prompt.strip()`.

Explicit non-goals / unchanged surfaces:

- `GET /health` shape unchanged: `{"status", "enabled", "engine", "telemetry"}`.
- Decision envelope for valid prompts unchanged (decision, confidence,
  threshold, mode, engine, ts, event_id).
- Malformed JSON body: existing behavior unchanged (parsed as `{}` -> now
  falls into the missing-prompt 400; this is part of the new contract).
- Non-`/route` POST paths still 404.
- Telemetry schema/logger unchanged; no new event types.

## No side effects guarantee

A 400 response must not: call `router_v1.route`, load the model lazily, or
call `record_route_decision`. Ledger row count for the test telemetry dir must
be 0 after any sequence of 400-producing requests.

## Exact test matrix (TDD, red-first)

1. `test_route_empty_prompt_400` — prompt `""` → HTTP 400, exact body, zero
   ledger rows, service still healthy after.
2. `test_route_missing_prompt_400` — `{}` payload → 400, zero ledger rows.
3. `test_route_whitespace_prompt_400` — `"   "` → 400, zero ledger rows.
4. `test_route_nonstring_int_prompt_400` — `123` → 400, zero ledger rows.
5. `test_route_null_prompt_400` — `null` → 400, zero ledger rows.
6. `test_route_400_precedes_threshold_drift` — drifted-threshold config +
   empty prompt → **500** (drift wins, not shadowed) with body
   `{"error": "threshold drift"}`.
7. `test_service_healthy_after_400s` — after several 400s, `/health` returns
   200 with unchanged shape and a subsequent valid prompt routes normally.
8. `test_valid_prompt_unchanged` — existing valid-prompt 200 envelope intact
   (already covered by existing suite; asserted again in the edge file).
9. Existing 501-test suite fully green (compatibility gate).

Implementation order frozen: validate in `do_POST` right after payload parse;
update `telemetry/README.md` with one line (`/route` rejects empty/missing
prompts with 400); full suite run before each commit beyond the prereg.

## Acceptance

- All new tests pass; full suite (501 prior + new) green.
- `evidence/telemetry/*.jsonl` untouched (untracked, local-only).
- Test ports >= 8766; production 8765 never bound; service never restarted.
