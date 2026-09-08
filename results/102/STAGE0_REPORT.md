# Stage 0 Report — Idea 102: Doubly Robust Uplift Router

**Run:** 2026-09-09 · **Prereg:** `results/102/PREREG.md` (frozen `c5d9cc2`,
BEFORE any pipeline code) · **Correction:** `results/102/CORRECTION_LOG.md`
(declared `22fd693`, before the corrected gate run) · **Spend: $0**

## TERMINAL STATUS: **KILLED**

(Stage-0 gate G3 failed after the single preregistered diagnostic correction;
spec vocabulary: `KILLED | NEEDS_101_COVERAGE | STAGE0_PASS | QUALIFIED`.
`NEEDS_101_COVERAGE` was considered and rejected — see "Why not
NEEDS_101_COVERAGE" below. `QUALIFIED` is not claimable at Stage 0 by design.)

## What was run (exact frozen contract)

- Data: `winrate_table.parquet` train split only (29,193 rows; sha256
  `4e58f024…963a6`). **Test split never loaded** (only its membership count
  3678 via the split table); the 0-shot pickle was never opened. Validation
  split untouched (finalists-only; no finalist declared).
- Router feature: frozen V1 `p_strong` fixture (`cf1baa31…bea57`), V1
  untouched at threshold 0.30. Train anchor reproduced exactly:
  V1 train Q 0.64111, frac_strong 0.7681 (101-prereg anchor match).
- Deterministic 102 fit/eval split (md5 `102:` salt, 20% eval): 23,305 fit /
  5,888 eval, asserted in the loader and tests.
- Logging regimes (exact propensities stored, never estimated): L1 uniform
  (0.5/0.5), L2 `0.60·V1+0.20`, L3 `0.80·V1+0.10` (primary, realistic
  V1-skew). 10 seeds 102000–102009, one sampled log per (regime, seed).
- Learners: cross-fitted ridge nuisances `μ0/μ1` (5-fold, fit rows only);
  DR pseudo-outcomes with exact propensities; DRL-π second stage (ridge on
  p + 82 family one-hots + 5 interactions); T-learner; direct
  weak-correctness baseline (decision-form identical to V1: strong iff
  ŵ<0.30); frozen-V1 control; full-information oracle (diagnostic only);
  monotone threshold-on-p frontier controls. λ grid {0,10,25,50,100,150,
  200,300,500}; margin 0; unsupported rows fall back to the V1 decision.
- 12/12 invariant/unit tests passed before the gate run (`experiments/102/
  test_stage0.py`): hash integrity, split sizes, exact-propensity equality,
  seeded determinism, G5 loud-refusal probes, DR exact-recovery identity,
  pseudo-outcome unbiasedness, fallback semantics, λ-sweep monotonicity.

## Gate results (frozen vocabulary)

| gate | first run | after 1 preregistered correction | verdict |
|---|---|---|---|
| G1 DR value tracking (≤0.015, ≥2/3 regimes) | PASS 3/3 (errs ≤0.0023) | PASS 3/3 (errs ≤0.0023) | **PASS** |
| G2 uplift ranking vs direct (≥8/10 seeds, both sub-conditions) | FAIL (economics 10/10, rank 6/10) | PASS (economics 10/10, rank 8/10; mean ρ 0.159 vs 0.018) | **PASS** |
| G3 frontier capture (≥35% oracle Q lift @ ≤50% cost-advantage loss, or materiality dominance) | FAIL both branches | FAIL both branches | **FAIL → KILLED** |
| G4 unsupported honesty | PASS 10/10 (zero-overlap stratum flagged, fallback==V1 exactly; well-supported strata never flagged-majority) | same code path/thresholds | **PASS** |
| G5 propensity integrity | PASS (NaN/zero/×10 all refused loudly) | PASS | **PASS** |

G3 numbers (mean over 10 L3 seeds, best-cost-nonincreasing λ by the frozen
rule): DRL-π Q **0.63641** @ C **0.0013795**/row (frac_strong 0.7687) vs
frozen bars Q ≥ **0.65031** AND C ≤ **0.0011442**; vs V1 0.63944 @ 0.0014224;
vs best threshold-on-p control t=0.05: 0.64249 @ 0.0015569. The DR-uplift
policy is **dominated by a plain threshold on the same V1 score** — it neither
captures ≥35% of the oracle's +3.1pp quality lift nor loses ≤50% of the
oracle's cost advantage, and it does not beat the monotone control at matched
cost. This holds identically under broad (L1) and V1-skewed (L3) logging.

## Why not NEEDS_101_COVERAGE

`NEEDS_101_COVERAGE` is for a sound estimator that fails only because
realistic logging lacks support/ESS. That is not the failure mode observed:
L3's weights are benign (max |w| ≤ 10, ESS/n ≈ 0.9 for V1-shaped targets), G1
recovers policy values to ≤0.0011 in all three regimes, and the policy-value
and ranking machinery works (G2 rank wins improve to 8/10 after the
preregistered isotonic correction). The method fails because **τ̂'s decile
structure cannot beat the free monotone difficulty signal**: eval-decile true
τ is monotone in `p_strong` (−0.008 → +0.765), so a threshold on p is already
near-optimal within this feature budget, and the oracle lift (+3.1pp) lives
almost entirely in *downgrading* V1-strong rows (779 downgrade vs 108 upgrade
rows on train), which τ̂ does not identify well enough to act on at matched
cost. More randomized coverage (the 101 dependency) would not change a
frontier that is already dominated by a zero-information-cost threshold on
the same score.

## Oracle headroom vs prior evidence (consistency)

The full-information oracle(λ=0) on the eval split is +3.1pp Q at −$0.00056/row
vs V1 — matching the P1/P5 oracle-cascade family (+3.0–3.1pp train-side). As
P3/P6 established, that headroom sits in the weak-first architecture (and
mostly in downgrades), which this binary-uplift policy cannot harvest at
matched cost; the realizable v1-anchored ceiling (+0.3pp) is far below G3's
program-materiality bar. Stage 0's negative verdict is consistent with, and
now extends, the prior negative evidence from an identification-first angle:
even with exact propensities and DR correction, the causal-uplift target does
not produce a deployable frontier on this corpus/feature budget.

## Measured vs not

- Measured: DR policy-value recovery (G1) under uniform→V1-skewed logging;
  uplift ranking vs direct/T-learner controls (G2); end-to-end quality/cost
  frontiers over a frozen λ grid with support fallback (G3/G4); propensity
  integrity (G5); oracle-capture fractions and decile diagnostics; seed
  dispersion (all per-seed numbers in `stage0_results.json` /
  `stage0_corrected.json`).
- Not measured / out of scope: real/shadow telemetry (LOCKED pending 101),
  multi-action uplift (FR-005 defers until binary value — not demonstrated),
  R-learner (optional; not reached), 103/104 feature ablations (both KILLED
  in Wave A), 105 wrapping (no finalist), adversarial prompt perturbation
  (no text embeddings used; prompts enter only via the frozen V1 fixture).

## Eval-exposure log (appended)

- First gate run (`run_stage0.py` @ d7672ec): 30/30 (regime, seed) runs
  scored eval rows once each. One file-path crash after computation (results
  JSON path), fixed; no partial results were consumed from the crashed
  process (identical seeded rerun reproduced all numbers).
- Diagnostics pass (`run_diagnostics.py` @ same tree): per-seed rank deciles,
  G4 zero-overlap probe, A2 stability — eval rows read again for diagnostics
  only; no thresholds changed.
- Corrected gate run (`corrected_run.py` @ post-22fd693): 30/30 re-scored
  with the preregistered isotonic correction. This is the terminal scoring
  pass. No other eval exposure occurred; validation/test rows never touched.

## Artifacts

- `results/102/PREREG.md` — frozen contract (commit c5d9cc2, pre-code)
- `results/102/CORRECTION_LOG.md` — first-run gate table + correction declaration (22fd693)
- `results/102/stage0_results.json` — first run, 30 (regime, seed) cells
- `results/102/stage0_corrected.json` — corrected run, 30 cells
- `results/102/final_gates.json` — final frozen-gate table (all_passed=false)
- `results/102/frontier.csv` (2,880 rows) and `results/102/support_diagnostics.csv`
- `results/frontier.csv` — repo ledger +2 summary rows (KILLED)
- Code: `experiments/102/` (data/simulate/nuisance/dr_learner/features/policy/
  evaluate/diagnostics modules, gate runners, ledger emitter, 12 tests)
- Roadmap status: **KILLED** (ideas/STATUS.md updated by orchestrator per
  program rules; this agent does not edit ideas/STATUS.md).
