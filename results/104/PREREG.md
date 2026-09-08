# PREREG — Idea 104: Whitened Latent Marginal-Gain Probe (Stage 0)

**Frozen:** 2026-09-09 (AEST), BEFORE any pipeline code ran. Spend: $0. Test split SEALED (membership counts only: test=3678).

## Data contract

- Outcomes: `/Users/rath/transfer-bundle/analysis/winrate_table.parquet` (frozen split table; columns prompt, eval_name, split, strong_correct, weak_correct, cost_s, cost_w). **Train-only** rows (29,193) used for capture targets, CV, holdout. Test rows never loaded beyond the split-count above.
- Prompts: `/Users/rath/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl` (train rows, read-only), joined to winrate_table on exact prompt string.
- Target pair (frozen): strong = `gpt-4-1106-preview` (train mean cost 0.003293 ≈ cost_s mean 0.003289), weak = `mistralai/mistral-7b-chat` (train mean cost 4.57e-5 ≈ cost_w mean 4.6e-5).
- Target: pairwise marginal gain G = strong_correct − weak_correct (escalation utility). Labels strictly from winrate_table, never from model responses.

## Representation model (frozen)

- Model: `HuggingFaceTB/SmolLM2-360M-Instruct`, local snapshot in `~/.cache/huggingface/hub`, revision = frozen snapshot dir hash recorded in artifacts/104/metadata.json, dtype float32, CPU, greedy, max_new_tokens 16.
- Chat template: the model's own tokenizer template applied to the prompt text only.
- Frozen candidate layers (max 3, a priori): layer 8 (mid), layer 12 (late-mid), final hidden (layer 16, last before LM head) — SmolLM2-360M has 16 hidden layers.
- Token summaries (frozen): last-prompt-token hidden state per layer (pre-generation), and mean over the first 16 generated-token hidden states (final layer).
- Logit summaries: mean/min/variance of generated-token log-softmax max, mean entropy, logpro margin — computed from the same forward pass (no separate calls).
- Representation-transfer note (per plan.md): the representation model (SmolLM2) differs from the historical outcome models (GPT-4 vs Mistral-7B). This is explicitly a **representation-transfer test**; conclusions carry that caveat.

## Controls

1. Prompt BGE baseline: `BAAI/bge-small-en-v1.5` (local), prompt text only.
2. Logit/entropy summaries only.
3. Raw hidden summaries (z-scored, train-fold scaler).
4. PCA projection (frozen dims grid: 16/32/64, 90% variance) fit train-fold only.
5. Whitened PCA `Z=(H−μ)VΛ^(−1/2)`, eigenvalue floor = max(1e-5, 1e-4·λ_max), fit train-fold only.
6. Prompt BGE + winning latent summary (optional).

Probe: regularized logistic regression (L2), C grid {0.03,0.1,0.3,1,3} selected by inner CV on train folds only. No nonlinear models.

## Protocol

- 5-fold CV, md5-based row-hash fold assignment, fixed fold seed 104, 3 salt variants for shuffles/robustness.
- Capture: single pass over 29,193 train prompts, streaming float16 summaries to disk (no full activation dumps).
- Label-shuffle control must collapse to chance (AUC ≈ 0.5). Task-only baseline (eval_name one-hot) quantifies task-identity leakage.
- Task-family metrics reported; families with no signal flagged.
- Paired bootstrap (10k resamples) on held-out policy deltas for the finalist vs baselines.
- Whiten-vs-raw stability: probe-AUC spread across salts for whitened must be ≤ raw.

## Frozen gates (Stage 0)

- **G1 (separability):** whitened latent probe improves pairwise-gain AUROC on OOF folds over BOTH prompt-BGE and logit-only baselines by ≥ **0.03 absolute**, in ≥ 8/10 (folds × salts: 5 folds × 2 salts) runs. Alternative arm: any latent variant (raw/PCA) achieves a program-material end-to-end frontier gain despite smaller delta.
- **G2 (task-stratification):** the gain survives task-stratified analysis; not entirely one tiny family (no single eval_name contributes >50% of the aggregate improvement).
- **G3 (policy economics):** a cost-aware escalation policy using the winning probe achieves, vs a cost-matched random/coverage baseline and vs v1-referenced operating point on train-derived holdout: ≥ **0.5pp quality gain at matched cost**, or ≥ **3% relative cost reduction at matched quality**, or captures ≥ **35%** of the oracle (strong−weak>0) uplift under the same action pair.
- **G4 (stability):** whitening at least as stable as raw across seeds/salts.
- Leakage tests must pass; representation must not collapse after removing eval-family signal (task-only baseline documented).

## Verdict vocabulary (frozen, no retuning after results)

- `REPRESENTATION_BLOCKED` — hidden states/logits inaccessible locally (not triggered; feasibility confirmed).
- `KILLED` — latent features fail G1/G2 (no marginal-gain signal beyond prompt embedding / logit summaries).
- `RAW_OR_PCA_PASS` — latent signal passes but whitened does not beat raw/PCA (whitening dropped).
- `WHITENED_PASS` — whitened variant passes all gates and wins the variant comparison.
- `QUALIFIED_FEATURE` — passes gates plus runtime-feasibility bench (<10 ms/req overhead path shown).

Diagnostic correction allowance: exactly ONE preregistered correction permitted on gate failure — re-running with prompt+latent combined features for G3 policy if the latent-only policy fails G3 but latent signal passed G1. Nothing else.
