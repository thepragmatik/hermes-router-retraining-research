# 101 Edge-Fix Deploy Verification — 2026-09-09

Orchestrator-executed deploy + live re-verification of the preregistered
edge-prompt rejection contract (`results/101/EDGE_REJECTION_PREREG.md`,
prereg commit `777d8f8`, erratum `5c773ee`).

## Deploy
- Branch `fix/101-edge-prompt-rejection` merged at `dbb75ff` after independent
  compliance checks: `git diff` vs research branch showed 0 changed files under
  `specs/`, 0 under `evidence/`, commit order prereg → erratum → code.
- Full suite re-run by orchestrator in the fix worktree: **197 passed, 0 failed**
  (160.66 s).
- Production restarted via `launchctl kickstart -k
  gui/$(id -u)/com.rath.router-shadow-v1` (new PID 38003; note: `launchctl
  kick` is not a valid subcommand on this macOS build — `kickstart` is).
- Health after restart: `status ok, enabled true, engine router-v1-frozen,
  telemetry logged 0, errors 0`.

## Live edge probes (127.0.0.1:8765, post-restart)
| # | Payload | Result |
|---|---|---|
| 1 | `{"prompt": ""}` | HTTP 400, `{"error": "empty or missing prompt"}` |
| 2 | `{}` (missing prompt) | HTTP 400, same body |
| 3 | `{"prompt": "   "}` (whitespace) | HTTP 400, same body |
| 4 | `{"prompt": 123}` (non-string) | HTTP 400, same body |
| 5 | `{"prompt": null}` | HTTP 400, same body |
| 6 | valid prompt (`traffic_stratum: edge-fix-verify-v2`) | HTTP 200, decision `strong`, confidence 0.6079, threshold 0.3, engine `router-v1-frozen` — unchanged envelope |

- No model call and no ledger write for probes 1–5: `telemetry.logged`
  stayed at 0 through all five 400s; after the valid control it read exactly
  1 (the control alone). `errors` 0 throughout. This is the prereg's
  no-side-effect contract, verified live.
- Pre-fix behavior (this morning) routed + logged empty/missing prompts with
  `prompt_hash = e3b0c44298fc` (sha256 of empty string) — see
  `results/101/LIVE_VERIFICATION.md` edge cases (wording corrected by
  orchestrator: the original report said `null`).

## Verdict
**EDGE_FIX_DEPLOYED** — production behaves exactly per the frozen prereg.
Spend: $0. Frozen V1 internals untouched. Ledger remains local-only
(gitignored, untracked per operator policy).
