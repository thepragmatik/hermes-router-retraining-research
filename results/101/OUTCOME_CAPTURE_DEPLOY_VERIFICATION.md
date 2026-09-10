# 101 Step-2 Outcome Capture — Deploy Verification — 2026-09-10

Orchestrator-executed production deploy of the preregistered outcome-capture
work (`results/101/OUTCOME_CAPTURE_PREREG.md` + errata 1–2, branch
`feat/101-outcome-capture`, merged `667d5de`, pushed).

## Compliance (pre-merge, independently verified by orchestrator)
- Prereg-first commit order verified (bd4fb3a → b613a68 → c00a21c → 1012197).
- Frozen V1 source untouched; a stray tracked `.pyc` under router_v1/ reverted.
- Suite re-run by orchestrator on the PRODUCTION interpreter (system python
  3.9): **238 passed, 1 skipped** (child's original run was on pyenv 3.11 and
  silently broke under 3.9 via a user-site `tests` package shadowing the repo
  namespace package — import fix committed 2e870aa).
- Black-box probe on scratch port 8766: 5 enforcement 400 shapes with frozen
  body + zero ledger writes; route→outcome 202; duplicate 409 / unknown 404 /
  invalid 400; prompt-edge 400 intact; per-shape counters exact (both-ids-
  missing bumps BOTH counters, per frozen prereg); missing_ids_logged pin-at-0;
  join tool self-test + real join (join_rate 1.0).

## Deploy
- Operator-approved `launchctl kickstart -k` → new PID 54445.
- /health carries additive blocks: `outcomes{logged,errors}`,
  per-shape `edge_rejections{...,missing_session_id,missing_message_id}`,
  `missing_ids_logged` — all zero at start.

## Live verification on 127.0.0.1:8765 (post-deploy)
- Enforcement: POST /route without ids → 400
  `{"error": "session_id and message_id are required"}`, no ledger write
  (telemetry.logged stayed 0 after the reject).
- Valid route with ids → 200, decision strong (conf 0.399 ≥ threshold 0.3),
  event_id issued, telemetry.logged 1, missing_ids_logged still 0.
- Envelope block unchanged and active (alpha 0.01, shadow) — V1 decision
  semantics untouched.
- Edge-400 (empty/whitespace prompt) behavior intact.

## What production now is
router-v1-frozen (threshold 0.30) + α=0.01 conformal envelope (record-only)
+ outcome capture (`POST /outcome`, schema 1.1.0, no prompt_id) + mandatory
session_id/message_id on /route. Join path: decision(event_id) ←→ outcome.

## Next steps (from operationalisation plan)
- Step 3: re-audit 109 stage-routing trace viability now that joinable
  outcomes + ids are enforced (expect TRACE_DATA_INSUFFICIENT until real
  organic traffic accumulates).
- Step 4: end-to-end operationalisation verification + final report.

## Verdict
**OUTCOME_CAPTURE_DEPLOYED** — live-verified. Spend $0.