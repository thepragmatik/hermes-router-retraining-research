# 105 Envelope Deploy Verification — 2026-09-09

Orchestrator-executed production deploy of the preregistered conformal
safety envelope (`results/105/ENVELOPE_DEPLOY_PREREG.md`, prereg `9152228`,
erratum `48995b2`, branch head `ca0c631`, merged `f343854`).

## Compliance (independent, pre-merge)
- `git diff` research..feat/105-envelope-deploy: 0 changed files under
  `specs/`, `evidence/`, and `router_v1/` (frozen V1 untouched).
- Commit order prereg → erratum → code → wiring → sanity: verified via
  `git log --reverse`.
- Full suite re-run by orchestrator in the worktree: **234 passed** (275.8 s)
  = 197 baseline + 23 unit + 14 service.

## Deploy
- Merged at `f343854`; production restart via
  `launchctl kickstart -k gui/$(id -u)/com.rath.router-shadow-v1`
  (new PID 45811).
- Flag flip: `router_config.yaml` `envelope_enabled: false → true`
  (operator-authorized), second restart, new PID 45811 serving flag ON.

## Live verification on 127.0.0.1:8765 (post-flip)
- `/health` now carries the envelope block: `enabled true, mode shadow,
  alpha 0.01, state active`, zero alarms (`ks_fire 0, risk_breach 0,
  load_failed 0, error 0`), action counts present.
- Control route: V1 decision `strong`, confidence 0.551, threshold 0.3 —
  **unchanged envelope semantics** — plus record-only envelope block
  (`action: escalate-strong`, `threshold_used: 0.8243549466133118` =
  the α=0.01 frozen CP threshold).
- Edge rejection intact: empty prompt → HTTP 400
  `{"error": "empty or missing prompt"}`, no ledger write.
- `telemetry.logged` delta exactly 1 (the control only); errors 0.
- Child's own live sanity (test port, 1,500 routes): accepted 327 ==
  offline expectation exactly, risk 0.0092 ≤ α 0.01 (S1), k=3 ≤ 6
  critical (S2, p=0.64), KS 0 false fires — evidence
  `results/105/live_sanity_evidence.json`.

## Known disclosure (from frozen prereg §7)
Sanity slice (seed-10 eval segment) overlaps Stage-0 fold rows under other
permutations; no fully-untouched row subset exists. Slice is independent of
the deployment artifact (seeds 0–9 folds). Stated in prereg, not a gate
weakening.

## Verdict
**ENVELOPE_DEPLOYED** — production (router-v1-frozen, threshold 0.30) now
runs with the α=0.01 conformal envelope in shadow/record-only mode: cost
savings 55–60% available, risk bounded ≤ α, alarms armed. Spend $0.
