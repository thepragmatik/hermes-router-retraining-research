# V1 Baseline — Shadow Log Gaps (documented 2026-09-08, baseline tag pending)

The V1 router (`router_v1/`, engine `v1_mf_router`, version `router-v1-frozen`,
threshold 0.30) is the frozen baseline artifact. It is correct and untouched.
What follows are gaps in the SHADOW LOGGING wrapper around it, found and
verified on 2026-09-08. No fix is applied in this baseline — fix directions are
recorded, code changes are deliberately deferred to a new prereg.

## Evidence base

- Log: `evidence/shadow/shadow_log.jsonl` — 67 rows through 2026-09-08T06:00Z
  (68 by baseline commit; one probe row added during gap verification),
  2026-09-06T09:25:39Z → 2026-09-08, 61 strong / 6 weak (pre-baseline),
  threshold 0.3, engine `router-v1-frozen`. ALL rows carry `prompt_id: 0`
  (one distinct probe prompt; rows 1-3 identical confidence 0.558 seconds
  apart = health probes).
- Boundary check (log is correct where it exists): row at confidence 0.2999 →
  weak; row at 0.3472 → strong. Threshold behaves exactly.
- Code: `router_v1_cli.py:69` (hardcoded prompt_id), `router_v1_cli.py:8`
  (disabled-state schema prompt_id came from), `router_v1_cli.py:71-79`
  (best-effort append, hardcoded `evidence/shadow/` path),
  `router_shadow.py` do_POST (routes + sends only — no logging).
- Live service: launchd `com.rath.router-shadow-v1`, 127.0.0.1:8765, health
  ok, enabled, kill-switch re-verified both states 2026-09-07.

## Gaps

- G1 — `prompt_id` hardcoded 0 (`router_v1_cli.py:69`): never incremented,
  never wired to any prompt identity. Every logged decision is unlinkable to
  the prompt that produced it.
- G2 — the HTTP service never logs: the launchd shadow service (the production
  traffic path) only routes and returns; the append code exists only in the
  CLI. Live service traffic leaves NO decision record at all. The logged rows
  are CLI-era health calls, not production data.
- G3 — no prompt text or content hash in the log: decisions cannot be
  deduped, joined to prompts, or resurrected later for training data.
- G4 — no outcome capture: the routed model's answer and its correctness are
  never recorded, so log rows cannot become training/fine-tuning data.
- G5 — volume unrepresentative: 67 rows at baseline, one distinct prompt, 91%
  strong share (vs 77% strong on the 3,626-prompt eval). Health signal only.
- G6 — config cosmetic drift (found dirty, normalized at this baseline):
  threshold written `0.3` vs canonical `0.30`, kill-switch comments dropped.
  Float guard verified intact (drift 0.31 → CLI exit 2). Non-issue, recorded.

## Consequence

The cents spent running the shadow so far bought uptime/kill-switch
verification (real operational value) but ZERO usable training data — by
construction of G1-G4, not by volume alone.

## Fix direction (deferred; needs fresh prereg before any code)

- Log `prompt_sha256[:12]` (content hash — dedupe, join, verify, no text
  stored), proper batch-mode prompt_id increment, caller-supplied
  `session_id`/`message_id` when the caller has them (resurrection join).
- Service-side logging parity with the CLI (close G2).
- Outcome join later: routed model's answer + correctness on a sampled
  subset (that capture is a separate capture pipeline, not the log's job).

Baseline tag: `v1-baseline-2026-09-08` (commit recorded in MISSION_LOG).
Research next steps are tracked in the R8 plan, separate from this baseline.
