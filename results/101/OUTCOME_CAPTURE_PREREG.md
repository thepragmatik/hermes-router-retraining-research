# OUTCOME_CAPTURE_PREREG — Idea 101 outcome capture (frozen before code)

Commit order: this file is committed BEFORE any implementation code. No paid
API calls. router_v1/ read-only. specs/ read-only. Production service
127.0.0.1:8765 untouched (orchestrator deploys). Test services bind ports
>= 8766 only. Live telemetry ledgers under evidence/telemetry/*.jsonl are
local-only gitignored — read-only for this work; production may append.

## 0. Frozen vocabulary and exact contracts

### POST /outcome (NEW endpoint)

Request JSON body, all keys optional except event_id/outcome:

- `event_id`: string. Matching rule (FROZEN): the service matches the value
  against logged decision events by EXACT full 32-hex string equality against
  the ledger's `event_id` values. If the value is shorter than 32 chars
  (1..31 chars), it is treated as a PREFIX: it must be a valid hex string.
  - 0 matching events -> HTTP 404, body {"error": "unknown event_id"}
  - >1 matching events (prefix ambiguity) -> HTTP 409,
    body {"error": "ambiguous event_id prefix"}
  - non-string or empty event_id -> HTTP 400,
    body {"error": "invalid event_id"}
- `outcome`: required, one of the frozen closed vocabulary:
  `"success" | "failure" | "timeout" | "aborted"`. Anything else -> HTTP 400,
  body {"error": "invalid outcome"}. Missing outcome key -> same 400.
- `cost`: optional, positive number (> 0). int or float; bool rejected.
  Invalid -> HTTP 400, body {"error": "invalid cost"}.
- `latency_ms`: optional, positive int (> 0). Floats/bools/strings rejected.
  Invalid -> HTTP 400, body {"error": "invalid latency_ms"}.
- `note`: optional string <= 200 chars. Longer -> HTTP 400,
  body {"error": "invalid note"}. The note is operator-supplied metadata and
  is stored as given (caller-provided, not prompt text; the endpoint never
  receives prompts).
- Malformed JSON body / non-JSON -> HTTP 400, body {"error": "malformed json"}.

Success: HTTP 202, body {"outcome_id": <32-hex>, "event_id": <matched id>,
"status": "logged"} and ONE row appended to the NEW local-only ledger
`evidence/telemetry/outcomes.jsonl` (append-only JSONL, atomic single write
per line under a process lock, fsync-after-write for crash safety; a write
failure is 500 {"error": "outcome write failed"} and increments
outcomes.errors — no silent loss, no decisions.jsonl touch).

Outcomes ledger row schema (FROZEN, schema_version "1.1.0"):
`{"schema_version", "outcome_id", "event_id", "outcome", "cost"?,
"latency_ms"?, "note"?, "ts", "joined_session_id_hash", "joined_message_id_hash"}`
where joined_*_hash are copied from the matched decision event when present
(null otherwise) so the join tool can report id hygiene without re-reading
decisions. Order-independent dedup: if an (event_id, outcome) pair is already
present in outcomes.jsonl -> HTTP 409,
body {"error": "duplicate outcome"} and NO append.

NO model call, NO changes to decisions.jsonl, NO envelope involvement.

### /health additive counters

- `outcomes.logged`, `outcomes.errors` — additive keys on the existing health
  object (outcomes section nested as `"outcomes": {"logged": n, "errors": n}`).
  In-memory per-process; reset on restart; same semantics as telemetry counters.
- CLEANUP B: `"edge_rejections": {"empty_prompt": n, "missing_prompt": n,
  "whitespace_prompt": n, "non_string_prompt": n, "malformed_json": n}` —
  in-memory per-process counters, reset on restart, incremented on each 400
  for the corresponding shape. All five keys always present (0 when unused),
  additive-only. The edge-400 response bodies themselves are UNCHANGED.
- SCOPE ADDITION (operator-requested, folded in pre-code): 
  `"missing_ids_logged": n` = count of decisions logged by THIS process whose
  session_id_hash OR message_id_hash was null. In-memory per-process, reset on
  restart. Additive-only.

### CLEANUP A — decision schema bump to "1.1.0" (prompt_id dropped)

`SCHEMA_VERSION` moves "1.0.0" -> "1.1.0" (FROZEN exact value). NEW decision
events no longer carry `prompt_id`. OLD rows keep it. Validation:
`validate_decision` accepts rows from BOTH schemas — presence of prompt_id is
optional (if present must equal the legacy 0); absent is fine on 1.1.0.
Old consumers keying on prompt_id must move to prompt_hash/event_id; the
removal is a schema bump, documented here and in telemetry/schema.py.
Outcome rows validate against the same SCHEMA_VERSION constant ("1.1.0").
(Existing telemetry OUTCOME_REQUIRED schema from LIVE_PREREG remains
unchanged for the synthetic/fixture outcome events; the NEW outcomes.jsonl
service rows use the simpler row schema above — two distinct, both frozen.)

### Outcomes ledger local-only

`.gitignore` already contains `evidence/telemetry/*.jsonl` — outcomes.jsonl is
covered; no .gitignore change needed (verified). Never committed, never
modified/deleted by this work; production appends are fine.

### JOIN TOOL (read-only, stdlib)

`experiments/101/join_outcomes.py`:
- Inputs: `--decisions PATH --outcomes PATH` (default evidence/telemetry paths).
- Loads ledgers read-only (schema-tolerant: reads both decision schema
  versions; quarantines bad lines, never crashes on one bad row).
- Emits to STDOUT only (no file writes unless --out PATH given):
  - n_decisions, n_outcomes, join_rate (outcomes joined to decisions /
    n_outcomes), orphan count (outcome with no decision);
  - outcome breakdown by chosen_action and by envelope.action (envelope
    frames live in /route responses, not the decision ledger — the join tool
    reads envelope action from the OUTCOME note field if the operator chose
    to record it; otherwise envelope.action breakdown is emitted as null/absent;
    FROZEN: envelope breakdown is computed from outcome rows' optional
    `note`-embedded `envelope_action=<x>` tag when present);
  - avg cost by chosen_action (rows with cost only; "-" when none);
  - join-readiness section (SCOPE ADDITION): fraction of decisions with null
    session_id_hash and fraction with null message_id_hash; WARNING line
    printed when either fraction > 0.20.
- `--self-test`: runs tiny built-in fixtures (no external data) and asserts
  expected summary values; exit 0 on pass.

## 1. Behavior invariants preserved exactly

- V1 decision semantics, envelope record-only, kill switch, threshold-drift
  500, edge-400 responses (bodies unchanged; only new counters), C1-C7 ledger
  fields unchanged except the pre-approved prompt_id removal (schema bump),
  /health shape additive-only.
- /outcome validation precedes any state change; a 400/404/409 writes NO ledger
  row and changes NO counter except (for 400s) the edge_rejections-shaped
  counters are NOT used for /outcome — outcome request errors are NOT edge
  rejections of /route; they are observable via outcomes.errors? NO — frozen:
  outcome 4xx responses increment NOTHING (pure request validity), only the
  5xx write-failure increments outcomes.errors.

## 2. Test matrix (red-first, full suite 234 + new all green)

1. outcome happy path -> 202 + file row with frozen schema;
2. unknown event_id -> 404, exact body;
3. ambiguous prefix -> 409, exact body;
4. malformed JSON -> 400 exact body; invalid outcome/cost/latency/note -> 400
   exact bodies;
5. duplicate (event_id, outcome) -> 409, no second append;
6. /outcome never touches decisions.jsonl (byte-identical before/after) and
   makes no model call (disabled-config service still accepts outcomes);
7. join tool --self-test passes; join tool on fixture ledgers produces frozen
   summary shape incl. join-readiness warning at >20% null ids;
8. schema bump: new decision events lack prompt_id and carry schema_version
   "1.1.0"; a synthetic 1.0.0 row with prompt_id still validates; old
   read_decisions still works;
9. edge_rejections counters increment per shape (all five), additive on
   /health, edge-400 bodies unchanged;
10. missing_ids_logged counts logged decisions with null id hashes; 
11. all prior invariants: full suite green.

## 3. Live black-box check (local test service, port >= 8766)

POST routes, POST one outcome of each error shape + happy paths, run join
tool, verify join_rate/breakdown/join-readiness, /health shows all new
counters. Production 8765 never contacted or bound.

## 4. Deviations

None at freeze time. SCOPE ADDITION (missing_ids_logged + join-readiness)
received before any code was written and is folded into this prereg
normally (no erratum needed).


---

## ERRATUM 1 (2026-09-09, BEFORE enforcement code — operator policy change)

**Policy change: id ENFORCEMENT supersedes the missing_ids_logged counter
steer.** The operator mandates 100%-joinable traffic: null-id decisions must
become impossible by construction, not merely counted.

1. **POST /route now REQUIRES session_id AND message_id.** Missing, empty,
   or whitespace-only value for either -> HTTP 400 with frozen body
   {"error": "session_id and message_id are required"} and NO ledger write,
   NO model call, handled exactly like the empty-prompt edge rejection
   (precedes config/kill-switch/threshold checks; protected paths stay
   reachable). Counters: the edge_rejections family gains sibling keys
   `missing_session_id`, `missing_message_id` (in-memory per-process, reset
   on restart, incremented per offending request; both increment when both
   are missing — precedence: session_id checked first, message_id second;
   prompt-edge shapes unchanged and still win via the frozen precedence
   malformed > non-string/missing/whitespace/empty prompt... FROZEN ORDER:
   prompt edge checks first (existing bodies), then id checks). Whitespace
   definition: str value with .strip() == "" (after isinstance str check);
   non-string id values (e.g. 123) count as missing. Both missing increments
   BOTH counters (independent checks).
2. **/outcome UNCHANGED** by this erratum: keys on event_id only; the
   already-frozen /outcome contract stands exactly as written above.
3. **Rationale**: operator mandates 100% joinable traffic; null-id decisions
   should be impossible by construction.
4. **missing_ids_logged counter**: RETAINED as a cheap invariant check that
   must stay pinned at 0 (with enforcement, no logged decision can have a
   null id hash; a nonzero value after restart signals enforcement bypass
   or pre-existing legacy rows appended in-process — alarm-worthy).
5. **Join tool join-readiness section**: STAYS as preregistered (it audits
   the historical ledger, which contains 22 null-id rows from earlier test
   traffic; the WARNING remains the operator's id-hygiene signal for
   legacy rows).
6. **Tests**: 400 shapes for missing session_id, missing message_id, both,
   whitespace-only session_id, whitespace-only message_id, empty-string
   values, non-string values; NO ledger write on each; health counters
   asserted. All prior service tests updated to POST with explicit ids.
   Callers: no internal cron/verifier scripts POST /route in this repo
   (verified by grep at erratum time; production callers are external to
   this repo — deploy note: any external caller omitting ids will start
   receiving 400s after the orchestrator deploys).
