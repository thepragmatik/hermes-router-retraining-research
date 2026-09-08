# Idea 108 Stage 0 Report — Multi-Fidelity Synthetic→Real Fusion (retrospective, $0)

**Date:** 2026-09-09 (AEST). **Branch:** `108-multifidelity-synthetic-real`.
**Spend:** **$0.00** (no API/model calls; embeddings computed locally from the frozen
BGE snapshot; no new synthetic generation).
**Preregistration:** `results/108/PREREG.md` (frozen, commit 61db58e, before any
pipeline code) + `results/108/PREREG_ERRATUM.md` (E1–E6, pre-results, commit a1375a9).
**Terminal status (frozen vocabulary):**

# KILLED

(Gate 1 failed after the single preregistered diagnostic correction; verdict rule 4
of PREREG §11. No gate was weakened after seeing results.)

## 1. What ran

- **Data:** R7a-strict synthetic batch `r7_b1788903723_47290` (26 rows: 24 `weak_ok`,
  2 `need_strong`; verifiers 13 exact_match / 11 numeric_tol / 2 token_set), extracted
  from `feat/generator-pivot-r0` via `git show` without a branch switch (hashes in
  `results/108/inputs/PROVENANCE.md`); winrate-table TRAIN rows (29193, fidelity
  `benchmark`), y = need-strong (E1 semantics), untied decisive rows only (14111).
- **Splits:** deterministic seed-108 permutation, 70/30 → dev pool 20435 / eval pool
  8758; untied: dev 9861 / **labeled eval 4206**.
- **Budgets (frozen 146/292/584/1460/2919):** the 0.5% draw had 137 pos / 9 neg
  → INVALID under the frozen <10-class rule; per the frozen fallback, gates were
  evaluated over the remaining 4 valid budgets (1%, 2%, 5%, 10%), each requiring
  wins at a budget ≤ 2% — a stricter requirement than 3/5, not a weakening.
- **Arms:** real-only; synthetic-only (NON-PROMOTABLE); pretrain→update; weighted-joint
  (frozen CV grid on budget real rows); dr-direct (pooled direct model + DR feasibility
  report). Common model: L2 logistic regression on frozen 768-d BGE embeddings
  (E3: embeddings only — the prereg's original numeric features included y's own
  determinants and were removed pre-results as outcome leakage).
- **Metric:** policy utility U = r − 50·cost; route strong iff p̂(need-strong) ≥ 0.5.
  Anchors on labeled eval: all-weak 0.0618, all-strong 0.8453, oracle 0.9140;
  eval P(need-strong | untied) = 0.9365.

## 2. Shift diagnostics (T011; `shift_report.json`, computed before fitting)

| Diagnostic | Value | Flag |
|---|---|---|
| D-label | syn P(need_strong) 0.0769 vs real untied P(y=1) 0.9408 (Δ 0.864 > 0.15) | **FLAG** |
| D-embed | syn→real nearest-neighbor cos: mean 0.7403, min 0.6745, max 0.8444 vs real real-vs-real reference mean 0.8449 (syn mean < ref − 0.10 = 0.7449) | **FLAG** |
| D-len | median length 272.5 vs 739.0 chars, log-ratio −0.998 (rule: \|log-ratio\| > 0.5) | **FLAG** |
| D-pair | syn weak-solvable 92.3% vs real decisive need-strong 93.7% on eval | report |
| D-verifier | synthetic keys generator-emitted (tier VI-6); real outcomes benchmark-graded (tier VI-4) | structural |
| D-task | synthetic rows carry no eval_name stratum (mined taxonomy) | structural |

Correction flags (per §8): **[D_label, D_embed, D_len]** (the frozen pipeline's
`flags_for_correction`, exactly as recorded in `shift_report.json`) → m = 0.5³ = 0.125.

**Dominant finding:** the synthetic corpus is label-inverted relative to decisive real
traffic — R7a questions are 92.3% weak-solvable by construction (that is what the
factory selects for), while the untied real evaluation traffic is 93.7% need-strong.
The generator's selection criterion (usable = weak-solvable) makes its output
anti-correlated with exactly the rows where routing matters.

## 3. Gate 1 (spec survival gate) — FAIL

Wins = fusion beats real-only on labeled-eval utility (paired, identical real rows):

| Budget | Valid | real-only U | pretrain U | joint U | best fusion dU | w_syn (CV) | m_cls (CV) |
|---|---|---|---|---|---|---|---|
| 0.5% | no (137 pos / **9 neg** < 10) | — | — | — | — | — | — |
| 1% | yes | 0.845302 | 0.845302 | 0.845302 | 0.0 | 0.05 | 1 |
| 2% | yes | 0.845302 | 0.845302 | 0.845302 | 0.0 | 0.05 | 12 |
| 5% | yes | 0.845302 | 0.845302 | 0.845302 | 0.0 | 0.05 | 12 |
| 10% | yes | 0.845302 | 0.845302 | 0.845302 | 0.0 | 0.25 | 1 |

(Arms 4 and 5 share the pooled direct model per erratum E5.1; per-budget Gate-1
"fusion" = argmin dev-side CV loss between pretrain and joint — CV losses are recorded
in `budget_curve.csv` and never touch the evaluation pool.)

**Exact ties at every valid budget (dU = 0.0):** every arm — including real-only —
learns "route strong everywhere" on this eval pool, because P(need-strong | untied
eval) = 0.9365 makes all-strong dominant under U = r − 50·cost (all-strong 0.8453 vs
all-weak 0.0618). Fusion never wins a single budget (0/4, 0 at low budget), matched
criteria (a)/(b) fail (identical quality/cost), and the 25%-label-saving criterion is
vacuous (reached at 1% only because every policy equals the target utility exactly —
a tie, not a saving; the ≥25% saving clause presupposes fusion ≥ real-only somewhere,
which never occurs).

### The single preregistered diagnostic correction (§8, applied once)

All three flags → m = 0.125; weighted-joint recomputed with w ∈ {0.00625, 0.03125,
0.125}: **exact ties again at every valid budget (dU = 0.0)**. No further corrections
permitted. Gate 1 remains FAIL.

### Bootstrap / CI at the primary point

dU point estimate 0.0; wins-of-10 = 0/10; 95% percentile CI = [0.0, 0.0] (degenerate —
the policy comparison is deterministically identical, not uncertain).

## 4. Gate 2 (known-bias machinery validation) — PASS (does not rescue Gate 1)

On the simulated strata (40 rows/group over 86 eval_name groups; counts in
`stage0_gate.json`), at the smallest valid real budget (146 rows, 1% draw used for
B1/B2 per erratum E5.3):

- **B1 (benefit):** PASS — Prop-Sim (clean labels, group under-sampling) fusion BEAT
  real-only(146) (dU > 0); w_syn CV-selected **1.0** (the CV embraces useful signal).
- **B2 (reject harmful):** PASS — Flip-Sim (100% corruption) fusion did NOT beat
  real-only(146) (dU ≤ 0); w_syn CV-selected **0.05** (the grid minimum — the frozen
  CV rule pushed the harmful prior toward zero weight by itself).
- **Detector:** PASS — label divergence vs real dev P(y=1)=0.9427: Flip-Sim 0.8691
  vs Prop-Sim 0.0162 (flip ≫ prop, strictly larger as frozen).
- **Gate 2 PASS:** the fusion code can benefit from useful low-fidelity signal, reject
  100%-corrupted signal, and identify it as lower trust. The machinery works; the
  R7a source simply offers no usable signal for this decision on real decisive traffic.

## 5. Synthetic-only diagnostic (NON-PROMOTABLE)

U = 0.0618 vs real-only@10% 0.8453 → generalization gap **−0.7835 utility** (≈ the
all-weak anchor: the synthetic-only model routes almost everything weak because its
labels say 92% weak-solvable). As frozen, this arm is never used for promotion; it is
reported as the fidelity gap between synthetic validation and real outcomes (FR-009).

## 6. DR feasibility (non-gating, PREREG §13)

With simulated Bernoulli(0.5) logging on eval rows (seed 108): V_true = 0.84530;
|V_DR − V_true| = 0.00363 with the real-only μ̂ vs **0.00354 with the synthetic-assisted
μ̂** — the synthetic-assisted nuisance is marginally LESS biased here, but both are
dominated by the same all-strong policy, and DR stays a Stage-1 feasibility note
(FR-006 machinery works on real rows only for the propensity term; FR-002 held).

## 7. Why fusion died (mechanism, not noise)

1. **Structural label inversion (D-label):** the R7a factory optimizes for
   weak-solvable questions (usable = weak_ok), so its label mix (7.7% need_strong) is
   the mirror image of decisive real traffic (93.7% need-strong on untied eval rows).
   Synthetic prior thus pushes toward weak routing exactly where real evidence demands
   strong routing.
2. **Degenerate decision region:** on the frozen γ=50 utility and this pair's economics
   (rescue 45.5% of full train vs regression 2.9%), the optimal policy on untied rows
   is ~always-strong; real-only learns that from a few hundred rows already; 26
   inverted-prior synthetic rows cannot improve it and (at w_syn = 1, m_cls = 12,
   uncorrected bounds) never flip a single eval decision in Gate 1.
3. **Coverage, not just prevalence:** synthetic questions are short (median 272.5 vs
   739.0 chars, log-ratio −0.998), structurally missing task strata (D-task), and
   sit measurably below the real self-similarity reference in embedding space
   (syn→real NN cos mean 0.7403 vs real real-vs-real 0.8449) — the corpus neither
   covers nor matches the real prompt distribution.

Per spec kill logic: "If fusion hurts, kill it and use real-only learning." Fusion did
not even reach "hurts" at the policy level (exact ties), and never beat real-only
anywhere — the economic case never arises. **KILLED**, and per PREREG §11 rule 2/3
contingencies (LOW_FIDELITY_PRIOR_ONLY) do not apply: Gate 1 failed outright and
pretrain→update never beat real-only at any budget.

## 8. Consequences

- **Do not scale the generator** for router-label purposes on this evidence (FR-011
  stays closed; no scaled-batch spend request is drafted).
- The generator retains value only as **test fixtures / pipeline integrity checks**
  (plan kill-logic bullet 2), not as a low-fidelity label source for this routing
  decision.
- **108 does NOT feed 102**: 102's direct/nuisance models gain nothing from this
  source (T061); the roadmap dependency "108 only after a real-label transfer set
  exists" is moot for the synthetic arm.
- If the generator is ever reconsidered, the preregistered requirement is now on
  record: a **source-diversity hypothesis** (plan kill-logic bullet 4) must be frozen
  BEFORE generation — specifically a need-strong-stratified generator configuration
  (target the 45.5% rescue stratum, not the weak-solvable stratum) — plus a fusion
  re-test against a real-only control at matched budget.
- Real-data phase (T040–T043) is **not executed**: 101 telemetry does not exist yet,
  and the Stage-0 verdict already terminates the idea (a KILLED idea has no Stage 1).

## 9. Task coverage (every tasks.md T-number)

- **T001** — read constitution, spec, plan, tasks, GENERATOR_PREREG (R1–R7a full
  ladder), V1_BASELINE_GAPS, 101/102 contracts: done pre-freeze.
- **T002** — `results/108/PREREG.md` frozen (61db58e) before pipeline code: done.
- **T003** — provenance manifest + schema enforcement (`loaders.py`,
  `ProvenanceError` on fidelity mismatch; synthetic→real load refused): done,
  validated by run output.
- **T004** — sealed-test assertion (3678, membership count only): done (`seal_check.py`).
- **T010** — R7a rows + train-safe real outcomes loaded: done (26 + 29193).
- **T011** — task/embedding/label/pair/verifier/length shift diagnostics: done
  (`shift_report.json`).
- **T012** — known-bias low-fidelity simulator (Prop-Sim/Flip-Sim): done.
- **T013** — matched real-row budget draws frozen (146/292/584/1460/2919; 0.5%
  invalid per <10-class rule, fallback engaged): done.
- **T020** — real-only control at every budget: done (all 4 valid budgets).
- **T021** — synthetic-only diagnostic, labeled non-promotable: done (U 0.0618,
  gap −0.7835).
- **T022** — pretrain→update arm: done (ties real-only everywhere).
- **T023** — weighted-joint arm, frozen w_syn grid + CV: done (ties; CV picks 0.05).
- **T024** — DR correction arm (simulated propensities; real rows only in the
  propensity term): done (feasibility report; |bias| 0.0035 syn-assisted vs 0.0036
  real-only).
- **T025** — all arms evaluated on identical labeled eval rows: done (4206 rows).
- **T030** — budget curves + label-saving at frozen target: done
  (`budget_curve.csv`; saving clause vacuous-tie, reported).
- **T031** — paired/seed uncertainty + matched real-only comparison: done (0/10
  bootstrap wins, CI [0,0], exact ties).
- **T032** — fusion fails at ≥3/5 budgets (0/4 valid) → KILLED: applied.
- **T033** — pretrain-helps-only check: pretrain never beats real-only → rule 3 does
  not fire; LOW_FIDELITY_PRIOR_ONLY not applicable.
- **T040–T043** — conditional on 101 telemetry: **not executable now** (by design;
  documented; a KILLED Stage 0 has no real phase).
- **T050–T052** — conditional on transfer pass + operator spend prereg: **not
  executable** (transfer failed; $0 cap).
- **T060** — shift report, budget curves, Stage-0 report: done (this file).
- **T061** — roadmap/ledger note: 108 does NOT feed 102; STATUS.md row update
  (Stage 0 done / KILLED) recorded for the orchestrator (STATUS.md itself is
  orchestrator-owned per hard constraints — not edited by this agent).
- **T062** — terminal status chosen in frozen vocabulary: **KILLED**.

## 10. Artifacts

- `results/108/PREREG.md`, `PREREG_ERRATUM.md`, `stage0_report.md` (this file),
  `budget_curve.csv`, `shift_report.json`, `stage0_gate.json`, `inputs/` (7 R7a
  artifacts + PROVENANCE.md), `emb_cache.npz` (local embeddings, regenerable, not a
  result).
- `experiments/108/loaders.py`, `seal_check.py`, `pipeline.py`, `correction.py`.

## 11. Spend

**$0.00.** No paid API/model calls at any point. Embeddings: local CPU inference from
the frozen BGE snapshot. No new synthetic generation (FR-011 respected; rung ladder
already closed at R7a on the generator branch).
