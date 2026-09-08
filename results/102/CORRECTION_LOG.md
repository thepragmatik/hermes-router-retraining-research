# Preregistered Diagnostic Correction — consumed (1 of 1)

**Frozen trigger:** `results/102/PREREG.md` § "Single preregistered diagnostic
correction" — isotonic recalibration of OOF DR pseudo-outcomes χ on OOF τ̂
(fit rows only), applied to eval τ̂ before thresholding. Recorded here BEFORE
the corrected gate numbers were computed (this file's commit precedes the
final gate run).

## First-run gate table (exact, from stage0_results.json @ d7672ec)

| gate | result | detail |
|---|---|---|
| G1 (DR value tracking) | **PASS 3/3 regimes** | mean abs err DRL-π/V1: L1 0.00204/0.00234, L2 0.00134/0.00114, L3 0.00105/0.00066 (all ≤ 0.015; tripwire ok) |
| G2 (uplift ranking vs direct) | **FAIL (economics half passed, rank half failed)** | best-λ DRL-π beats best-λ direct baseline in 10/10 seeds (≥8 required) BUT decile-rank Spearman vs direct-inverted-ŵ wins only 6/10 (≥8 required); vs T-learner 0/10 |
| G3 (frontier capture) | **FAIL (both branches)** | best-λ mean Q 0.63748 < bar 0.65031; mean C 0.0013950 > bar 0.0011442; DRL-π frontier is dominated by the monotone threshold-on-p control (best threshold t=0.05: Q 0.64249 @ C 0.0015216 ≥ DRL's 0.64178 @ 0.0015548) |
| G4 (unsupported honesty) | **PASS 10/10** | zero-overlap stratum flagged in 10/10; well-supported strata never majority-flagged; fallback routes equal V1 exactly |
| G5 (propensity integrity) | **PASS** | NaN/zero/×10-corrupted propensities all refused loudly |

## Diagnosis (from first-run diagnostics, no new gates invented)

1. **Pseudo-outcome scale corruption, not ranking sign:** eval deciles of true
   τ rise monotonically (−0.008 → +0.765) while τ̂ deciles peak at decile 3
   (0.631) and *decay* to 0.444 by decile 9 — the second-stage ridge on
   19 one-hot-heavy features overfits the low-p strata (p·f interactions) and
   compresses the upper deciles. The χ scale itself is sound (G1 passed), so
   the frozen isotonic recalibration of χ→τ̂ is exactly the preregistered
   remedy: it re-monotonizes the score against the pseudo-outcomes without
   touching data, propensities, λ grid, split, or gates.
2. **Cost-mechanics artifact in the λ sweep (documented, unchanged by the
   correction):** at λ∈{0,10,25} the DRL/direct policies exceed V1's cost
   because they add strong calls on low-p rows without removing any (V1 rows
   stay strong since τ̂−λ·ΔC > 0 everywhere there). The oracle shows the same
   plateau. Frontier movement therefore only appears at λ ≥ 100, which is why
   the best-cost-nonincreasing λ lands far down the quality curve.
3. τ̂ correlates with true τ (ρ≈0.47 overall) and the direct baseline is the
   V1 decision-form itself (its "win" over V1 is the t=0.30→t≈0.05 threshold
   shift), consistent with P3/P6's structural finding that v1's weak-side
   stratum is a both-fail stratum (train upgrade mass 108 rows).

## Correction applied

`experiments/102/corrected_run.py`:
- 5-fold OOF DRL-π τ̂ on fit rows (same nuisances/λ as first run);
- isotonic regression (PAVA, unweighted, strictly increasing clamp) of OOF χ
  on OOF τ̂ over fit rows → scalar recalibration map g;
- eval τ̂ ← g(τ̂(eval)); identical λ sweep / best-λ rule / gates / support
  fallback;
- T-learner and direct baselines untouched; V1 untouched; oracle untouched.

This is the single preregistered correction. If G2/G3 still fail, terminal
status is **KILLED** (no further correction exists).
