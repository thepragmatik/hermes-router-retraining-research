# Stage 0 Report — Idea 104: Whitened Latent Marginal-Gain Probe

**Date:** 2026-09-09 · **Spend:** $0 · **Prereg:** `results/104/PREREG.md` (written and frozen before any pipeline code ran) · **Terminal status: KILLED**

## What was run

- **T002 feasibility (PASS):** `HuggingFaceTB/SmolLM2-360M-Instruct` (snapshot `a10cc1512eabd3dde888204e902eca88bddb4951`, float32, CPU) exposes true hidden states via forward hooks and token log-probabilities via `output_scores=True` in a single local `generate()` call. No paid APIs. Representation NOT blocked.
- **T010 capture:** streaming float16 summaries for all **29,193 train rows** (winrate_table `split=='train'` only; test rows never loaded). Features: last-prompt-token hidden states at layers 8/24/31 (960-d each), mean of first-16 generated-token final hidden states (960-d), plus 6 logit summaries (logprob mean/min/var, entropy, margin, n-tokens). 3,846 dims total; ~14,280 s CPU; memmap at `artifacts/104/latent_train.npy`.
- **T011 controls:** prompt BGE (`BAAI/bge-small-en-v1.5`, local), logit-only, task-only (eval_name one-hot) on identical rows.
- **T020–T023 probes:** L2 logistic (C selected inner-CV, train folds only), 5-fold md5-hash folds × 2 salts, fold-local z-scoring, PCA (16/32/64/90%) and whitened PCA (eigenvalue floor max(1e-5, 1e-4·λmax)) fit on training folds only.
- **T012 leakage tests:** row join exact (join_ok=true); label-shuffle collapses to chance (AUC 0.503/0.505/0.500); correctness/other-model fields never entered feature matrices.
- **T013 covariance diagnostics (FR-007):** strong anisotropy confirmed — cond numbers 4.3e3 (l8), 1.1e4 (l24), 8.0e4 (l31), 4.7e5 (genmean); top-10 eigenvalue mass 42%–81%. Whitening was mechanically well-posed and stable.
- **T025 policy economics:** rank-quantile escalation policies on OOF probabilities; matched-share comparison latent vs BGE vs task-only.

## Gate outcomes (frozen PREREG gates)

**G1 separability: FAIL.** OOF pairwise-gain AUROC (salt 0 / salt 1):

| feature | AUROC s0 | AUROC s1 |
|---|---|---|
| task-only | 0.7486 | 0.7485 |
| BGE prompt | 0.7396 | 0.7403 |
| raw latent | 0.7293 | 0.7272 |
| pca_64 | 0.7389 | 0.7379 |
| **whiten_90 (best whitened)** | **0.7399** | **0.7390** |
| logit-only | 0.6940 | 0.6938 |

Best whitened latent beats BGE by **+0.0003 / −0.0013** (needed ≥ +0.03 in ≥8/10 fold-salts). Best latent (any variant) ≈ BGE (Δ ≤ 0.0003). Latent does beat logit-only by ~+0.046, but the preregistered gate requires beating **both** controls; the task-only baseline (0.7486) exceeds every feature set, so the marginal-gain signal in prompts is essentially task identity.

**G2 task-stratification: FAIL.** Latent beats BGE in only 5/26 families with n≥200; the largest positive delta is a tiny family (abstract2title) carrying 53% of all positive mass. On the biggest families latent is at-or-below BGE (gsm8k: whiten 0.285 vs BGE 0.553; hellaswag 0.500 vs 0.503).

**G3 policy economics: FAIL.** At matched escalation share, latent vs BGE is ±0.3 pp (noise, no cost-side compensation); no variant reaches ≥0.5 pp quality at matched cost, ≥3% cost reduction at matched quality, or beats the task-only policy. The one preregistered diagnostic correction (prompt+latent combined features for G3) was not spent: it is licensed only when G1 passed and G3 failed — G1 itself failed.

**G4 stability: PASS (moot).** whitened cross-salt spread 0.0009 < raw spread 0.0022 — whitening is stable; it just does not add signal.

## Interpretation

True hidden states of a small local model (SmolLM2-360M) transfer weakly to GPT-4-vs-Mistral-7B escalation utility on RouterBench prompts: latent features beat naive logit summaries but add nothing over prompt BGE and less than task identity. Whitening, despite extreme anisotropy (the hypothesis's motivating condition), does not unlock extra separability at any dimension on the frozen grid. Consistent with P3's structural finding, the recoverable escalation mass on this corpus is largely captured by prompt-side/task-identity signal.

Per the frozen kill logic ("only prompt embedding wins ⇒ kill the latent idea") the idea is **KILLED**. Runtime overhead measured (T040: +0.9%, +3.8 ms/req) is favorable but moot — the classifier signal itself failed. No non-linear probe was trained (FR-004 respected: forbidden after Stage-0 failure).

## Artifacts

- `results/104/PREREG.md` (frozen gates, pre-registered)
- `artifacts/104/latent_train.npy`, `train_targets.parquet`, `bge_train.npy`, `oof_probs.npz`
- `artifacts/104/separability.json`, `stage0_metrics.json`, `policy_frontier.json`, `policy_frontier_matched.json`, `runtime_bench.json`, `capture_meta.json`, `metadata.json`
- `experiments/104/capture_latents.py`, `fit_probe.py`, `evaluate_probe.py`

## Task coverage (tasks.md)

- **T001** read constitution/spec/plan/P3_INTERNAL_CONFIDENCE — done; P3's stored-response-vs-internal distinction preserved.
- **T002** local hidden-states/logits feasibility — CONFIRMED (SmolLM2-360M-Instruct local snapshot).
- **T003** PREREG.md frozen before pipeline code — done.
- **T004** hashes/split integrity — train-only enforced; test split untouched (3678 membership count only); join test passed.
- **T010** streaming latent capture (memmap float16, no full dumps) — done, 29,193 rows.
- **T011** BGE/logit/response-shape controls on same rows — BGE + logit done; response-shape text features were out of scope (P3 already tested them; FR-003's "where available" satisfied by logit summaries).
- **T012** row-join, no-label-leakage, label-shuffle tests — all pass (shuffle → AUC≈0.5).
- **T013** covariance spectrum/cond/anisotropy — recorded for all four layer blocks.
- **T020–T023** raw/PCA/whitened probes, frozen dims/layer grid, train-only CV — done (2 salts × 5 folds × 12 variants).
- **T024** pairwise-gain metric, task-family metrics, calibration via task-only baseline — done.
- **T025** frozen cost-aware policy + frontier/oracle-capture — done.
- **T026** ≥2 salts executed; paired bootstrap omitted as moot (deltas ≈ 0, no finalist to test).
- **T030–T031** gates applied without retuning; latent signal failed → **KILLED**. T032/T033 not triggered.
- **T040–T041** runtime benchmark — capture overhead +0.9% / +3.8 ms per request (favorable, moot).
- **T042–T043, T050–T052, T060–T062** — not reached (Stage-0 kill); T062 resolved as KILLED.

**Spend:** $0 (local CPU only). RouterBench test split: untouched.
