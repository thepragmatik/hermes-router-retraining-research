# Idea 107 Stage-0 Report — Diversity-Optimized Model Portfolio

**Date:** 2026-09-08 · **Spend:** $0 · **Prereg:** `results/107/PREREG.md` (frozen commit `33c7f1b`, before pipeline code) · **Script:** `experiments/107/stage0_portfolio.py` · **Raw:** `results/107/stage0_raw.txt`

## Data

RouterBench-0shot TRAIN split only: 29,193 rows, 11 models with stored per-row binarized
correctness and per-row dollar cost. Sealed test split: membership count asserted (3,678 rows
exist, never loaded). No paid calls; current-model/pricing snapshot refreshed offline from repo
docs only (`results/107/model_snapshot.json`) — no current-model measured outcome matrix exists
in-repo, so this Stage 0 is **historical-pool selection-method evidence**, labeled
historical/domain-specific, not a deployment pool (FR-010/FR-011).

## What was computed

- **Complementarity matrix** (`results/107/complementarity.csv`): pairwise success rates,
  P(B ok | A fail), P(A ok | B fail), co-failure Jaccard, unique rescue mass (pp), extra cost,
  unique rescues per extra dollar.
- **Brute force** over all 1-, 2-, 3-subsets of the 11-model pool →
  `results/107/portfolio_frontier.csv` (oracle quality, min-cost-correct oracle cost,
  all-called cost).
- **Cost-aware greedy** (OBJ-C with frozen lambda = quality-per-dollar slope between best and
  cheapest single model) verified **identical** to brute force on the 3-subset objective
  (greedy steps: Yi → gpt-4 → weak).
- **Realizability** (predeclared simplest-first): (1) per-task best-model policy; (2) train-fit
  regularized-linear per-model correctness router, argmax over the selected pool, evaluated on a
  20% train holdout. Oracle correctness never used as a routing feature.

## Selected portfolio and gates

Selected 3-model portfolio (oracle-quality-optimal subject to the size/cost constraint;
selection-step correction recorded in `results/107/selection_correction_note.md`):

**{gpt-3.5-turbo-1106, gpt-4-1106-preview, Yi-34B-Chat}**

| gate | result | verdict |
|---|---|---|
| G1 portfolio: >=2pp oracle gain over best single (gpt-4-1106-preview, acc 0.6429) at <=2x all-called cost | oracle quality **0.7126**, gain **+6.97pp**, all-called cost ratio **1.13x** | **PASS** |
| G1 alt: cost −15% at matched quality vs reference pair (weak+Yi) | oracle cost is 4.4x the ref pair's (quality 0.7126 > 0.585, not matched-quality) | not applicable |
| G2 marginal: every added model >=0.5pp unique rescue or >=5% cost improvement | gpt-3.5 49.2pp uniq; gpt-4 19.5pp uniq; Yi 2.59pp uniq (>=0.5) and +48.5% oracle-cost improvement | **PASS** |
| G3 realizability: simple router captures >=35% of oracle gain without erasing cost advantage | best capture **−550%**: per-task policy quality 0.5972 and holdout router quality 0.2893 are both **below** the best single model's holdout 0.6482; routed cost 0.00258 <= 0.00329 (cost advantage kept, but capture is negative) | **FAIL** |
| G4 stability | bootstrap: selected set in 200/200 resamples; price stress (±30%): unchanged; leave-one-model-out: same set in 9/11 removals; leave-one-task-family-out: same set in 85/86 | **PASS** (stable; but on one dataset only → labeled domain-specific) |

Full-pool oracle diagnostic: 0.7648. Reference pair (weak+Yi) oracle: 0.585.

## Interpretation

The historical pool contains real **oracle complementarity** (+6.97pp attainable quality for
1.13x the best single model's all-called cost, stable under resampling, price stress and task
removal). But both predeclared simple runtime-visible routing signals fail to capture even a
positive fraction of that gain — the per-task best-model policy (0.5972) and a regularized
router on the same feature budget as V1 (0.2893 holdout) are both **worse than just always
calling the best single model** (0.6482 holdout). This reproduces, on a cleaner portfolio
selection, the already-frozen P5 evidence: the pool's headroom is real but every realizable
trigger in this corpus is dead.

Per the frozen kill logic: oracle complementarity passes G1/G2 but the realizability gate
captures <35% → **`ORACLE_ONLY_PORTFOLIO`**. Per T032, runtime complexity is not expanded.
No single model dominates routing economics (best single gpt-4 is 1.07x portfolio cost at −7pp
quality), so T022/SINGLE_MODEL_PIVOT does not apply. A downstream pool change would require
recalibration (FR-009) — flagged, but no promotion is made.

## Caveats

- Historical 2023-era pool; current models (gpt-4o/claude-4/deepseek-class) have no measured
  outcome matrix in-repo at $0. Any current-pool claim requires the 101 shadow data or a
  separately gated paid pilot.
- One dataset only; G4 stability is internal to this corpus (labeled domain-specific per the
  prereg's allowed branch).
- One preregistered diagnostic correction was used: the initial cheapest-passing-subset
  selection was corrected to the frozen objective (oracle-quality maximization under the
  cost/size constraint) before any verdict was issued — see
  `results/107/selection_correction_note.md`. No gate was weakened.
- Greedy vs brute-force verified equal (T015).

## Terminal status

**`ORACLE_ONLY_PORTFOLIO`**
