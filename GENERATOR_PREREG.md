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

## R1 verdict (2026-09-07, post-run) — FAIL; R1b amendment

R1 executed under this prereg (n=100, cap $0.10, actual ledgered spend
$0.00092). Result: **GATES FAILED** — verifiable yield 19% (gate >=60%),
weak_ok 0, both_fail 17/19. Postmortem (all from evidence artifacts):

1. **FATAL, run-invalidating: the weak tier was unreachable.** Every weak
   call to `qwen/qwen3.7-flash` failed with HTTP 404 under the operator's
   OpenRouter key (provider allowlist: z-ai / alibaba / deepseek /
   deepinfra, per the 2026-09-04 judge-calibration finding). The catalog
   lists the id; this account cannot route it. All 19 strong calls were
   fallback work against a dead weak tier; **no R1 label is valid** and no
   R1 metric is interpretable as model quality. Ledgered strong spend
   $0.00092 is written off as calibration.
2. Generator strict-parse rejected 72/100 as not_json; inspection showed
   fenced/markdown-wrapped JSON. Fixed in 58153eb (one bounded retry on
   fenced blocks + brace-span), test added; re-measured in R1b.
3. Ledger recorded 19/19 weak rows as `unpriced` (0 tokens billed) —
   consistent with the 404s; the pricing cache resolves the id but the
   account cannot route it. Cache correctness vs routeability are
   different gates; R1b adds a 2-call smoke before any batch.

### R1b amendment (pre-registered before execution, this row)

- Weak tier fallback: `z-ai/glm-5.3-flash` ($0.075/$0.25 per M,
  allowlisted and live-verified on this account). Strong tier unchanged:
  `deepseek/deepseek-v4-flash`.
- Added pre-flight gate: 2-call smoke per tier before each batch; any
  404/error aborts the rung at $0 (< 20 calls).
- Gates for R1b unchanged from R1: yield >= 60%, dedup reject <= 30%,
  cap $0.10. n=100.
- Note: with glm-5.3-flash weak and v4-flash strong, expected spread is
  1.19x/0.71x — labeling economics degrade vs pair B (est. $0.18/1k) but
  label semantics are unchanged; deployment-pair decision stays the
  post-R2 open operator gate.

## R1b outcome (2026-09-07, post-run) — frozen gates PASS; economics caveat logged

Executed per amendment: n=100, weak=`z-ai/glm-5.3-flash`, strong=`deepseek/deepseek-v4-flash`,
cap $0.10. Realized spend $0.00937 (9.4% of cap). Separated from R1 by ts-filter
(R1's last dead-row ts 11:31:54Z); NOTE: batch_id was reused (`r1_b8919`), so the
aggregate ledger_report mixes both runs — the honest split is ts-filtered (below).

R1b-only (ts-filtered from ledger.jsonl):
- generated ~98 -> items accepted 79 (item yield 81%; gate >=60% PASS)
- parse rejects 9 (was 72 in R1; fenced-JSON recovery fix effective)
- self-verifier rejects 10; dedup rejects 21 (~21%; gate <=30% PASS)
- labeled 79: weak_ok 16 (20%), escalated 64, strong_ok 7, both_fail ~56 (71%)
- usable labels 23/79 (29%); $/usable-label $0.00037 (~$0.37/1k vs $0.12-0.18/1k estimate)
- weak tier billed real tokens on every call (R1's zero-token signature gone)

Verdict: frozen R1 gates (yield, dedup) PASS. Caveat for R2 design: 71% both_fail
means the generator's questions are mostly unsolvable as-verifier-checked —
generator quality, not pipeline plumbing, is now the bottleneck. Escalation rate
81% made strong calls dominate cost. Pair-B economics ($0.12/1k) remain
unreachable on this account until qwen3.7-flash is routeable (allowlist).

## R2 prereg (2026-09-07, pre-registered before execution)

Root causes (from the R1b postmortem; plan reference: `.hermes/plans/
2026-09-07_231651-r2-generator-quality-fix.md`, workspace-relative path):
1. generate_items.py:242 sent GEN_PROMPT raw — placeholders never substituted
   (no .format call in module); taxonomy conditioning never reached the model.
2. cascade_label.py ask() max_tokens=300 truncated 31/65 strong answers past
   the final-answer region (verified: completion_tokens==300 exactly).
3. No "Final answer:" instruction to labeler tiers; verifiers need that
   region for exact_match/numeric_tol extraction.

R2 changes: build_prompt(seed) rotation wiring (fix 1); max_tokens 700 +
ANSWER_FORMAT_SUFFIX in cascade_label._payload (fixes 2+3); routeability smoke
(smoke_tiers.py, 2 calls/tier, exit 3 abort) wired into run_rung.sh before
generation; salted batch ids.

Frozen gates for R2 (n=100, rung 2):
- item yield >= 60% (unchanged)
- dedup reject <= 30% (unchanged; threshold 0.85 unchanged)
- both_fail <= 35% (new — root-cause fix target; R1b was 71%)
- usable (weak_ok + strong_ok) >= 50% (new; R1b was 29%)
- $/usable-label <= $0.00025
- spend <= $0.10 cap (estimate ~$0.03 worst case at 700 strong tokens)

Pair: weak=z-ai/glm-5.3-flash, strong=deepseek/deepseek-v4-flash (same as R1b;
pair switch deferred to R3 — single-variable discipline). Routeability smoke
runs before generation; any tier failure aborts at <$0.001.
Operator approved execution + <$0.001 qwen probes (qwen3.5-flash-02-23,
qwen3.8-flash) 2026-09-07 ("go ahead").

## R2 outcome (2026-09-07, post-run) — 4/6 gates PASS; verdict: PARTIAL PASS

Executed exactly per this prereg: rung 2, n=100, weak=`z-ai/glm-5.3-flash`,
strong=`deepseek/deepseek-v4-flash`, cap $0.10, smoke-gated. Salted batch id
`r2_b1788835509_18671` (clean split from R1/R1b — no ts-filter needed; the
Task-4 fix worked as designed). Realized (from `r2_` ledger rows):

| gate | realized | frozen | verdict |
|---|---|---|---|
| usable (weak_ok + strong_ok) | 31/48 = 64.6% | >=50% | PASS |
| $/usable-label | $0.00018 | <=$0.00025 | PASS |
| dedup rejects | 3% | <=30% | PASS |
| spend | $0.00543 | <=$0.10 | PASS |
| item yield | 48/97 = 49% | >=60% | FAIL |
| both_fail | 17/48 = 35.4% | <=35% | FAIL (0.42pp) |

Root-cause fixes verified working: weak_ok 20%->60% (the dominant win: labeler
no longer truncates + asks for "Final answer:" lines); escalation rate 81%->40%
(strong calls 19 vs 82); $/usable-label $0.00037->$0.00018; unpriced calls 0.

Residual failures, honestly:
- Item yield fell 81%->49%: not_json rejects tripled (36/97). The formatted
  taxonomy-conditioned prompts push glm-5.3-flash off strict-JSON output more
  often (new domain/style heads change the output distribution). The strict
  parser's fenced-block recovery helps but does not fully cover it.
- both_fail 35.4% vs 35% gate: essentially at the line; the labeler-side fixes
  worked, the remaining both_fail is generator capability (questions whose
  single answer neither tier produces verbatim under exact_match).

Verdict per prereg discipline: PARTIAL PASS. Primary economics gates (usable,
$/label) PASS decisively; the two failing gates are generator-side, not
pipeline-side. R3 prereg must attack: (a) generator JSON compliance under
taxonomy conditioning (one-line system-message "STRICT JSON only" or
response_format=json_object if glm supports it), (b) exact_match brittleness
(consider normalized-token-set overlap as a verifier type in a NEW prereg —
never silently retune). Pair stays glm/v4-flash: qwen family confirmed blocked
(404 on qwen3.5-flash-02-23 AND qwen3.8-flash, 2026-09-07 smoke).

## R3 prereg (2026-09-07, pre-registered before execution)

Operator approved R3 ("yes, go ahead", 2026-09-07). Target: the two R2-failing
gates, both generator-side per the R2 outcome row.

Changes (and what is NOT changed):
1. Generator call gains a system message: "You output ONLY one raw JSON object.
   No prose, no markdown fences, no keys." (always on — additive instruction,
   no API-compat risk).
2. `response_format: {"type": "json_object"}` gated behind env `GEN_JSON_MODE=1`
   (glm-5.3-flash support unknown; an unsupported field would 400 and waste
   spend, so default OFF). If a R3 micro-probe shows it routes clean, a later
   rung may flip it; R3 runs with the system message only.
3. NO verifier retuning. exact_match brittleness is noted as a future lever but
   R3 attacks JSON compliance only — changing two variables would unattribute
   the outcome.

Frozen R3 gates (rung 3, n=100, cap $0.10, weak=glm-5.3-flash, strong=v4-flash,
same smoke gate, salted batch ids):
- item yield >= 60% (R2: 49%; not_json <= 20% of generated, R2: 37%)
- usable >= 50% (hold R2 level)
- both_fail <= 35% (hold)
- $/usable-label <= $0.00025 (hold)
- spend <= $0.10

Pre-registered interpretation: if yield gate passes but both_fail still trips,
R4 attacks exact_match brittleness via a NEW verifier type (normalized
token-set overlap) in a fresh prereg. If yield still fails, R4 switches
generator model (deepinfra catalog scan, same allowlist constraint).
