# MISSION_LOG — Stackable routing pivot

**Mission start:** 2026-09-06 (this file created at Phase A of the pivot execution).
**Canonical spec:** `STACKABLE_ROUTING_MISSION.md` (ACTIVE, 2026-09-06).
**Repository state at mission start:** branch `main` @ `356f943` (plus Phase A0 import
commit `7e8a7be`, tag `router-v1-frozen`).

## Operator-reported historical failures (do NOT rerun unchanged)

From `research/phase0` branch (exp000–exp013, all preregistered, $0–$0.34 spend):

| Family | Verdict (committed on `research/phase0`) |
|---|---|
| exp003/FEV sparse-label acquisition | FALSIFIED at 0.5–5% budgets |
| exp004 one-sided PU / judge-derived labels | CLOSED (stage B' defprobe precision 1.0 @ 7.5% recall only) |
| exp005 semantic-cluster routing / cost frontier | FAILED (sanity APGR 0.6459 confirmed; G3 only at 100% strong) |
| exp010 embedding ensemble | No effect beyond noise (all deltas <= 0) |
| exp009 entropy-guided acquisition | FALSIFIED (C1 0.6139 vs C0 0.6277) |
| exp011 pool swap (binarized anchors) | ARM CHOICE PARTIAL |
| exp012 cascade regret | CASCADE-CLOSED (oracle regret > 0 all lambda; proxy degenerate) |
| exp013/013a pair coherence | Amended then closed on `research/phase0` |

Later judge-label retrain of the MF router (v2) FAILED its G-PRIMARY gate and was
auto-reverted to v1 (transfer-bundle commit `f2e8674`).

## Mounted local artifacts and hashes

| Artifact | sha256 |
|---|---|
| `~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl` (36,497 rows; 11 model score cols + responses/costs; 86 eval families) | `ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d` |
| `~/transfer-bundle/analysis/winrate_table.parquet` (split: train 29,193 / val 3,626 / test 3,678) | recorded in B-phase evidence |
| `router_v1/mf_router.pt` (tag `router-v1-frozen`) | `db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7` |
| `router_v1/route.py` | `b9fa430d300e3a1693f6bedfad51926a20a5192ebd46a4dfd07d6a877a8aeb46` |

The 5-shot and raw RouterBench pickles are mounted but are NOT substitutes for the
0-shot artifact in exact-pair work (DATASETS.md) and never carry the sealed test split
into experiments.

## Train / pivot-holdout / validation counts

- train 29,193 · val 3,626 (historical, already consulted by prior experiments) ·
  test 3,678 (SEALED — never load).
- Pivot development: train-only CV or deterministic train-derived holdout (seed 42,
  protocol frozen in `experiments/PIVOT_PROTOCOL.md`).

## Validation exposures (append BEFORE looking at qualification results)

| # | Date | Purpose | Preregistered threshold | Result ref |
|---|---|---|---|---|
| (none yet in this mission) | | | | |

Historical context (previous mission, for the record only): v1 val APGR 0.6459;
v1 test APGR 0.6528.

## Model / provider / version inventory

- Historical weak: `mistralai/mistral-7b-chat`; historical strong/frontier:
  `gpt-4-1106-preview` (labels stored in RouterBench 0-shot).
- Screening pool (stored score columns): WizardLM-13B-V1.2, claude-instant-v1,
  claude-v1, claude-v2, gpt-3.5-turbo-1106, meta/code-llama-instruct-34b-chat,
  meta/llama-2-70b-chat, mistralai/mixtral-8x7b-chat, zero-one-ai/Yi-34B-Chat.
- Router encoder: `BAAI/bge-small-en-v1.5` (sentence-transformers 5.1.2, torch 2.8.0).
- Current-candidate screening: `costs/model_prices.json` snapshot (web-sourced,
  dated) + any free public stored results per `DATASETS.md` Tier B.

## Current price snapshot source / date

`costs/model_prices.json` — snapshot date 2026-09-06, sources per entry (OpenRouter /
provider price pages). Screening evidence only; prices move.

## Environment / package versions

- macOS host, python3 (system 3.9 + project venv as used per script), pandas/numpy
  present, torch 2.8.0, sentence-transformers 5.1.2. Router inference CPU-only,
  verified live 2026-09-06.

## Spend to date

$0.00 (cap $5.00). All experiments so far use stored labels only.

## Active hypotheses

- H-P0: the historical weak tier is economically obsolete vs a current cheap model
  (to be tested from stored/public evidence first).
- H-P1: extra cheap samples / disagreement can replace a material share of frontier
  calls (bounded by stored-data feasibility).
- H-P2: deterministic verifiers can safely accept a useful subset of weak answers.
- (further hypotheses preregistered before each phase; see experiments/)

## Decisions and stop reasons

- 2026-09-06: V1 frozen at tag `router-v1-frozen` as read-only Tier-0 prior; pivot
  mission builds on it (P0 baseline + composition reference), per operator direction.
- 2026-09-06 (B1): baseline reproduction PASS — all six frozen metrics exact
  (weak 0.2289 / strong 0.6448 / always-strong APGR 0.6459 / v1 routed 0.6395 /
  frac_strong 0.7686 / PGR 0.9874). Note: APGR integrates PGR over the call-fraction
  axis (per eval_apgr.py); the threshold-axis variant reads 0.6096 and is WRONG.
- 2026-09-06 (P0): keep historical weak tier as primary cheap tier; Yi-34B-Chat
  carried as mid-tier/heterogeneous-sample candidate (best rescue-per-dollar
  0.4702 @ 4.05× weak cost); claude-v2 + code-llama-34b + llama-2-70b rejected
  (kill rules); naive disagree-cascade (PGR 0.7299) does not beat v1 (PGR 0.9874).
  Pool-currency question (current cheap models not in stored pool) logged as open
  follow-up requiring Tier B public results or SPEND_GO-gated calls.
- 2026-09-06 (C/P1+P2): prereg frozen (d8af031) BEFORE holdout scoring. Two harness
  bugs found and fixed dev-side before the final single holdout pass (Series-vs-scalar
  verifier call; anchor cost-scaling); first two passes VOID, fixes in
  results/BINARIZATION_NOTE.md. Binarization convention verified = build_winrate.py
  fillna(0).astype(int) truncation (partial-credit columns; convention preserved).
  Results: P1b disagreement-escalate KILLED (acc -0.0078, cost +22.1% vs v1 on
  holdout); P1c verifier-gated pair KILLED (acc 0.2545 vs 0.6475); P2 all four
  verifier families FAIL precision gate (best 0.67 vs gate 0.90; mbpp has zero
  asserts, no JSON blocks). P1a oracle ceiling: +6.7pp acc at -39.8% cost vs v1 —
  headroom target for P3/P4 runtime trigger, not deployable. Spend $0.
  Next: Phase D = P3 internal confidence (trigger must capture >=50% of oracle lift).
- (phase decisions appended as the mission proceeds)
