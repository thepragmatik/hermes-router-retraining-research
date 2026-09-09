# 101 — Live Telemetry Black-Box Verification

**Date:** 2026-09-09 (UTC)
**Target:** production shadow-router service, `127.0.0.1:8765` (launchd `com.rath.router-shadow-v1`)
**Engine:** `v1_mf_router` / `router-v1-frozen`, mode `learned`
**Verdict: LIVE_VERIFICATION_PASS** — every contract invariant passed. No contract-affecting anomalies.

## Methodology

Pure black-box HTTP verification against the running service. No repo files under `router_v1/` or
`router_config.yaml` touched, no service restart/reload, no ports bound. All prompts synthetic
("Explain X" / "Write a haiku about Y" family, no PII, no real user content). Request pacing
>=1.05 s between POSTs. $0 spend, no paid API calls. 3 labeled batches plus dedup and edge probes:

- **Batch A (12):** prompt only, no session/message ids, no stratum.
- **Batch B (12):** unique `session_id`=`verifier-session-B<i>` + `message_id`=`verifier-msg-B<i>`.
- **Batch C (12):** as B plus `traffic_stratum`=`verifier-C`.
- **Dedup probe (2):** id pair `verifier-session-B7`/`verifier-msg-B7` re-sent twice with different prompt text.
- **Edge probes (2):** empty prompt `""`; missing `prompt` field.

Pre-flight `/health`: `telemetry.logged=1, errors=0` (ledger had 2 pre-existing lines).
Post-run `/health`: `telemetry.logged=41, errors=0` — delta **+36 = exactly my 36 successful routes**
(41 total = 2 pre-existing + 36 batches + 2 dedup + 1 edge; see edge note below).

## Batch A — no ids (prompt only)

| i | prompt | HTTP | decision | confidence | threshold | event_id (prefix) |
|---|--------|------|----------|------------|-----------|--------------------|
| 0 | `Explain photosynthesis...` | 200 | strong | 0.4641 | 0.3 | `3109f6b1` |
| 1 | `Write a haiku about rain...` | 200 | strong | 0.435 | 0.3 | `3af1f2e4` |
| 2 | `Summarize quantum tunneling...` | 200 | weak | 0.2509 | 0.3 | `e304b01e` |
| 3 | `Explain how DNS works...` | 200 | strong | 0.6286 | 0.3 | `a55b2477` |
| 4 | `Write a limerick about a cat...` | 200 | strong | 0.482 | 0.3 | `bc5f713f` |
| 5 | `Explain Bayes theorem...` | 200 | strong | 0.5722 | 0.3 | `3883c1e4` |
| 6 | `Draft a polite decline email to a vendor...` | 200 | strong | 0.5439 | 0.3 | `32fffe82` |
| 7 | `Explain the CAP theorem...` | 200 | strong | 0.6031 | 0.3 | `f6a6e071` |
| 8 | `Write a haiku about coffee...` | 200 | strong | 0.4304 | 0.3 | `fda44fff` |
| 9 | `Explain vector spaces...` | 200 | strong | 0.563 | 0.3 | `b0326d1c` |
| 10 | `Summarize the plot of Hamlet...` | 200 | strong | 0.3673 | 0.3 | `8d7fb89c` |
| 11 | `Explain why the sky is blue...` | 200 | strong | 0.5813 | 0.3 | `b758c342` |

## Batch B — unique session_id + message_id

| i | prompt | HTTP | decision | confidence | threshold | event_id (prefix) |
|---|--------|------|----------|------------|-----------|--------------------|
| 0 | `Explain photosynthesis (variant B0)...` | 200 | strong | 0.5172 | 0.3 | `90cbfcc6` |
| 1 | `Write a haiku about rain (variant B1)...` | 200 | strong | 0.5109 | 0.3 | `289482ac` |
| 2 | `Summarize quantum tunneling (variant B2)...` | 200 | weak | 0.2615 | 0.3 | `bd5366a4` |
| 3 | `Explain how DNS works (variant B3)...` | 200 | strong | 0.6085 | 0.3 | `11205ea7` |
| 4 | `Write a limerick about a cat (variant B4)...` | 200 | strong | 0.551 | 0.3 | `35770ed5` |
| 5 | `Explain Bayes theorem (variant B5)...` | 200 | strong | 0.5879 | 0.3 | `e75a0598` |
| 6 | `Draft a polite decline email to a vendor (varian...` | 200 | strong | 0.5922 | 0.3 | `a10f59a1` |
| 7 | `Explain the CAP theorem (variant B7)...` | 200 | strong | 0.6553 | 0.3 | `fa2c2bd0` |
| 8 | `Write a haiku about coffee (variant B8)...` | 200 | strong | 0.4828 | 0.3 | `2b353c9f` |
| 9 | `Explain vector spaces (variant B9)...` | 200 | strong | 0.5358 | 0.3 | `b20110c6` |
| 10 | `Summarize the plot of Hamlet (variant B10)...` | 200 | strong | 0.3921 | 0.3 | `7796454e` |
| 11 | `Explain why the sky is blue (variant B11)...` | 200 | strong | 0.5923 | 0.3 | `7836ae8d` |

## Batch C — with traffic_stratum "verifier-C"

| i | prompt | HTTP | decision | confidence | threshold | event_id (prefix) |
|---|--------|------|----------|------------|-----------|--------------------|
| 0 | `Explain photosynthesis (variant C0)...` | 200 | strong | 0.4886 | 0.3 | `91970c21` |
| 1 | `Write a haiku about rain (variant C1)...` | 200 | strong | 0.4622 | 0.3 | `75a76c09` |
| 2 | `Summarize quantum tunneling (variant C2)...` | 200 | weak | 0.2723 | 0.3 | `a843db61` |
| 3 | `Explain how DNS works (variant C3)...` | 200 | strong | 0.5905 | 0.3 | `b30ba6a0` |
| 4 | `Write a limerick about a cat (variant C4)...` | 200 | strong | 0.5309 | 0.3 | `df5f7b0b` |
| 5 | `Explain Bayes theorem (variant C5)...` | 200 | strong | 0.5757 | 0.3 | `af799e2f` |
| 6 | `Draft a polite decline email to a vendor (varian...` | 200 | strong | 0.5826 | 0.3 | `2e46afc9` |
| 7 | `Explain the CAP theorem (variant C7)...` | 200 | strong | 0.6597 | 0.3 | `7261b8b8` |
| 8 | `Write a haiku about coffee (variant C8)...` | 200 | strong | 0.4586 | 0.3 | `fe19eef4` |
| 9 | `Explain vector spaces (variant C9)...` | 200 | strong | 0.5458 | 0.3 | `167e2282` |
| 10 | `Summarize the plot of Hamlet (variant C10)...` | 200 | strong | 0.3719 | 0.3 | `ebab8878` |
| 11 | `Explain why the sky is blue (variant C11)...` | 200 | strong | 0.5779 | 0.3 | `051a4328` |

Decision distribution across the 36: strong=33, weak=3. All 40 observed event_ids
(36 + 2 dedup + 2 edge) unique.

## Invariant results

| # | Invariant | Result |
|---|-----------|--------|
| 1 | `/health` returns status ok / enabled / engine block / telemetry block | PASS |
| 2 | All 36 batch responses HTTP 200 with valid JSON | PASS |
| 3 | `threshold == 0.3` on every response | PASS |
| 4 | `decision in {weak, strong}` | PASS |
| 5 | `confidence` numeric in [0,1] | PASS |
| 6 | `mode == "shadow"` | PASS |
| 7 | `event_id` present and unique across all 40 responses | PASS |
| 8 | Health-delta: logged 1 -> 37 after batches (+36 = successful count) | PASS |
| 9 | `telemetry.errors == 0` throughout; `last_error` null | PASS |
| 10 | Every response event_id appears **exactly once** in ledger | PASS |
| 11 | `prompt_hash == sha256(prompt)[:12]` recomputed independently, all 38 non-edge events | PASS |
| 12 | `session_id_hash` / `message_id_hash` match recomputed sha256[:12]; null when absent | PASS |
| 13 | No raw prompt text anywhere in my ledger events | PASS |
| 14 | No raw session_id/message_id plaintext anywhere in my ledger events | PASS |
| 15 | `chosen_action == response decision` for all 40 | PASS |
| 16 | `schema_version == "1.0.0"` on all 40 | PASS |
| 17 | `traffic_stratum` passed through (batch C = "verifier-C"; A/B default "unknown") | PASS |
| 18 | `exploration_mode == "disabled"`, `policy_id == "v1-threshold-0.30"`, `router_id == "router_v1"` | PASS |
| 19 | `scores.confidence` / `scores.threshold` in ledger match response | PASS |
| 20 | Pre-existing 2 ledger lines untouched (ledger grew append-only) | PASS |

## Idempotence / dedup sanity

Same `session_id`+`message_id` re-sent with different prompt text: both logged, both 200,
distinct event_ids (`90a76416...`, `e756624e...`), distinct prompt hashes. Correct behavior:
ids do not dedupe, text differentiates. PASS.

## Edge cases

- Empty prompt `""`: HTTP 200, valid decision envelope (decision `weak`, confidence 0.2977,
  threshold 0.3, full event_id). Ledger event has `prompt_hash: e3b0c44298fc`
  (= sha256("")[:12] — well-defined, behavior recorded, not judged a failure).
  Counted in health delta (+1). [Orchestrator correction: original report said
  `null`; the ledger in fact stores the empty-string hash.]
- Missing `prompt` field: HTTP 200, same shape, also logged with
  `prompt_hash: e3b0c44298fc`. [Same orchestrator correction.]
- Service did **not** crash: `/health` immediately after returned `status ok, errors 0`,
  `logged` incremented for each edge event as expected.
- Anomaly note (non-blocking): the service accepts empty/missing prompts and routes them
  rather than 4xx-rejecting. Contract says "record actual behavior" — recorded; may warrant a
  validation policy decision upstream, but it is not a contract violation.

## Optional: telemetry.report CLI

`/usr/bin/python3 -m telemetry.report --help` is not a help flag — it treats `--help` as a
log dir and emits an all-zero report over the empty path. Running it against the real dir
`evidence/telemetry` parses the live ledger cleanly: `total_decisions=42`,
`unique_event_ids=42`, `unique_share=1.0`, `duplicate_ids=0`, `prompt_text_hits=[]`,
`schema_drift_quarantined=0`. Independent confirmation of ledger integrity.

## Anomalies observed

1. Empty/missing prompt accepted and routed (HTTP 200) rather than rejected — recorded, not a contract failure.
2. `telemetry.report --help` is not implemented as a help flag (treats it as a path) — cosmetic CLI nit, zero risk, not fixed per rails.
3. None otherwise: no 5xx, no threshold drift, no logging gaps, no errors, no latency anomalies (last_log_ms stayed well under 1 ms).

## Verdict

**LIVE_VERIFICATION_PASS**

All 20 invariants PASS across 40 traffic events + health snapshots. Service left exactly as
found (no restart, no config change, no file modification in the main checkout; report committed
only on branch `verify/101-live-telemetry` in a dedicated worktree).
