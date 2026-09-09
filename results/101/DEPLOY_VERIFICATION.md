# Idea 101 — Production Deploy Verification (2026-09-09)

Operator-approved deploy; push + launchd restart executed by the operator directly
(orchestrator commands were blocked by the host consent gate; operator ran them via Option 1).

## Deployed artifact
- Branch `research/router-innovation-2026-09-08`, merge `70d46ca` (idea 101 Phase 2-5, SHADOW_READY).
- Push verified: local == origin at `70d46cabefc2dfeada9f18afd4083c364dfe28dc`.
- Service: launchd `com.rath.router-shadow-v1`, PID 34951, started Wed 9 Sep 17:07:05 2026,
  `/Users/rath/src/hermes-router-retraining-research/router_shadow.py`, 127.0.0.1:8765.
- New-code proof: service log shows `[router_shadow] model warmup done in 8.3s`
  (one-shot pre-serving warmup added in this phase).

## Live verification (all checks pass)
1. `/health`: `{"status":"ok","enabled":true,"engine":{"name":"v1_mf_router","version":"router-v1-frozen","mode":"learned"},"telemetry":{"logged":0,"errors":0,"last_error":null}}` — telemetry counters present.
2. Live smoke route (POST /route, synthetic prompt, caller-supplied join ids):
   `{"decision":"strong","confidence":0.5796,"threshold":0.3,"mode":"shadow","engine":"router-v1-frozen","event_id":"9f02ba8d4d8e40c5a1989d612704db20"}` — frozen V1 behavior unchanged; response shape backwards-compatible.
3. Ledger event (evidence/telemetry/decisions.jsonl, appended by the production service):
   `event_id` matches response; `prompt_hash` sha256[:12] only (`065ba7ad65fe`);
   `session_id_hash`/`message_id_hash` present; `traffic_stratum="deployment-verification"`;
   `exploration_mode="disabled"`, `eligibility_reason="not_eligible_no_exploration"`;
   `policy_id="v1-threshold-0.30"`; `schema_version="1.0.0"`. Zero raw prompt text.
4. Post-route `/health`: `logged: 1, errors: 0, last_log_ms: 0.314` (NFR p95 < 5 ms).

## Kill switch / drift guard status
- Code path unchanged and suite-covered (501 tests pass on merged tree, incl. kill-switch,
  threshold-drift 500, config-missing, logging-IO-failure, restart, concurrency).
- Threshold check exercised live implicitly (0.30 accepted, no drift 500).
- Optional live drills (config toggle / drift value) NOT run against production without
  separate operator approval.

## State after deploy
- Production logs decisions with full join keys (closes G1/G2 from results/V1_BASELINE_GAPS.md).
- Outcomes join is a separate write path — no real outcomes yet; 102/108 real-data phases
  unblocked only once joined real outcomes accumulate (results/101/DOWNSTREAM_UNBLOCKS.md).
- Live exploration remains disabled; activation requires operator-countersigned
  experiments/101-live-exploration-prereg.md.
