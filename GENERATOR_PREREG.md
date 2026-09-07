# GENERATOR_PREREG — Generator Pivot, Rung R0 → R1 (frozen 2026-09-07)

Preregistered BEFORE any spend. This document freezes the labeling pair,
label semantics, spend gates, and acceptance gates for the generator-pivot
factory (`experiments/gen_factory/`). Nothing in this file authorizes
spend by itself: R1+ requires the operator environment gates below.

## Hypothesis

Cheap, in-distribution generated items with **verifier-by-construction**
(deterministic exact-match / numeric-tolerance checks written into the
generation contract) can produce **usable cascade labels** for router
training at **< $0.01 per usable label** under the frozen pair below —
measured, not assumed, by `experiments/gen_factory/ledger_report.py`
(`cost_per_usable_label_usd`, the only decision metric).

## FROZEN labeling pair (operator decision 2026-09-07, catalog-verified)

Supersedes any pair named in plan 013.

| Role | OpenRouter id | Input $/M | Output $/M | Context |
|---|---|---|---|---|
| weak | `qwen/qwen3.7-flash` | $0.03 | $0.13 | ≥ 16k (catalog-verified 2026-09-07) |
| strong | `deepseek/deepseek-v4-flash` | $0.089 | $0.177 | ≥ 16k (catalog-verified 2026-09-07) |

**Catalog-drift note (2026-09-07):** the historical V1 pair is retired from
the OpenRouter catalog — `gpt-4-1106-preview` and `mistral-7b-chat` no
longer resolve. `deepseek-v4-flash-latest` exists ONLY as a tilde alias;
the **canonical id `deepseek/deepseek-v4-flash` is frozen** and must not be
swapped for the alias.

**Router-contract compatibility:** `cascade_label.py` env defaults remain
the V1-frozen pair (`mistralai/mistral-7b-chat` /
`openai/gpt-4-1106-preview`) so the V1 router contract is untouched. The
frozen pair above is passed via `WEAK_MODEL` / `STRONG_MODEL` env vars by
`run_rung.sh` — never by editing the module defaults.

**Pricing-cache step (required before R1 spend):** the pricing cache
(`evidence/gen_factory/model_pricing_cache.json`, untracked, regenerable)
is refreshed by the $0 public GET
`/usr/bin/python3 experiments/gen_factory/fetch_pricing.py`, which now
carries the `qwen_flash` role for the frozen weak id. The cache refresh is
an operator-run step (network access is operator-gated on this host);
ledger pricing and the spend gate read ONLY this cache, never hard-coded
prices.

## Label semantics (cascade)

- `weak_ok` = the WEAK model's answer passes the item's verifier.
- `need_strong` = weak failed AND the STRONG model's answer passes the
  verifier (strong called ONLY after weak failure — cascade order).
- **both-fail** = weak failed AND (no strong call OR strong failed).
  Recorded in the ledger, **excluded from `weak_ok`**, and reported
  separately (`both_fail_count` in `ledger_report.json`); the strata
  partition as `weak_ok + need_strong + both_fail == n_labeled`.
- Items are counted `n_labeled` = one weak labeling decision each; usable
  labels for the cost metric = `n_labeled`.

## Spend gates

| Rung | Cap | Authorization required | Notes |
|---|---|---|---|
| R0 | $0.00 | none | mock-only; zero network from suite |
| R1 | **$0.10**, pilot n=100 | `GEN_GO=1` AND `OPENROUTER_API_KEY` AND `SPEND_CAP_USD>0` | aborts (SystemExit) the instant ledgered spend reaches the cap |
| R2+ | set per-rung in a NEW prereg row before spend | same gates | rung ladder: no rung starts without the previous rung's gate PASS |

`run_rung.sh` refuses (exit 1, `REFUSED`) unless `GEN_GO=1` and
`SPEND_CAP_USD>0`; `cascade_label.py` additionally requires the API key.
The ledger is the single price source of truth (Wave-0 cache priced;
unpriced rows are flagged, costed $0, and counted — never silent).

## Acceptance gates for R1 (frozen; from plan 013 Task 6)

| Metric | Gate | Source |
|---|---|---|
| verifiable yield (generator output passing parse + verifier-executability) | **>= 60%** | plan 013 R1 gate |
| dedup reject rate | **<= 30%** | plan 013 R1 gate |
| spend | **<= $0.10** | plan 013 R1 cap |

R2 gates (frozen here for the record, executed only after a NEW prereg row
and operator go): verifier agreement with a 20-item hand-check **>= 90%**;
`need_strong` rate in the **40–80% band**. R3: complete 1,000-label batch
at **<= $1.50**. R4: requires a V2 prereg doc + operator sign-off.

**Measured-only metrics (no frozen threshold — reported, not gated):**
`cost_per_usable_label_usd` at R1 (sample too small to gate; the <$0.01/label
hypothesis is tested on R2+ aggregates), `both_fail_count`, unpriced call
count (any nonzero value is investigated, but is not an automatic gate),
latency. No threshold is invented for these.

## Dedup gate (frozen)

Cosine similarity **>= 0.85** reject, against ALL THREE sealed corpus
frames (`winrate_table`, `mf_val_frame`, `mf_test_frame`) AND in-batch
(duplicate generated items), via `BAAI/bge-small-en-v1.5`. Rejects are
logged (item_id + max_sim + source frame only — never prompt text).

## Deployment strong tier — OPEN operator gate (post-R2)

NOT decided here. Alternates with current catalog prices:

| Candidate | Input $/M | Output $/M | Notes |
|---|---|---|---|
| `deepseek/deepseek-v4-flash` (as-is, frozen labeling pair) | $0.089 | $0.177 | proven on this project (evidence-mode calibration PASS) |
| `qwen/qwen3-235b-a22b-2507` | $0.09 | $0.55 | cheaper input, pricier output |
| `deepseek/deepseek-v4-pro` | $0.955 | $1.911 | quality ceiling, ~10x cost |

Decision is deferred until R2 rung measurements exist; the deployment tier
is an explicit operator gate and is documented as OPEN, not pre-picked.

## Risks

1. **Catalog drift** — ids/prices move; mitigation: the pricing cache
   refresh step above + the 7-day freshness test; spend gate reads the
   cache, never hard-coded prices.
2. **Both-fail rate inflating strong spend** — every weak-failure costs a
   strong call; if the both-fail stratum is large, strong spend balloons
   while producing zero usable labels. Mitigation: cascade order (never
   call strong first), both-fail reported separately, R2 need_strong band
   gate (40–80%) halts before volume.
3. **PII posture** — no prompt/question text in the ledger or dedup logs
   (item_id only); `labels_batch*.jsonl` and `items_batch*.jsonl` carry
   question text but are LOCAL-ONLY (never committed; evidence/ is
   untracked). Generated question text is synthetic (no session content),
   but the no-user-text discipline still applies to every log.
