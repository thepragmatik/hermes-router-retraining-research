# PREREG — Idea 105 Stage 0: Conformal Safety Envelope (frozen before any pipeline run)

**Date frozen:** 2026-09-09 (before any calibration/evaluation code ran)
**Worktree:** `/Users/rath/src/idea-worktrees/105-conformal-safety-envelope`, branch `105-conformal-safety-envelope`
**Spend cap:** $0. No paid API/model calls authorized.

## 1. Candidate score (frozen)

Primary and only Stage-0 candidate: **frozen V1 router score** `results/v1_train_probs.npy`
(sha256 `dfbe974ecadb93e8f2b78ebb5f87b33d6ae9c108b48b903a4c433dd5b017e1af`, float32, n=29193),
the train-split outputs of `router_v1/mf_router.pt` (sha256
`db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7`, engine `router-v1-frozen`,
decision threshold 0.30, never modified). Row order is the winrate-table train split order
(29193 rows); verified by row-count alignment. No other candidate score is independently
qualified at execution time (102/103/104 have not passed), so Phase-1 candidate set = {V1}.

## 2. Routing action and risk event (frozen)

Two-tier setting: **cheap action** = route to weak model (mistralai/mistral-7b-chat);
**reference action** = route to strong model (gpt-4-1106-preview). Labels come from the
frozen winrate table (`/Users/rath/transfer-bundle/analysis/winrate_table.parquet`,
sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`): binary
`strong_correct`, `weak_correct` and per-row costs `cost_s`, `cost_w`.

**Risk event (binary, exact):**

```
R = 1{ cheap (weak) answer is INCORRECT while the reference (strong) answer is CORRECT }
  = 1{ weak_correct == 0 AND strong_correct == 1 }
```

Rationale: this is the unacceptable quality loss the cheap route can cause relative to the
reference action — the high-precision event an envelope must control. Overall train rate ≈
0.4548 (unconditional), so the envelope must find a high-safety subset. **This definition is
frozen; it will not be changed after seeing calibration or evaluation results.**

## 3. Splits (frozen)

Source population: RouterBench-0shot TRAIN rows only (29193; test split SEALED — never
loaded; the only permitted test touch is the membership count in the split table, above).
No historical-validation rows are touched (V1 probs are train-only; val is excluded).

10 deterministic folds, seeds 0–9. Within each fold:

- **fit**: not needed for V1 (score pre-frozen) — placeholder only;
- **calibration**: 40% of train rows (threshold selection / risk bound only);
- **evaluation**: 40% of train rows (untouched until threshold frozen);
- remaining 20% unused per fold (buffer, avoids split-reuse).

Split generation: `numpy` `default_rng(seed)` permutation of row indices, deterministic.
Calibration rows are never used to tune V1 (V1 is frozen) nor the envelope beyond
threshold selection.

## 4. Envelope method (frozen)

Simple finite-sample nested-threshold risk control (spec FR-003):

- safety score `s(x)` = V1 cheap-safety score. Larger = safer for cheap routing. Frozen
  definition: `s = P_weak_correct_calibrated` — V1's strong-win probability `p` mapped
  monotonically to safety as `s = 1 - p` when V1 would route weak, and, for rows V1
  routes strong (p ≥ 0.30) we still evaluate the counterfactual cheap decision; the
  acceptance family is over ALL train rows ordered by `s = 1 - p` (descending). Note:
  because weak correctness is decreasing in nothing observable except p, higher `p`
  means V1 believes strong is needed; `s = 1 - p` orders rows from "cheapest-safest" to
  "riskiest". (Frozen now; no re-choice after results.)
- Acceptance sets: accept cheap route iff `s >= t`, threshold grid = calibration-quantile
  nested family (all distinct calibration values of `s`, evaluated largest→smallest
  coverage).
- For each acceptance set, compute observed failures `k/n` on calibration rows and the
  **one-sided exact Clopper–Pearson (1−δ) upper confidence bound** on the risk;
- select the **largest-coverage threshold whose CP upper bound ≤ α**;
- if no threshold qualifies → `NO_SAFE_COVERAGE` for that fold/α (never relax α).

**Frozen hyperparameters:**

- α grid: `{0.01, 0.025, 0.05}`
- δ (bound confidence): `0.05` (i.e. 95% one-sided CP bound)
- minimum calibration size: `n_cal ≥ 2000` per fold (and ≥ 200 per stratum else back off to global)
- folds/seeds: 10 (seeds 0..9), deterministic
- optional coarse strata (tested ONLY after global result, at most these 2, preregistered now):
  1. task family = `eval_name` coarse bucket (exact `eval_name` value; strata with < 200 calibration rows back off to global);
  2. traffic/V1-decision stratum: {V1-routes-weak, V1-routes-strong} (each ≥ 200 rows required, else global).
  Stratification is kept only if it materially increases useful coverage without risk violation.

## 5. Gates (frozen before evaluation — verbatim from spec Stage 0)

Survival requires ALL of:

- **G1 risk:** empirical held-out risk ≤ target α in ≥ **9/10 folds**, for at least one α in the grid (or the CP bound covers α as designed — bound is enforced at selection, so we verify realized risk);
- **G2 coverage:** cheap-acceptance coverage ≥ **10%** on the train population (≥ 5% only counts if paired with program-material cost saving / high-value risk reduction);
- **G3 economics:** matched-quality total cost improves ≥ **3% relative** vs the unwrapped conservative baseline (always-strong), **or** the wrapper materially reduces false-cheap/high-value misses at acceptable cost;
- **G4 drift:** on preregistered synthetic drift fixtures (task-mix reweighting, score-distribution shift, OOD eval_name subset, score noise/revision simulation), the shift/support alarm correctly reduces/disables the envelope (no preserved stale guarantee).

Economics: total routed cost = mean cost of chosen arm under the envelope (cheap accepted rows → cost_w, else cost_s), compared to always-strong (mean cost_s). Quality matchedness reported as routed accuracy vs always-strong accuracy.

## 6. Verdict vocabulary (frozen)

- `NO_SAFE_COVERAGE` at all useful α for V1 → **KILLED** (envelope killed for current scores);
- V1 yields useful safe coverage meeting G1–G4 → **V1_SAFE_SLICE**;
- a non-V1 independently qualified candidate yields the coverage → **CANDIDATE_SAFE_SLICE**;
- envelope qualifies as a wrapper over an independently qualified score → **QUALIFIED_WRAPPER**.

Given the candidate set = {V1}, attainable Stage-0 verdicts here: **KILLED | V1_SAFE_SLICE**.
(PROMPT lists the full vocabulary; CANDIDATE_SAFE_SLICE/QUALIFIED_WRAPPER are unreachable at Stage 0 because no other score is qualified yet.)

## 7. Assumptions / limitation statement (frozen)

- Any exchangeability/conformal claim is conditional on calibration/evaluation exchangeability within the train distribution; it is **not valid under arbitrary distribution shift**. Drift fixtures are diagnostics, not guarantees.
- Recalibration triggers (frozen): change of router version/checkpoint hash, grader/label definition change, or major traffic-distribution change (task-mix shift detected by the drift fixtures).
- Winrate-table binary correctness is the grader; it is not an objective verifier and may contain label noise.

## 8. Artifact hashes (T004)

- routerbench_0shot.pkl: `ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d`
- winrate_table.parquet: `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`
- router_v1/mf_router.pt: `db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7` (matches PROVENANCE.md)
- results/v1_train_probs.npy: `dfbe974ecadb93e8f2b78ebb5f87b33d6ae9c108b48b903a4c433dd5b017e1af` (byte-identical to `git show feat/router-v1-operationalise:results/v1_train_probs.npy`)
- Split-table membership counts (only test touch): train 29193 / val 3626 / test **3678 (sealed, never loaded)**.
