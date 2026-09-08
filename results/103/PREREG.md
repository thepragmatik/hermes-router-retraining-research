# PREREG — Idea 103 Bayesian Semantic Performance Memory, Stage 0 (FROZEN before pipeline run)

**Date frozen:** 2026-09-08 (AEST). **Spend cap:** $0. **Status:** all gates frozen BEFORE any pipeline code ran.

## Provenance hashes (sha256)
- routerbench_0shot.pkl (train rows, 29193): `ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d`
- winrate_table.parquet (frozen split; test rows present but NEVER loaded/inspected): `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`
- frozen BGE model: BAAI/bge-small-en-v1.5 snapshot 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a, model.safetensors `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`
- sentence_transformers 5.1.2 / torch 2.8.0, host /usr/bin/python3, macOS arm64.

## Data rules
- Train split only (29193 rows from winrate_table.parquet, split=='train'). RouterBench TEST split is SEALED; only permitted touch is the membership count already recorded here (test rows = 3678, from the split table value_counts, not row content). Val split (3626) permitted as train-derived development holdout? NO — historical validation has been consulted repeatedly by prior experiments; to keep this clean, Stage 0 uses train-only leave-group-out CV over eval_name groups and a deterministic train-derived holdout (last 20% of train rows by stable row order). Val is NOT used.
- Outcome definition: strong_correct / weak_correct binary (from frozen winrate table), costs cost_s / cost_w. Strong model = the strong arm, weak = the cheap arm of the frozen pair.
- Embedding of prompts: frozen BGE-small-en-v1.5, normalized, no new embedding APIs, no embedding model bake-off.

## Frozen experimental design
- CV: leave-group-out over eval_name groups (86 groups), 10 folds via deterministic assignment: groups sorted alphabetically, round-robin to folds (seed 103). Additionally a train-derived holdout: rows with index (stable row order) mod 5 == 4 (20%), remaining 80% as memory pool; same seed everywhere = 103.
- k grid: {8, 16, 32, 64}
- decay/temperature grid T: {0.05, 0.1, 0.2} with w_i = exp(-d_i/T) on cosine distance (d = 1 - cos sim); plus rank-decay w_i = 1/(i+1) as one variant.
- prior strengths kappa: {4, 16, 64}; global prior Beta(a0_m, b0_m) = (mean*kap0, (1-mean)*kap0) with kap0 = 16.
- support threshold (n_eff) grid: {2, 5, 10}; below threshold -> back off to task prior; below half that -> global prior.
- Routing-cost grid for the policy diagnostic: cost ratios considered over observed (cost_s, cost_w); policy = pick action maximizing expected marginal gain per dollar with a tie-break to the cheaper model; frontier evaluated at observed costs only, no price changes.
- Perturbation set (train-only prompts, deterministic): paraphrase fixtures from existing train prompts via (a) prefix distractor, (b) suffix distractor, (c) format/whitespace change, (d) instruction-meta repetition. (No LLM paraphrasing, $0.)
- Support/OOD rule (frozen): OOD flag = n_eff < threshold OR median neighbor cosine distance > 0.6.

## Frozen gates (Stage 0, train-derived holdout/CV only)
Gate A (memory value): hierarchical/shrunk memory must improve held-out log loss/Brier or pairwise gain ranking over BOTH raw kNN and task-prior controls on >= 8/10 folds.
Gate B (routing utility): converted to a routing policy, must achieve >= 0.5pp quality gain at approximately matched cost, OR >= 3% relative cost reduction at matched quality, OR preregistered alternative: materially improve OOD/low-support handling without >0.2pp quality loss (i.e., better calibration/Brier on OOD-flagged rows with <=0.2pp mean quality loss).
Gate C (paraphrase robustness): route-flip rate under perturbations must not exceed unperturbed-neighbor-uncertainty baseline flip rate by >10pp without a corresponding support drop (support must drop on flipped cases in the majority of flip cases).
Gate D (support informativeness): low-support/OOD rows must show worse calibration/error than high-support rows in the expected direction.
- If raw kNN helps but shrinkage does not: KNN_ONLY. If neither helps: KILLED. If shrinkage passes all applicable gates: SEMANTIC_MEMORY_PASS.
- Single preregistered diagnostic correction permitted on gate failure: none other defined; no gate may be weakened after results.
