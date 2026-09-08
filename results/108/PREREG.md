# PREREG — Idea 108 Stage 0: Multi-Fidelity Synthetic→Real Fusion (FROZEN)

**Date frozen:** 2026-09-09 (AEST), BEFORE any fusion/pipeline code ran. **Spend cap: $0.**
**Worktree:** `/Users/rath/src/idea-worktrees/108-multifidelity-synthetic-real`, branch
`108-multifidelity-synthetic-real`. This is **retrospective Stage 0**: the R7a synthetic
factory data already exists (branch `feat/generator-pivot-r0`, batch
`r7_b1788903723_47290`); no new generation is authorized (FR-011); the real identified
data phase waits on Idea 101 telemetry and is NOT executable now (Phase 3 conditional).

Everything below is frozen. Gates are the contract; on failure the only permitted
response is the single preregistered diagnostic correction (Section 8), then the frozen
verdict vocabulary (Section 11). No gate is weakened after seeing results.

## 1. Data and provenance (FR-001, FR-010, FR-012)

- **Synthetic source (the only one):** R7a strict rung, batch `r7_b1788903723_47290`,
  extracted from `feat/generator-pivot-r0` via `git show` (no branch switch). 26
  accepted rows (24 `weak_ok`, 2 `need_strong`); verifiers: 13 exact_match, 11
  numeric_tol, 2 token_set. Generator config: R7a strict (R5-strict verifier-only K=3
  majority key gate, agreement arm removed, GEN_JSON_MODE=1, weak `z-ai/glm-5.3-flash`,
  strong `deepseek/deepseek-v4-flash`); key-validation mode = strict verifier-only
  majority (R7a hand audit wrong-key 0/11). Extracted copies + sha256 hashes:
  `results/108/inputs/` (see `PROVENANCE.md`). Weaker historical rungs (R1–R6) are NOT
  pooled in.
- **Real rows:** `winrate_table.parquet`
  (sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`), TRAIN
  split only (29193 rows), binary `strong_correct`/`weak_correct`, costs `cost_s`/`cost_w`.
  Real-row fidelity tag: **`benchmark`** (constitution VI tier 4 — trusted benchmark
  outcomes; NOT task-native accepted outcomes; never upgraded).
- **Fidelity schema (T003):** `experiments/108/loaders.py` tags every row `fidelity` at
  load time; accepted values: `synthetic_r7a` (R7a jsonl only), `benchmark`
  (winrate-train only). Loading a synthetic file with any target fidelity other than
  `synthetic_r7a` raises `ProvenanceError`; a synthetic row cannot enter a real frame
  through the Stage-0 loaders. Synthetic rows never enter any propensity-weighted
  observed-outcome term (FR-002): the only propensity terms in Stage 0 act on real rows.
- **Seal (T004):** `(split=='test').sum()==3678` asserted in
  `experiments/108/seal_check.py`; test rows never loaded/inspected/embedded/deduped.
- **VAL split (3626) NOT used** (historical validation exposed).

## 2. Splits, label, budgets (frozen)

- **Label:** y = 1 iff weak correct AND strong wrong ("rescue": weak strictly better);
  y = 0 iff strong correct AND weak wrong. Tied rows (both correct 0.1881 / both wrong
  0.3285 of train) are EXCLUDED from fitting and evaluation for every arm identically.
- **Split:** deterministic 70/30 of the 29193 train rows via
  `numpy.random.default_rng(108)` permutation: dev pool 20435, eval pool 8758. The
  permutation order is also the stable row order used for budget draws.
- **Labeled pools:** labeled dev = dev ∩ untied; labeled eval = eval ∩ untied (~4236
  expected; exact count computed in code). All evaluation uses labeled eval only,
  identical for every arm and budget.
- **Real-label budgets (frozen):** 0.5%, 1%, 2%, 5%, 10% of 29193 = **146 / 292 / 584 /
  1460 / 2919 rows** (`int(round(b·29193))`), drawn as the FIRST k untied rows of the
  frozen dev-pool permutation. **Every arm at a budget uses the exact same real rows**
  (FR-003). Single frozen draw per budget (spec freezes budgets; no re-drawing).
- **Budget-validity fallback (frozen, deterministic):** if a budget draw has <10
  positives or <10 negatives, that budget is invalid for all arms; the 0.5% budget is
  then replaced by 1% and gates are evaluated over the remaining valid budgets; exact
  class counts are printed in the report. Applies identically to all arms.
- **Seeds:** primary seed 108 (draws + CV). Uncertainty = bootstrap of the eval pool
  (Section 12), not re-drawn budget samples.

## 3. Arms (frozen; FR-005)

Common model: `sklearn` multinomial `LogisticRegression(C=1.0, max_iter=2000)` on
[dense features ; 6 numeric features] (Section 4). No LLM fine-tuning anywhere.

1. **real-only**: fit on the budget real rows (fidelity `benchmark`).
2. **synthetic-only (NON-PROMOTABLE diagnostic)**: fit on the 26 R7a rows
   (`weak_ok`→y=0, `need_strong`→y=1); evaluated on the same real eval rows. Marked
   non-promotable in code, every table, and the report; never used for promotion (FR-009).
3. **pretrain→update**: stage 1 fit on the 26 synthetic rows; stage 2 `warm_start=True`
   refit on the budget real rows (`max_iter=100, tol=1e-4` — a bounded real update of
   the synthetic-initialized model).
4. **weighted-joint**: fit on budget real rows (weight 1) + 26 synthetic rows (weight
   w_syn; R7a `need_strong` rows additionally weighted by class multiplier m_cls).
   **Frozen grids:** w_syn ∈ {0.05, 0.25, 1.0}; m_cls ∈ {1, 12} (12 = 24/2, the R7a
   weak_ok:need_strong count ratio) applied to `need_strong`-labeled synthetic rows
   only. Selection: 5-fold deterministic `KFold(5, shuffle=False)` CV **on the budget
   real rows themselves** (the same real information real-only gets; never on the eval
   pool; FR-008), minimizing out-of-fold log loss of the weighted-joint model; ties →
   smaller w_syn. Selected combo is then used for the full fit at that budget.
5. **dr-direct**: μ̂(a,x) fit on synthetic + budget real rows (pooled, w_syn from the
   same CV rule), DR value computed on eval rows under the Prop-Sim simulated logging
   policy (Section 13) with propensities known exactly; synthetic rows never enter the
   propensity-weighted term (FR-002, FR-006).

**Policy (frozen, identical rule for all arms):** route weak iff p̂(y=1 | x) ≥ 0.50,
where p̂ is the arm's model; route strong otherwise. No threshold tuning.

## 4. Features (frozen)

- Frozen 768-d **BGE-small-en-v1.5** normalized embeddings (same frozen snapshot as
  ideas 103/105: `BAAI/bge-small-en-v1.5`, snapshot
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, model.safetensors
  `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`), computed
  offline via `sentence_transformers` (CPU, batch 128) on train prompts and R7a
  questions — $0, no new embedding APIs.
- 6 numeric features: `[cost_w, cost_s, cost_s − cost_w, 1{weak_correct},
  1{strong_correct}, 1{weak_correct == strong_correct}]`. **Labels are never features**
  (y is the separate target).
- Synthetic rows: numeric features set to the corresponding TRAIN MEANS (frozen
  means; synthetic rows carry no RouterBench outcomes). Never re-tuned.
- Model = multinomial logistic regression, C=1.0, max_iter=2000, lbfgs, intercept.

## 5. Known-bias simulator (frozen; FR-004, plan part B; T012)

Two simulated low-fidelity sources built from the labeled dev pool (full-information
train matrix; disjoint from the eval pool by construction):

- **Prop-Sim (useful low-fidelity signal):** 40 rows per eval_name group (deterministic
  first-k under the frozen permutation; ~3440 rows), label = y_true (clean), i.e. the
  bias is domain skew (heavy group under-sampling), not label corruption.
- **Flip-Sim (harmful low-fidelity signal):** same strata construction, label =
  1 − y_true (100% corruption).

**Gate 2 (code-path validation, frozen):**
- **B1 (benefit):** weighted-joint with Prop-Sim labels + the 0.5% (146-row) real
  budget beats real-only(146) on labeled-eval policy utility (paired, same eval rows).
- **B2 (reject):** weighted-joint with Flip-Sim labels + the 146-row real budget does
  NOT beat real-only(146) (same w_syn CV rule; report the selected w_syn — CV must
  push w_syn toward 0/small).
- **Detector:** Flip-Sim must be identified as lower trust than Prop-Sim via the frozen
  D-label diagnostic: |p_syn − p_real_dev| strictly larger for Flip-Sim; AND B2 holds.
  This operationalizes the spec's "harmful-transfer detector identifies the deliberately
  biased synthetic control as lower trust".
- B1 AND B2 AND detector all pass → Gate 2 PASS.

## 6. Shift diagnostics (frozen; descriptive, computed BEFORE model fitting; T011)

Flags use frozen rules; diagnostics are descriptive and never reweight outside Section 8.

- **D-label:** synthetic P(y=1) = 2/26 = 0.0769 vs real train P(y=1 | untied)
  (≈ 0.4548; exact value computed in code). Flag iff |Δ| > 0.15.
- **D-embed:** mean/max cosine of each of the 26 synthetic question embeddings to their
  nearest real-train prompt embedding (BGE space); reference = mean nearest-neighbor
  cosine among a fixed sample of 2000 real train prompts (frozen permutation head).
  Flag iff syn mean sim < real reference mean − 0.10. (Self-referenced rule; no
  absolute threshold invented.)
- **D-len:** synthetic question length (chars) vs real prompt length; flag iff
  |ln(median_syn / median_real)| > 0.5.
- **D-pair:** synthetic label strata {weak_ok 92.3%, need_strong 7.7%} vs real pair
  states {weak-correct 21.7%, rescue 45.5%}; report; structural prevalence mismatch.
- **D-verifier:** synthetic rows carry generator-emitted verifier/key types (13 EM /
  11 nT / 2 tS); real rows have NO verifier/key column (benchmark-graded outcomes) —
  different evidence tiers (constitution VI tier 6 vs 4). Report; structural finding.
- **D-task:** synthetic rows have no eval_name stratum (generated from the mined seed
  taxonomy) — task-strata are structurally missing for synthetic rows; TV distance is
  computable only for Prop-Sim/Flip-Sim vs real dev strata and is reported. Report only.

## 7. Metric (frozen)

**Policy utility** on labeled eval rows: `U = r − γ·cost`, r = 1{routed model correct},
cost = cost_w (weak route) or cost_s (strong route), **γ = 50** (reward per $1; frozen
scale: quality differences are O(1), the strong−weak mean cost gap ·50 ≈ 0.16, so the
metric is quality-dominant but cost-visible). Frozen anchors (recomputed exactly in
code): all-weak U ≈ 0.2144, all-strong U ≈ 0.4785, oracle (strong iff rescue) ≈ 0.5970.
Per-arm quality and mean cost are also reported separately (needed for the spec's
matched-cost / matched-quality criteria).

## 8. Single preregistered diagnostic correction (the ONE bounded correction)

If and only if Gate 1 FAILS: recompute the weighted-joint arm with
w_syn′ = w_syn × m, m = 0.5^(#flags among {D-label, D-embed, D-len}), re-run its w_syn
CV with the multiplier applied, re-evaluate Gate 1 once. If Gate 1 then passes, the
pass is reported as post-correction (and Gate 2 must still pass for
SAMPLE_EFFICIENCY_PASS). If Gate 1 still fails → verdict per Section 11 with no further
corrections. This correction is never applied when Gate 1 already passes.

## 9. Gate 1 (spec survival gate; exact spec language, frozen operationalization)

Fusion (best of arms 3/4/5 per budget, chosen by the same frozen selection rules) must
beat real-only on labeled-eval policy utility at **≥ 3/5 budgets, including at least
one budget ≤ 2%** (paired: same eval rows, same real rows; primary seed 108), AND at
the best low-budget point (best budget ≤ 2%) at least one of:
- **(a)** quality(fusion) − quality(real-only@same budget) ≥ 0.005 (0.5pp) AND
  mean cost(fusion) ≤ mean cost(real-only) (matched cost);
- **(b)** mean cost(fusion) ≤ 0.97 × mean cost(real-only) AND quality(fusion) ≥
  quality(real-only) (≥3% cost reduction at matched quality);
- **(c)** real-label saving ≥ 25% to reach the frozen target utility T = U(real-only@10%):
  smallest frozen budget b* with U(fusion@b*) ≥ T must satisfy 1 − b*/10% ≥ 0.25
  (i.e. b* ≤ 7.5%); if none reaches T, saving = 0.

AND all of:
- synthetic-only is not used for promotion (structural: it never enters Gate 1);
- the harmful-transfer detector identifies Flip-Sim as lower trust (Section 5);
- benefits survive **≥ 8/10 bootstrap resamples** (Section 12) or the paired bootstrap
  95% CI of ΔU excludes 0 (correct sign) at the primary point (the best budget ≤ 2%
  where the ≥3/5 count is achieved; if fusion wins no budget ≤ 2%, Gate 1 fails).

## 10. Gate 2 (bias-simulator validation)

B1 AND B2 AND detector (Section 5). Gate 2 PASS is required for
SAMPLE_EFFICIENCY_PASS; a Gate 2 fail caps the verdict at LOW_FIDELITY_PRIOR_ONLY.

## 11. Verdict logic (frozen, complete) and terminal vocabulary

1. Gate 1 PASS + Gate 2 PASS → **SAMPLE_EFFICIENCY_PASS**.
2. Gate 1 PASS + Gate 2 FAIL → **LOW_FIDELITY_PRIOR_ONLY** (prior helps; machinery not
   validated for scaled use; stop scaling).
3. Gate 1 FAIL + the pretrain→update arm alone beats real-only at ≥ 3/5 budgets
   including one ≤ 2% → **LOW_FIDELITY_PRIOR_ONLY** (T033; synthetic helps only as
   initialization, not as final-policy fusion; stop scaling).
4. otherwise → **KILLED** (T032; includes fusion hurting real performance, benefit only
   at abundant budgets without economic justification, and detector failure).

Terminal status vocabulary (exact, from PROMPT.md):
**`KILLED | LOW_FIDELITY_PRIOR_ONLY | SAMPLE_EFFICIENCY_PASS | QUALIFIED_FUSION`**.
QUALIFIED_FUSION requires the Stage-1 real identified-data phase (Idea 101 telemetry)
and is NOT reachable in retrospective Stage 0. The report and machine output state the
terminal status exactly in this vocabulary.

## 12. Statistics (frozen)

- Paired ΔU = U(arm) − U(real-only@same budget) on identical labeled eval rows.
- **Bootstrap:** 10 eval-pool resamples (seeds 0–9, n = labeled-eval size, with
  replacement); models NOT refit (fixed frozen predictions; only eval rows resampled).
  Gate-1 seed criterion: fusion > real-only in ≥ 8/10 resamples at the primary point.
- **CI:** paired bootstrap 95% percentile CI for ΔU at the primary point, 2000
  resamples, seed 108. Either the 8/10 criterion or CI-excludes-0 satisfies the
  seed/CI component (spec: ">=8/10 seeds/resamples or have uncertainty excluding zero").
- Synthetic-only generalization gap (reported): U(syn-only) − U(real-only@10%).
- Real-label saving curve: for each budget, U(fusion), U(real-only); b* vs T (Section 9c).
- All numbers in the report come from the frozen pipeline; no post-hoc subset switches.

## 13. DR / propensity reporting (frozen; FR-002, FR-006; T024-equivalent)

Prop-Sim logging on the labeled eval rows: action ~ Bernoulli(0.5) per row (known
propensities; both potential outcomes exist in the frozen table). DR value of each
arm's policy: V_DR = (1/n) Σ_i [ μ̂_a(x_i) + (r_i(a_i) − μ̂_{a_i}(x_i))·1(π(x_i)=a_i)/e_i ]
with e_i = 0.5. Reported: V_DR for the real-only μ̂ vs the synthetic-assisted μ̂, against
the exact policy value V_true (both potential outcomes known). |bias| comparison is a
FEASIBILITY report for the Stage-1 design, NOT a gate. Synthetic rows appear only
inside μ̂ fitting, never in the propensity term (FR-002).

## 14. Economic check (frozen; plan kill-logic bullet 3)

If fusion wins only at 5%/10% budgets, report that scaled use must include generator +
maintenance cost and requires operator review (R7a economics: $0.000069/usable label,
2000 labels ≈ $0.14 + audit/maintenance time). Reported, not gated, if it occurs.

## 15. Deliverables

`experiments/108/`: `loaders.py`, `seal_check.py`, `pipeline.py` (single deterministic
pipeline producing all artifacts). `results/108/`: `PREREG.md` (this file),
`stage0_report.md`, `budget_curve.csv`, `shift_report.json`, `inputs/` (R7a artifacts +
`PROVENANCE.md`). Commits on the idea branch only.

## 16. Conditional phases NOT executable now (by design)

- **Phase 3 (T040–T043):** requires Idea 101 real propensity-logged telemetry; 101 is
  STAGE0_PASS but telemetry is not yet collected. Marked not-executable-now.
- **Phase 4 (T050–T052):** only after transfer passes + a separate operator-gated
  spend prereg. $0 cap here means no generation. Marked not-executable-now.

---
*Frozen 2026-09-09 before any fusion pipeline code ran. Never weaken a gate after
seeing results. A failed gate is evidence.*
