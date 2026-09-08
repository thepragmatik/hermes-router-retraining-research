# Stage 0 Report — Idea 105: Conformal Safety Envelope

**Terminal status: `V1_SAFE_SLICE`**
**Date:** 2026-09-09 · **Worktree:** `/Users/rath/src/idea-worktrees/105-conformal-safety-envelope`
**Spend:** $0 (no paid API/model calls) · **RouterBench test:** SEALED (only touch = split-table membership count: 3678 rows; never loaded)

## Executive summary

The frozen V1 router score supports a **~22% cheap-acceptance slice at α=0.01** with empirical
held-out risk ≤ α in 9/10 folds (max realized risk 0.0111), a ~55% cost saving vs always-strong,
and near-parity routed accuracy. Gates G1–G4 pass. Stratification adds nothing and is removed.
Verdict per the frozen vocabulary: **V1_SAFE_SLICE** (PROMPT full vocabulary:
`KILLED | V1_SAFE_SLICE | CANDIDATE_SAFE_SLICE | QUALIFIED_WRAPPER` — the latter two are
unreachable at Stage 0 because no non-V1 candidate score is independently qualified yet).

## Setup (all frozen in PREREG.md before any pipeline run)

- Candidate score: frozen V1 train probs `results/v1_train_probs.npy`
  (sha256 `dfbe974e…`, byte-identical to `git show feat/router-v1-operationalise:results/v1_train_probs.npy`),
  model `router_v1/mf_router.pt` (sha256 `db6706b1…`, matches PROVENANCE.md), threshold 0.30 untouched.
- Safety score: `s = 1 − p_strong_wins` (larger = safer for the cheap route); frozen in PREREG.
- Risk event (frozen): `R = 1{weak_correct == 0 AND strong_correct == 1}` — cheap answer
  incorrect while the reference (strong) answer is correct. Train base rate 0.4548.
- Method: nested acceptance sets on calibration-ordered thresholds, exact one-sided
  Clopper–Pearson (1−δ), δ=0.05, α ∈ {0.01, 0.025, 0.05}; largest-coverage threshold with CP
  upper bound ≤ α; else `NO_SAFE_COVERAGE` (never relaxed — occurred in stratified small
  strata and backed off to global per FR-007, α never changed).
- Splits: 10 deterministic folds (seeds 0–9), 40% calibration / 40% evaluation of the 29193
  train rows; val and test untouched.
- Data hashes: routerbench_0shot.pkl `ba4f77f1…`; winrate_table.parquet `4e58f024…`.

## Global envelope results (results/105/coverage_risk_global.csv)

| α | folds risk ≤ α | mean coverage | mean risk | max risk | mean cost | saving vs always-strong | acc gap |
|---|---|---|---|---|---|---|---|
| 0.01 | **9/10** | 22.1% | 0.0062 | 0.0111 | 0.001477 | **55.1%** | +0.0010 |
| 0.025 | **9/10** | 23.5% | 0.0189 | 0.0266 | 0.001399 | 57.5% | +0.0035 |
| 0.05 | **9/10** | 25.3% | 0.0409 | 0.0558 | 0.001327 | 59.7% | +0.0077 |

Always-strong baseline: cost 0.003289, accuracy 0.6429.

## Gates (spec Stage-0 survival conditions)

- **G1 risk (9/10 folds):** PASS at every α. At α=0.01 exactly 9/10 folds ≤ α (the 10th
  realized 0.0111); the prereg allows ≥9/10. No systematic violations.
- **G2 coverage ≥10%:** PASS — 22–25% across α on the train population (not a 0.1% sliver).
- **G3 economics ≥3% relative cost improvement at matched quality:** PASS — 55–60% saving
  vs always-strong with accuracy within 0.1–0.8 pp. (Also far above the "≥5% with material
  saving" alternative clause.)
- **G4 drift alarms deactivate/widen the envelope:** PASS — see below.

## Stratification (Phase 2; results/105/coverage_risk_stratified.csv)

Both preregistered strata (`eval_name` task family; V1-decision) were tested with the
frozen ≥200-calibration-row minimum and global backoff (small strata and strata with
in-stratum `NO_SAFE_COVERAGE` back off to global). Result: mean coverage/risk/cost within
~0.1 pp of global for both strata (e.g. α=0.01: eval_name 22.13% vs global 22.14%). **No
material gain → stratification removed; global envelope is the promoted configuration.**

## Drift / adversarial stress (Phase 3; results/105/drift_stress.csv)

α=0.01 global envelope, detector = realized-risk breach OR KS score-shift alarm (p<0.01):

| fixture | cov | emp risk | KS p | alarm | action |
|---|---|---|---|---|---|
| in-distribution control | 0.224 | 0.0050 | 0.096 | no | keep |
| task-mix reweight (3 families) | 0.000 | — | 3e-10 | **yes** | reduce/disable |
| score-distribution shift (+0.05) | 0.230 | 0.0097 | ~0 | **yes** | reduce/disable |
| rare/OOD-like task families | 0.467 | 0.1429 | 4e-12 | **yes** | reduce/disable |
| score revision noise (sd 0.05) | 0.225 | 0.0068 | ~0 | **yes** | reduce/disable |
| adversarial score push (+0.2) | 0.209 | 0.0000 | 0.0 | **yes** | reduce/disable |

All shifted fixtures alarm and disable/reduce the envelope; the in-distribution control
does not. User-controlled prompt manipulation could not be simulated by re-encoding
modified prompts at Stage 0 (frozen train probs); the score-effect is simulated and the
shift detector fires. A text-level manipulation test (re-encode adversarial suffixes
through the frozen encoder, still $0) is recommended before any deployment claim.

## Assumptions & limitations (FR-002, FR-009, FR-010)

- The CP guarantee is conditional on calibration/evaluation **exchangeability within the
  RouterBench train distribution**. It is NOT valid under arbitrary distribution shift.
- Labels are winrate-table binary correctness, not an objective verifier; label noise
  inflates the effective risk.
- The 1-of-10 folds at α=0.01 that exceeded target (0.0111 > 0.01) is expected under the
  (1−δ) bound design; the CP bound at selection covered the target as designed.
- **Recalibration triggers:** router version/checkpoint hash change, grader/label definition
  change, or major traffic-distribution change (detected by the KS/mix alarms above).
- Sample sizes: n_cal = 11,677 per fold global; stratified strata ranged 29–~9,000.

## Stackability (Phase 4 — T050–T052)

No other candidate score (102/103/104) is independently qualified at this time, so no
wrapper integration was performed. When one qualifies, wrap exactly ONE final envelope per
score (no stacked calibration wrappers); report its ranking gain separately from the
envelope's risk-control/coverage value.

## Verdict

`V1_SAFE_SLICE` — the frozen V1 score yields a useful (~22% coverage, 55% cost saving)
high-precision cheap slice at α=0.01, with a working conservative drift-invalidation path.
The envelope is a wrapper; it does not make V1 smarter and receives no ranking credit.
