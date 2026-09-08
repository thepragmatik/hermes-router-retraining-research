# PREREG ERRATUM #1 — Idea 108 Stage 0 (pre-results)

**Date:** 2026-09-09 (AEST). **Status at time of erratum:** PREREG frozen and committed
(61db58e). **NO model has been fit, NO metric computed, NO result exists yet.** This
erratum corrects internal contradictions in the frozen design before the pipeline's
first run. It changes NO gate threshold, NO budget, NO seed, NO arm list, NO CV rule,
NO verdict logic. Every correction removes leakage or repairs a contradiction, and each
can only make the fusion test HARDER (anti-fusion direction), never easier.

## E1 — Label semantics (repairs §2/§3 contradiction)

§2 defined y=1 = weak-better, but §3's frozen synthetic mapping (`need_strong`→y=1,
`weak_ok`→y=0) and `experiments/108/loaders.py` encode y=1 = strong-better ("need
strong" — the program's native rescue semantics). As written, the synthetic training
labels would have been inverted relative to the real label.

**Corrected frozen definition (now in force):**
- `y = 1` iff weak wrong AND strong correct ("need strong": strong strictly better;
  the R7a `need_strong` label maps to y=1 directly, as §3 froze).
- `y = 0` iff weak correct AND strong wrong (weak strictly better; R7a `weak_ok`
  maps to y=0: weak sufficed, strong not needed — noting the honest caveat that a
  `weak_ok` row never observed the strong arm, so its y=0 means "strong not strictly
  better *observed*", a fidelity limitation the diagnostics document).
- Untied rows only (both correct / both wrong excluded) — unchanged.

## E2 — Policy rule direction (repairs §3 accordingly)

With y=1 = need-strong, the frozen threshold policy becomes: **route STRONG iff
p̂(y=1) ≥ 0.50; route weak otherwise.** (Threshold 0.50, no tuning — unchanged; only
the direction is stated correctly.) All arms use the identical rule.

## E3 — Feature set (removes outcome leakage; §4 corrected)

§4's numeric features included `1{weak_correct}`, `1{strong_correct}`,
`1{weak==strong}` — y is a *deterministic function* of these, contradicting §4's own
"labels are never features". Realized costs (`cost_w`, `cost_s`) are also
post-decision quantities (response-length dependent), not decision-time covariates.

**Corrected frozen feature set:** the 768-d frozen BGE-small-en-v1.5 normalized
embedding of the prompt/question ONLY, plus intercept. No numeric features; no
standardization beyond the frozen unit-norm embeddings; synthetic rows therefore need
no imputation at all. Consequence: the real-only control gets strictly LESS information
(leakage removed), so the correction cannot manufacture a fusion win; it can only
make Gate 1 harder. The fusion question becomes exactly the spec's question: do
synthetic question/label pairs add real embedding-space routing signal over the same
real rows?

## E4 — D-label diagnostic under corrected semantics (§6 restated)

D-label compares P(y=1): synthetic = 2/26 = 0.0769 vs real train untied P(y=1)
(≈ 0.9408; exact value computed in code). Flag rule unchanged (|Δ| > 0.15). The
expected huge gap (synthetic questions are mostly weak-solvable; real decisive traffic
mostly needs strong) is a genuine, reportable fidelity finding.

## E5 — Mechanical clarifications (no design change)

1. **Fusion arm per budget (Gate 1):** arms 4 (weighted-joint) and 5 (dr-direct) share
   one pooled direct model by construction (§3 arm 5 fits μ̂ on the same syn+real pool
   with the same CV weights), so their policies are identical; arm 5's distinct
   deliverable is the DR value-estimation feasibility report (non-gating). The
   per-budget "fusion" for Gate 1 is therefore selected between arms 3 (pretrain→update)
   and 4 (joint) by the LOWEST frozen dev-side CV log loss on the budget real rows —
   a selection rule that never touches the evaluation pool.
2. **m_cls grid:** applies to R7a `need_strong` rows only; simulator arms (Prop-Sim /
   Flip-Sim) use m_cls = 1 and CV over w_syn only.
3. **Gate 2 budget:** B1/B2 use the smallest VALID real budget under the §2
   budget-validity fallback (if 0.5% is invalid, the 1% budget).
4. **"≥ 3/5 budgets" reading under invalid budgets:** if the §2 fallback invalidates
   the 0.5% budget (for all arms identically), wins are counted over the remaining
   valid budgets and the requirement is wins ≥ 3 over valid budgets, still including
   at least one budget ≤ 2%. (3-of-4-valid is stricter than 3-of-5, not weaker.)
5. **DR construction (§13):** μ̂_weak = logistic model of weak-correctness trained on
   budget real rows (target `weak_correct`) plus R7a `weak_ok` rows (target 1, weight
   w_syn); μ̂_strong = logistic model of strong-correctness trained on budget real rows
   (target `strong_correct`) plus R7a `need_strong` rows (target 1, weight w_syn·m_cls).
   Outcome u(a,x) = correctness − γ·cost. Logged actions under Prop-Sim: Bernoulli(0.5),
   seed 108. Synthetic rows enter μ̂ fitting only, never the propensity term (FR-002).
6. **Bootstrap (§12) restated:** models are fit ONCE per arm/budget on the frozen real
   draw; bootstrap resamples evaluation rows only (10 seeds for the ≥8/10 criterion;
   2000 resamples, seed 108, for the paired ΔU percentile CI at the primary point).

---
*This erratum is part of the frozen preregistration. After this point the pipeline runs
once, gates are evaluated as frozen (plus the single §8 diagnostic correction if and
only if Gate 1 fails), and no gate is touched again regardless of outcome.*
