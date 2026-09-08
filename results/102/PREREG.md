# PREREG — Idea 102 Stage 0 (Doubly Robust Uplift Router)

**Frozen:** 2026-09-09, before any pipeline code ran (T002). Stage-0 contract only.
No gate below may be weakened after results are seen. Spend: **$0** — no paid or
free model inference; historical stored matrix only. Simulation-only: the
real-data phase stays LOCKED until 101 produces qualified telemetry.

## Authority

- `specs/102-doubly-robust-uplift-router/spec.md` (Stage-0 gates, FR-001..012)
- `specs/102-doubly-robust-uplift-router/plan.md` (data protocol, estimator menu)
- `specs/102-doubly-robust-uplift-router/tasks.md` (T001–T021 Stage-0 scope)
- `.specify/memory/constitution.md`, `experiments/PIVOT_PROTOCOL.md` (frozen)
- Prior evidence honored: P1/P3/P5/P6 negative results (V1-anchored headroom is
  small: realizable ceiling ≈ +0.32pp over V1; weak-first oracle +3.1pp is
  architecturally unreachable by a v1-layer addition). This idea changes the
  *learned quantity* (τ, incremental value) and the *identification* (exact
  randomized propensities + cross-fitting + DR correction), not the classifier.

## Data source (train-only, full-information; test SEALED)

- Frozen split: `/Users/rath/transfer-bundle/analysis/winrate_table.parquet`
  sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`
  (29193 train / 3626 val / 3678 test). **TEST SPLIT IS SEALED — never loaded.**
  The loader asserts the loaded frame contains zero `split=="test"` rows.
  The 0-shot pickle (`routerbench_0shot.pkl`, sha256
  `ba4f77f19517610a707c374e99322d7750c30fc4ae7ff5527888595a1e65d36d`) is used
  ONLY for split-membership verification (row counts), never for test rows.
- Full-information matrix: `train` split columns `weak_correct`,
  `strong_correct` (0/1 as stored — the repo's binarization convention,
  `results/BINARIZATION_NOTE.md`), costs `cost_w`, `cost_s`.
- Router feature: frozen V1 engine (`router_v1/`, threshold 0.30, untouched)
  scores `p_strong` on all 29193 train rows, serialized
  `telemetry/fixtures/v1_train_pstrong.npy`, sha256
  `cf1baa3195f1956641377022361adde7db7b608611f17fe55d2a47641a4bea57`.
- No other features. No embeddings are computed. Historical validation split is
  NOT touched (finalists-only per constitution; no finalist is declared here).

## Deterministic fit/eval split (Stage-0 protocol per spec)

Derived from train rows only by md5 bucketing (same mechanism as the frozen
P1–P5 pivot holdout, salted `102:`):

- `eval_i = 1` iff `int(md5("102:" + prompt_i)[:8], 16) % 10000 < 2000`.
- All learners, fold boundaries, τ second-stage fits, λ/π selection inputs use
  **fit rows only**. Eval rows are consumed exactly once per seed by the frozen
  pipeline (nuisance models are out-of-fold on eval rows; τ̂(eval) never sees
  eval outcomes/correctness).
- Measured sizes (pre-freeze probe, recorded as anchors): eval 5,888 / fit
  23,305. The pipeline asserts these sizes and fit∩eval = ∅.
- No split parameter (salt, rate) may change after any eval exposure. If a
  harness bug forces a rerun after eval rows were scored, the earlier pass is
  VOIDED and disclosed in the report; the corrected run is the only valid
  exposure; no threshold is tuned across passes.

## Action set, quality, costs

- Actions `A = {weak=0, strong=1}` (binary per FR-005).
- Quality `Q = correctness` (0/1 as stored). Utility `U = Q − λ·C` with `C` =
  per-row model cost (dollars, stored `cost_w`/`cost_s`); ΔC(x) = C_strong−C_weak.
- FR-007 router output fields: `uplift` (τ̂), `uncertainty` (row support/OOF
  residual scale), `delta_cost` (ΔC), `utility` (τ̂ − λ·ΔC), `fallback` flag.

## Sanity anchors (pre-freeze read-only probe; NOT gates)

Computed before freezing via the exact transform above, full-information only:
EVAL V1 truth Q 0.63944 / C 0.0014224 / frac_strong 0.7634 (consistent with the
historical V1 val anchor 0.6395/0.7686 on a different row set). EVAL oracle(λ=0)
Q 0.67052 / C 0.0008660 / frac 0.4496 → oracle lift vs V1 +3.108pp, cost saving
+$0.0005564/row. Train upgrade mass on V1-weak side 108 rows; downgrade mass on
V1-strong side 779 rows (P3/P6-consistent structure). Min logged-strong count
per frozen decile (L3, fit rows) ≈ 217. These numbers are recorded so gate
outputs can be sanity-checked against them; the gates below are the contract.

## Logging regimes (≥3 per spec; exact propensities stored, never estimated)

`e(a|x)` = logging probability of action a given row; one sampled action per
row per (regime, seed); **exact** chosen propensity stored with the log; the
learner never sees unchosen outcomes (only `Y = Q[A]`).

- **L1 broad/uniform:** `e = (0.5, 0.5)` on every row.
- **L2 moderately V1-skewed:** `e = 0.60·V1(a|x) + 0.20` (min support 0.20).
- **L3 realistic V1-skewed (primary):** `e = 0.80·V1(a|x) + 0.10`
  (min support 0.10; V1(a|x) deterministic at threshold 0.30).
  This mirrors 101's ε-mixture with a weaker exploration floor.

Per-row logging strength for support diagnostics:
`overlap_i = e(A_i|x_i)·e(1−A_i|x_i) = e_min(x_i)·(1−e_min(x_i))`.

## Seeds

10 deterministic seeds `102000..102009` (numpy `default_rng(seed)`), one
simulated log per (regime, seed). All RNG flows through the per-seed
`default_rng`; no unseeded randomness anywhere.

## Frozen feature sets

- `F_mu` (nuisance outcome features, 20 cols): `[p, 1] ⊗ [1, a]` with
  `a ∈ {0,1}` = intercept, p, strong-indicator, p·strong (intercept carried in
  ridge). Same scalar feature `p_strong` budget as 101's DR outcome model.
- `F_tau` (τ second-stage features, 19 cols): `p`, 82 eval-family one-hots,
  `p×f` for the 5 largest families by train count
  (hellaswag, grade-school-math, mmlu-professional-law, arc-challenge,
  winogrande — the top-5 of `train.eval_name.value_counts()`, a fit-side
  statistic), intercept.

## Nuisance models and estimators (frozen)

- Outcome nuisances `μ_a(x), a∈{0,1}`: ridge regression (closed-form, α =
  1e-4·n_train_fold as in 101) on `F_mu` restricted to logged rows with
  `A=a`, **5-fold out-of-fold** (fold assignment = `default_rng(seed)
  .permutation(n) % 5`). Cross-fitting per FR-003 (nuisance predictions on a
  row never use that row's outcome).
- **DR pseudo-outcome** (exact known `e`, per FR-002/prompt rule — propensities
  are never estimated when exact ones exist):
  `χ_i = μ1(x_i) − μ0(x_i) + (A_i/e_a_i)·(Y_i − μ_A(x_i)) −
  ((1−A_i)/(1−e_a_i))·(0 − μ_A(x_i))`, with `e_a_i = e(A_i|x_i)`.
- **DRL-π (the DR learner under test, FR-004):** ridge (α=10, closed-form) of
  `χ` on `F_tau` over fit rows → τ̂(x).
- **T-learner comparator:** τ̂_T = μ1(x) − μ0(x) from the same cross-fitted
  nuisances.
- **Direct weak-correctness baseline (spec's non-causal control):** ridge
  (α=10) of `1[A_i=0]·Y_i` on `F_tau` over fit rows → ŵ(x); its policy routes
  strong iff `ŵ(x) < 0.30` — the identical decision form to V1 (accept weak
  iff predicted weak-correctness ≥ 0.30), fit on the same features/budget.
- **Control arm (mandatory):** V1 frozen threshold policy (p ≥ 0.30). Its
  decisions are `np.array_equal`-asserted identical to the direct-baseline
  decision form's mask semantics (structural identity check); its value is
  evaluated like every other policy.
- **Oracle (diagnostic only, never deployable):** full-information
  strong iff `(Q_strong − Q_weak) > λ·ΔC(x)` on eval rows.
- **Monotone threshold-on-p controls (frontier guards):** V1-threshold family
  (t ∈ {0.05,...,0.70}) evaluated full-information on eval — if the τ̂-policy
  cannot beat these, uplift adds nothing over difficulty thresholds.

## Policies and λ sweep (FR-009; margin=0 per plan)

- λ grid (frozen): **{0, 10, 25, 50, 100, 150, 200, 300, 500}**.
- For each λ and each scorer s ∈ {DRL-π τ̂, T-learner, direct baseline, oracle}:
  `route_strong_i = τ̂_s(x_i) − λ·ΔC(x_i) > 0` on eval rows; V1 policy is
  λ-independent (single point).
- Full frontier emitted for every (regime, seed, scorer, λ):
  `Q`, `C`, `frac_strong`, `fallback_frac` → `results/102/frontier.csv`.
- No λ is "selected" for qualification; Gate 3 below is evaluated across the
  whole grid (best-λ allowed on eval by frozen rule: argmax mean-over-seeds
  (Q−Q_V1) subject to mean(C−C_V1) ≤ 0; ties → lowest λ, then lowest
  frac_strong). No post-hoc re-scoring at any other λ.

## Unsupported-region fallback (FR-008; frozen thresholds)

A row is flagged `INSUFFICIENT_SUPPORT` (and the policy falls back to the V1
decision for that row) if any of:

- `overlap_i < 0.09` (e_min(x_i) < 0.10);
- stratum ESS/n (importance weights `t(a)/e(a)` of the policy's preferred
  action against the log) < 0.05 within the row's frozen p-decile;
- the row's p-decile contains < 100 fit-side logged strong samples (nuisance
  support guard).

`fallback_frac` per policy is reported in every frontier row. Frozen decile
edges: quantiles of `p_strong` on fit rows at `linspace(0,1,11)` (shared across
seeds; a fit-side statistic only).

## Policy-value estimation for Gate 2 (full-feedback-honest)

For each (regime, seed): the τ̂-policy at λ=0 (built from that seed's fit rows)
and V1 are evaluated by cross-fitted DR policy value (101's estimator):
`V̂ = mean_i[ Σ_a π(a|x_i)·μ̂_a(x_i) + w_i·(Y_i − μ̂_{A_i}(x_i)) ]`,
`w_i = π(A_i|x_i)/e(A_i|x_i)`, using the same OOF μ̂. The eval split's
full-information truth for each policy is computed directly from the hidden
matrix (truth path never touches the simulated log). Supporting-weight
diagnostics (ESS/n, max|w|, quantiles) recorded per policy per seed; SI value
(diagnostic). Target-policy support flags (101's frozen thresholds: min target
prob < 1e-6, ESS/n < 0.01, max|w| > 50, coverage < 5%) recorded.

## Stage-0 gates (frozen; all must hold for STAGE0_PASS)

- **G1 (DR policy-value tracking, spec: |err| ≤ 0.015 on ≥ 2/3 regimes):** for
  the DR-estimated policy value of the frozen evaluation policies
  (τ̂-policy@λ=0 and V1) vs full-information eval truth: per (regime, seed)
  absolute error; regime passes if its mean-over-seeds |err| ≤ 0.015 for both
  policies. Require ≥ 2 of {L1, L2, L3} passing. Additionally the estimate
  must not exceed truth's plausible band by > 0.05 (sanity tripwire) in any
  (regime, seed) for V1.
- **G2 (uplift ranking vs direct baseline, spec: positive and stable gain on
  ≥ 8/10 seeds):** treatment-effect ranking quality measured as policy
  frontier dominance: on eval, for the L3 regime, DRL-π's best-λ policy beats
  the direct weak-correctness baseline's best-λ policy (same frozen best-λ
  rule) on mean ΔQ−λ·ΔC utility (λ=0 utility, i.e., quality at no cost
  increase) in ≥ 8/10 seeds; and its τ̂ ranks the oracle's τ strata better
  than the direct baseline's ŵ: OOF decile-monotonicity (Spearman τ̂ vs true
  per-decile τ on eval, diagnostic table) strictly higher in ≥ 8/10 seeds.
  Both sub-conditions are required (ranking AND economics).
- **G3 (frontier capture, spec: ≥ 35% of oracle quality lift at ≤ 50% of the
  oracle's cost advantage lost, or Pareto movement at program materiality):**
  on eval, L3, mean over the 10 seeds, the best-λ DRL-π policy must satisfy
  `Q ≥ Q_V1 + 0.35·(Q_oracle0 − Q_V1)` AND `C ≤ C_V1 − 0.5·(C_V1 − C_oracle0)`
  with the preregistered numeric anchors **Q ≥ 0.65031 AND C ≤ 0.0011442**;
  OR it must dominate every monotone threshold-on-p control on the (Q, C)
  plane by ≥ +0.002 quality at ≤ equal cost (program materiality). If G3
  passes only via the OR branch, record which branch.
- **G4 (unsupported-region honesty):** a zero-overlap stratum (eval rows with
  p_strong < 0.05 under a weak-only synthetic log) must be flagged
  INSUFFICIENT_SUPPORT and routed to V1 fallback in 10/10 seeds; the policy
  must never report a win computed on unsupported rows alone.
- **G5 (propensity integrity):** NaN/zero/>1 propensities raise loudly
  (ValueError, learner refuses); the learner consumes the stored exact
  propensities (asserted equal to the recomputed exact regime formula); a
  corruption probe (props ×10) is refused, never silently used.

## Adversarial / robustness suite (T018; frozen expectations)

- **A1 zero-overlap:** G4's synthetic weak-only log → flag + fallback, 10/10.
- **A2 skewed logging:** L3 is already the skew test; additionally report τ̂
  rank stability L1↔L3 (Spearman on eval τ̂, diagnostic; no gate).
- **A3 corrupted propensity:** ×10 corruption → loud ValueError (G5).
- **A4 λ separation:** re-threshold τ̂ at two λ values without refitting —
  frontier rows must differ only by the economic rule (assert identical τ̂
  arrays), verifying quality model and economics are separated.
- **A5 identity probe:** control-threshold policy's DR value equals its
  full-information truth to ≤ 1e-10 on every (regime, seed) (the OPE
  estimator's exact-recovery check on a known policy; catches silent
  estimator drift). Paired bootstrap (2,000 resamples, seed 102999) 95% CIs
  reported for ΔQ/ΔC vs V1 (L3) — reporting, not gating.

## Run-invariant asserts (pipeline refuses to print gate numbers otherwise)

- loaded train rows == 29193; zero test rows; fit/eval sizes == (23305, 5888);
- logged propensities ∈ (0,1] and ≥ 0.10 − 1e-12; chosen-propensity array ==
  exact regime formula elementwise;
- per-decile fit-side logged-strong count ≥ 100;
- emitted policies' frac_strong ∈ [0.05, 0.95]; fallback∪decided == eval;
- DR value for the control-threshold policy matches truth ≤ 1e-10 (A5).

## Single preregistered diagnostic correction (spec: one maximum)

If G1/G2/G3 fail: exactly one correction is permitted — **replace the τ̂
second-stage regressor with its rank-calibrated variant**: isotonic regression
of OOF DR pseudo-outcomes χ on OOF τ̂ (fit rows only), applied to eval τ̂
before thresholding. This addresses the most likely failure (pseudo-outcome
scale/miscalibration) without changing data, propensities, λ grid, gates, or
split. If gates still fail after it → `KILLED`. The correction and its
before/after numbers must appear in the report. No other correction exists.

## Decision vocabulary (frozen)

- All G1–G5 pass → `STAGE0_PASS` (real-data phase remains locked pending 101;
  QUALIFIED is reserved for Stage-1 real/shadow qualification and is NOT
  claimable here).
- Estimation gates pass but the method survives only under near-uniform
  exploration and collapses under L3 (V1-skewed) support → `NEEDS_101_COVERAGE`
  with a quantified coverage requirement (required e_min/ESS per stratum).
- Gates fail after the single preregistered correction → `KILLED`.
- Stage-1 qualification additionally requires 101 Stage-1/2 data quality, ≥5%
  relative runtime-cost reduction at matched quality or ≥1pp quality at
  matched cost, no task-family regression, and no unsupported stratum silently
  routed cheap (spec, unchanged).

## Integrity

- G4/G5-style checks run as unit tests before the gate run (`tests/`).
- No gate number is printed or consumed before all run-invariant asserts pass.
- Any exposure of eval rows is logged here (append-only section below) with
  what was scored and why.
- RouterBench test: sealed; zero rows loaded; pickle used for membership count
  only.
- V1 (`router_v1/`) untouched; threshold 0.30 never modified.

### Eval-exposure log

- (none yet — will be appended at run time)

## Spend

$0. No model calls of any kind; stored historical matrix only; no paid API is
authorized by this prereg or by tasks.md.
