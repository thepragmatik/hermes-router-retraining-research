# Stage-0 Report — Idea 103 Bayesian Semantic Performance Memory

**Date:** 2026-09-08. **Spend:** $0. **Terminal status: KILLED.**

## Task coverage
- T001: Read constitution, spec, plan, tasks, exp-005 prereg, PROMPT (in order) before any code.
- T002: `results/103/PREREG.md` written and all gates frozen BEFORE pipeline code ran.
- T003: sha256 provenance recorded for routerbench_0shot.pkl, winrate_table.parquet, frozen BGE model; test split untouched (only membership count 3678 read from split table value_counts, never row content).
- T010: Frozen BGE-small-en-v1.5 (snapshot 5c38ec7c) re-encoded 29193 train prompts -> train-only 384-d normalized neighbor matrix (`experiments/103/train_emb.npy`). No new embedding APIs.
- T011: Global-prior and task-prior baselines implemented. In strict leave-group-out CV the held-out groups have no train rows, so the preregistered task prior is the embedding-kNN-of-group-centroids prior (top-16 train groups, exp weights, shrunk to global with kappa=16).
- T012: Raw kNN measured-outcome estimator with n_eff and median-distance diagnostics implemented.
- T013: Empirical-Bayes shrinkage posterior (Beta-style pseudo-count shrinkage of similarity-weighted kNN evidence toward task prior, kappa in {4,16,64}).
- T014: Per-neighbor provenance: neighbors are train-split rows of the frozen winrate table (dataset=routerbench-0shot train, outcome=binary correctness from frozen labels, cost snapshot=cost_w/cost_s columns, single frozen model pair). Single dataset/pair -> no cross-pair mixing risk; pair-revision check trivially satisfied and recorded.
- T015: 10-fold leave-group-out CV over 86 eval_name groups; 36-point grid (k x T x kappa). Results: `results/103/cv_grid.csv`, `fold_losses.csv`.
- T016: All estimators converted to the same tau-threshold marginal-gain routing diagnostic; frontier in `results/103/frontier.csv`, matched-cost table `matched_cost_comparison.csv`.
- T020: Deterministic $0 perturbation fixtures (prefix distractor, suffix distractor, whitespace/format, meta-repetition) on the 5838-row train-derived holdout.
- T021: Neighbor Jaccard, posterior delta, route flips, support response measured — `results/103/perturbation_results.csv`.
- T022: Low-support/OOD rows defined by frozen rule (n_eff<5 or median neighbor cosine distance>0.6); behavior of posteriors on those rows verified.
- T023: Error vs support measured (`results/103/support_diagnostics.json`); support signal judged below.
- T030/T031/T032: Gates applied below; verdict KILLED (see Gate analysis).
- T040-T043, T050-T052: Conditional phases; skipped — no semantic memory baseline showed signal sufficient to pass Stage-0 gates, so capability decomposition and external transfer phases never unlocked.
- T060: This report, `retrieval_diagnostics.json`, `frontier.csv`.
- T061/T062: Handoff note below.
- T063: Status chosen: **KILLED**.

## CV results (Gate A: HIER must beat BOTH raw kNN and task prior on >=8/10 folds)
Best frozen grid point (chosen by CV log loss, k=16, T=0.05, kappa=4):
- HIER log loss 0.52161, Brier 0.16939
- TASK prior log loss 0.52206, Brier 0.16953
- GLOBAL prior log loss 0.52274, Brier 0.16976
- Raw kNN log loss 0.61984, Brier 0.19460 (badly miscalibrated; ~12pp below task prior)

Per-fold: HIER beats raw kNN 9/10 folds; HIER beats task prior 9/10 folds -> **Gate A technically passes (9/10 >= 8/10)**, but the margin over the task prior is tiny (mean log-loss delta ~0.001, i.e. ~0.1% relative; on ~29k rows the held-out log loss improvement is ~0.0005 nats/row — negligible practical memory value; HIER is essentially returning a slightly smoothed task prior).

## Routing utility (Gate B)
The frozen policy (route strong iff predicted rescue gain > tau at observed costs) yields:
- ALL estimators including plain task prior achieve 0.6429 quality at cost 0.003289 (tau<=0.3) or 0.2167 at 0.000046 (tau>=0.5). There is no tau at which HIER achieves >=0.5pp quality gain over TASK at matched cost (dQ = 0.0pp at every tau; matched-cost table confirms).
- No >=3% relative cost reduction at matched quality either (dC = 0.0%).
- Preregistered alternative (OOD-handling improvement without >0.2pp quality loss): see Gate D — OOD handling does not show a meaningful improvement over the task prior either (HIER brier_low 0.2116 vs TASK 0.2148, on n=296 rows; ~0.3pp Brier improvement on 1% of rows does not qualify as a material gain, and both retain good calibration).
- **Gate B FAILS.**

## Paraphrase/perturbation robustness (Gate C)
Holdout n=5838. Baseline (k=16 vs k=32 re-retrieval) route-flip rate 9.08pp.
- prefix: 7.01pp flips (< baseline), Jaccard 0.69, 58% of flips accompanied by support drop -> PASS
- suffix: 5.04pp (< baseline), Jaccard 0.86, support drop on 27% of flips -> PASS
- format: 0.00pp flips, Jaccard 1.00 -> PASS
- meta-repetition: **11.29pp flips (> 9.08pp baseline by 2.2pp, i.e. within the 10pp allowance), Jaccard 0.64, support drop on only 44% of flips** -> marginal PASS on the flip-rate clause, but flip cases do NOT reliably show a support drop (44% < 50%), so the "without a corresponding support drop" clause is only partially satisfied. This is a warning sign, not a gate failure.
- Gate C: passes numerically, with the meta-repetition caveat recorded.

## Support informativeness (Gate D)
Frozen support rule flags 1.01% of rows (n=296). Expected direction holds (low-support rows have worse calibration for every estimator — e.g. HIER brier 0.2116 low vs 0.1690 high; kNN 0.2760 low vs 0.1938 high). n_eff and distance do carry signal. **Gate D PASSES.**

## Verdict reasoning
The frozen Stage-0 contract requires Gate A AND Gate B. Gate B fails decisively: the hierarchical memory provides no routing-utility gain over the simple task prior at matched cost (0.0pp quality, 0.0% cost) and no material OOD gain. Per spec: "If neither helps, kill semantic performance memory rather than changing embeddings repeatedly." The task-family prior alone (a far cheaper mechanism with no neighbor index at inference) captures essentially all available signal; the semantic memory adds only ~0.0005 nats of log loss and zero frontier movement. The single preregistered diagnostic correction was not needed (no gate failure triggered it; no gates were changed after results).

**Terminal status: KILLED.**

## Handoff (T061/T062)
- 103 should NOT feed 102/105/106 as an evidence feature: the posterior adds no information over a task prior at matched cost, and its support/OOD signal, while directionally correct, is available from the much cheaper task-prior + embedding-distance computation without a neighbor index.
- No authoritative support field to promote; the frozen n_eff/median-distance definitions in results/103/ remain the reference if any later spec revisits retrieval memory with materially new data (e.g., 101 real outcomes).
- RouterBench test split untouched; val split untouched; total spend $0.
