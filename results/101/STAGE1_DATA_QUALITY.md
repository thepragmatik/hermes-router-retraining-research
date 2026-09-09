# Stage 1 Data Quality — Idea 101 (Counterfactual Shadow Telemetry)

**Run:** 2026-09-09 (UTC) · **Prereg:** `results/101/LIVE_PREREG.md` (frozen
commit `6ecd41e`, before any Phase-2 code) · **Spend:** $0
**Terminal status: SHADOW_READY** (all six Stage-1 gates measured PASS on
1,100 events; correction C-4 applied to the G4' measurement before its final
value was consumed — see prereg §10).

## Evidence stream

1,100 decision events through the REAL paths with the REAL frozen V1 engine
(threshold 0.30, untouched):

- 660 via HTTP `POST /route` on a test service bound 127.0.0.1 on an
  ephemeral port >= 8766 (production port 8765 never touched);
- 440 via the CLI (`router_v1_cli.py`);
- 40 distinct synthetic fixture prompts (duplicate-heavy by design: prompt
  hash stability), 8 distinct caller sessions; 594 fixture outcomes
  (`provenance_class="synthetic"`) written for 90% of service events
  (partial-feedback design; CLI events intentionally receive no outcomes).

Stream composition verified from the ledger: 1,100/1,100 unique `event_id`,
40 distinct `prompt_hash`, 8 distinct `session_id_hash`, weak/strong
0/1100 on this prompt pool, `exploration_mode="disabled"` on 100%
(no live randomization exists anywhere in this stage).

## Stage-1 gates (spec.md lines 109–118, verbatim thresholds)

| Gate | Measured | Threshold | Verdict |
|---|---|---|---|
| G1' unique valid event ids | **100.0%** (1100/1100) | >= 99.9% | **PASS** |
| G2' action/model/router provenance | **100.0%** (0 rows missing) | 100% | **PASS** |
| G3' propensities on randomized events | **100.0%** (0 randomized events; property proven by Phase-4 10k sim + schema refusal — correction C-3) | 100% | **PASS** |
| G4' join success for fixture outcomes | **100.0%** (594/594 fixtured events resolved `joined`; 0 ambiguous, 0 orphans) | >= 99% | **PASS** |
| G5' raw prompt text in decision ledger | **0 hits** (scan over both ledgers) | 0 | **PASS** |
| G6' service-side logging parity | **100.0%** (660/660 service routes logged via the shared logger, event_id returned; CLI/HTTP parity test A14 green) | verified | **PASS** |

Machine-readable: `results/101/stage1_data_quality.json` (includes the full
quality report: duplicate ids 0, missing provenance 0, schema drift
quarantined 0/0, ambiguous joins [], orphans 0).

Notes:
- Overall joined/decisions = 594/1100 (53.9%) is the partial-feedback design,
  NOT the gate: the spec's G4' is join success *for fixture outcomes*, i.e.
  over events that received one. The first measurement run scored G4' with
  the wrong denominator (0.54, FAIL); correction C-4 fixed the measurement —
  same ledgers, no new traffic, no threshold change — before the final gate
  value was consumed.
- Logging overhead (T036, separate load test, 1,200 sequential appends):
  **p50 = 0.011 ms, p95 = 0.014 ms** (NFR: p95 < 5 ms) — `tests/test_101_load.py`.

## Robustness matrix (all green, `tests/test_101_service.py` + ledger tests)

kill switch (no model load, no event) · missing config (fail closed) ·
threshold drift (CLI exit 2 / HTTP 500, no event) · logging I/O failure
(route survives, /health error counter >= 1) · service restart (append-only
preserved) · 12 concurrent requests (all logged exactly once, no
interleaving) · duplicate prompts (same hash, distinct ids) · caller
session/message ids hashed, never raw · telemetry disable env switch.

## Corrections consumed

C-1 (join-by-reference supersede semantics), C-1b (metadata whitelist
narrowed), C-2 (concurrency cold-start guard), C-3 (G3' scope), C-4 (G4'
denominator) — all recorded in `results/101/LIVE_PREREG.md` §10 with their
timing relative to the affected tests/results. No gate threshold was moved.

## What Stage 1 does NOT claim

No real-outcome data exists yet (outcomes here are synthetic fixtures
exercising the join machinery); no live traffic was touched (production
service 8765 never contacted; deploy is orchestrator-side); no exploration
was enabled (modes default `disabled`; the live-exploration prereg is DRAFT
with operator approval fields unfilled).
