# PREREG — Idea 107 Stage 0: Diversity-Optimized Model Portfolio

**Frozen:** 2026-09-08 (before any pipeline code ran) · **Spend cap:** $0 · **Script:** `experiments/107/stage0_portfolio.py`

## Candidate data sources (frozen)

1. **Primary:** local RouterBench-0shot TRAIN split, 29,193 rows, stored labels + stored costs for 11 models
   (`~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl` + frozen split table
   `~/transfer-bundle/analysis/winrate_table.parquet`). Test split SEALED — only a membership count
   (`(split=="test").sum()==3678`) is asserted; test rows are never loaded.
2. **Secondary (stability check, if fetchable at $0):** one public harmonized matrix
   (`Wikit/RoutingCompendium-perf` per DATASETS.md Tier B), used only as a stress-test / second
   dataset for gate G4. Role: `stress_test` — never exact-pair truth. If the fetch fails or the
   schema differs materially, G4 is decided on train-internal task-family split (eval_name families)
   and the result is **labeled domain-specific** (this satisfies the spec's "or is clearly labeled
   domain-specific" branch).
3. Prohibited: any paid API/model call; downloading model evaluations at cost; touching sealed test rows.

## Eligibility filters (frozen, applied before optimization)

- Model must have stored per-row outcome labels and per-row cost in the train matrix (sufficient coverage = label present on all 29,193 train rows).
- Historical models are inherently non-current; per the hard constraint the current-model/pricing
  snapshot is refreshed by metadata lookup from existing repo docs/results ONLY (`results/P0_MODEL_POOL.md`,
  `research/2026-09-08-innovation-deep-research.md`, `costs/model_prices.json` — currently empty, $0 sources).
  No model is excluded for being historical in Stage 0; instead the whole result is labeled
  **historical-pool evidence** and any promotion claim is bounded to "selection method + relative
  complementarity", not to current deployment. This is recorded, not silently assumed away.
- No provider/privacy exclusions are applied in Stage 0 (all stored pool providers pass
  repo constraints); capability filters are vacuous on stored matrices and noted as such.

## Pool-size limit (frozen)

Max promoted pool = 3 (FR-005). Brute force over all subsets of size <=3 (pool is 11 models, feasible).

## Objectives (frozen)

- **OBJ-Q:** `F(S) = mean_i max_{m in S} Q_im` (oracle attainable quality).
- **OBJ-C:** `F_lambda(S) = mean_i max_{m in S} (Q_im - lambda*C_im)`, `lambda` chosen so the best
  single model on OBJ-C equals the cheapest eligible model's operating point; report lambda.
- Controls (FR-002): cheapest eligible single model (weak tier), best-quality single model,
  historical weak+Yi reference pair (P0/P5 comparison), full-pool unconstrained oracle diagnostic.

## Marginal gates (frozen, from spec Stage 0)

- **G1 (portfolio gate):** a <=3-model portfolio improves oracle attainable quality by >= 2pp over
  the best eligible single model at <= 2x its expected all-called cost, **or** reduces oracle cost
  by >= 15% at matched quality versus the larger/reference pool (weak+Yi pair used as reference).
- **G2 (marginal-contribution gate):** every added model in the selected portfolio contributes
  >= 0.5pp unique success/rescue mass or >= 5% relative cost improvement after preceding models,
  unless it serves a distinct required capability.
- **G3 (realizability gate):** the predeclared simple runtime-visible router proxy captures
  >= 35% of the portfolio oracle gain without erasing its cost advantage.
- **G4 (stability gate):** selection is stable across two compatible datasets/task mixes, or the
  result is explicitly labeled domain-specific.

## Realizability method (frozen, simplest-first per plan)

`realizability.py`-style proxy, in order: (1) per-task (eval_name) best-model policy — task id is
legitimately known in RouterBench structure; (2) if that is insufficient, a simple train-fit
pairwise regularized logistic router on cheap runtime-visible features (prompt length, task family
one-hot), fit on a 80% train sub-split, evaluated on the 20% train holdout — same feature budget
class as V1. Oracle correctness is never used as a routing feature. Realizability fraction =
(proxy attainable quality - best single) / (portfolio oracle - best single), with routed cost
compared to the oracle portfolio's all-called cost.

## Marginal-contribution definition (frozen)

Model m added to S: unique rescue mass = fraction of rows where m is the ONLY correct model in
S+{m} relative to all rows (pp); cost improvement = relative decrease of expected per-row cost of
the portfolio's min-cost correct-selection oracle. Gate passes if either >= 0.5pp or >= 5%.

## Corrections policy

Exactly one preregistered diagnostic correction is permitted if a gate fails narrowly:
re-running the frozen pipeline on the train-derived 80/20 dev/holdout re-split to check whether a
failure is a train-overfit artifact of the selection step. No other changes; no gate is weakened
after seeing results.

## Verdict vocabulary (frozen)

`KILLED | SINGLE_MODEL_PIVOT | ORACLE_ONLY_PORTFOLIO | PORTFOLIO_PASS | QUALIFIED_POOL`

- One model dominates routing economics (G1 fails because <=3 portfolio adds <2pp at <=2x cost AND
  best single is cheapest-quality-optimal) → `SINGLE_MODEL_PIVOT` (T022) or `KILLED` per kill logic.
- Oracle complementarity passes G1/G2 but G3 < 35% → `ORACLE_ONLY_PORTFOLIO`.
- All gates pass on historical pool with stability label → `QUALIFIED_POOL` (selection-method
  qualified; not a deployment pool — requires recalibration downstream per FR-009 and a real pilot).
- Gates pass and the selected pool is deployable-ready on the local corpus → `PORTFOLIO_PASS`.
