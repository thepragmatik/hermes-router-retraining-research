# telemetry/ — Idea 101 shadow telemetry plumbing

Append-only decision/outcome ledgers for the frozen V1 shadow router
(idea 101, spec `specs/101-counterfactual-shadow-telemetry/`). Contract
frozen in `results/101/LIVE_PREREG.md` (commit `6ecd41e`, before any code).

## What lives here

| module | task | purpose |
|---|---|---|
| `schema.py` | T010-era + Phase 2 | versioned DecisionEvent/OutcomeEvent validators, sha256[:12] hash helpers, closed vocabularies |
| `decision_log.py` | T031 | append-only JSONL decision writer, visible error counters, best-effort contract |
| `outcome_log.py` | T032 | append-only JSONL outcome writer + reader |
| `join.py` | T032 | deterministic reconciliation (exactly-one semantics, supersede-by-reference, ambiguity surfacing) |
| `fixtures.py` | T033 | duplicate / late / provisional-final / contradictory outcome fixtures |
| `report.py` | T035 | data-quality report CLI (unique ids, provenance, propensities, joins, drift, prompt-text scan) |
| `wiring.py` | T040/T041 | the ONE shared logger both routing paths import (service parity, G2) |
| `exploration.py` | T050-T053 | eligibility predicates, modes (`disabled` default / `shadow_dual` / `randomized_sentinel`), seeded epsilon with exact propensities, rate+spend caps |
| `stage0.py`, `stage0_runner.py` | Phase 0/1 | OPE simulator (Stage-0, `STAGE0_PASS`) |
| `stage1_runner.py` | T044 | Stage-1 evidence generator + gate measurement (>=1,000 events) |

## Commands

```bash
# data-quality report over a ledger dir (default evidence/telemetry)
python3 -m telemetry.report [log_dir]

# regenerate Stage-1 evidence + gates (~6-8 min; local torch inference only)
python3 telemetry/stage1_runner.py

# full test suite
python3 -m pytest tests/ telemetry/ -q
```

## Data contracts

**Decisions** → `evidence/telemetry/decisions.jsonl`, schema_version `1.0.0`,
one JSON object per line (append-only). Required fields and types:
`results/101/LIVE_PREREG.md` §2. Identity = `event_id` (uuid4 hex); the legacy
`prompt_id: 0` is response-shape compatibility only and is deprecated.
Join keys: `prompt_hash` = sha256(prompt)[:12]; `session_id_hash` /
`message_id_hash` = sha256(caller id)[:12] when the caller supplies one,
else null. **Raw prompt text and raw caller ids never enter any ledger**
(enforced by construction + tests; metadata is a closed whitelist).

**Outcomes** → `evidence/telemetry/outcomes.jsonl`, schema_version `1.0.0`.
`provenance_class` is a closed fidelity vocabulary (constitution IV/VI):
`task_native, human_acceptance, randomized_model_outcome, benchmark, judge,
synthetic, unknown`. `finality`: `provisional | final | superseded`
(supersede is by reference via `supersedes_outcome_id` — append-only rows are
never rewritten).

**Join semantics** (`join.py`): one join unit per unique decision `event_id`;
live finals >1 → `ambiguous` (surfaced, never silently resolved); a decision
with no outcome → `unjoined`; an outcome with no decision → `orphan`.

## Estimator assumptions (inherited from Stage 0)

OPE (IPS / SN-IPS / cross-fitted DR / SWITCH-DR M=20) requires every
randomized event to carry its exact chosen propensity in (0,1]. Deterministic
events have `chosen_propensity: null` — downstream learners MUST NOT treat
missing propensities as known (constitution IV). Corrupted/missing propensities
raise loudly (G4 tests).

## Limitations

- The `model_provider_revision` map records the historical frozen RouterBench
  pair under `price_snapshot_id="historical-frozen-2026-09"`; it describes what
  V1 was trained on and is NEVER called. Refresh current IDs/prices before any
  live/Stage-2 work (constitution XII).
- The service serializes model inference (`ROUTE_LOCK`) and warms the model
  before serving; throughput is bounded by the local encoder (~5-8 routes/s).
  Fine for shadow; not a production-load design.
- JSONL ledgers assume the single-process append discipline documented in
  `LIVE_PREREG.md` §1; multi-writer deployment would need SQLite/WAL (out of
  scope, recorded in the prereg).
- `randomized_sentinel` mode exists but is inert: no production path
  constructs it without an operator-approved, countersigned prereg
  (`experiments/101-live-exploration-prereg.md` — DRAFT, approval fields
  unfilled). Default mode is and remains `disabled`.

## Production notes (deployed 2026-09-09)

- The production shadow service runs via launchd `com.rath.router-shadow-v1` on
  `127.0.0.1:8765` (`router_shadow.py`); health at `GET /health`, decisions at
  `POST /route`. See `results/101/DEPLOY_VERIFICATION.md`. `/route` rejects
  empty/missing (or whitespace-only, non-string) prompts with HTTP 400; no
  model call, no ledger write.
- Live decision ledger: `evidence/telemetry/decisions.jsonl` (outcomes:
  `evidence/telemetry/outcomes.jsonl`). Real traffic is being logged; no joined
  real outcomes exist yet.
