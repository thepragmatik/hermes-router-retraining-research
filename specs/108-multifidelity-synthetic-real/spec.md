# Feature Specification: Multi-Fidelity Synthetic→Real Fusion

**Feature Branch:** `108-multifidelity-synthetic-real`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Depends on:** R7a generator factory as low-fidelity source; Idea 101 real identified outcomes for authoritative qualification.

## Problem

The generator branch eventually produced a strict R7a configuration with low measured key-error in its small audit and very cheap usable labels, but earlier rungs exposed serious generator-key and verifier failure modes. Synthetic labels are therefore potentially valuable **low-fidelity information**, not deployment truth.

This feature tests whether synthetic data can reduce the amount of expensive real routing feedback needed when combined with a small, propensity-corrected real dataset. The key design is asymmetric: synthetic evidence may shape a direct/reward model or prior, while real observed outcomes provide the authoritative correction and qualification.

## User Stories

### Story 1 — Reduce real-label requirements

As a researcher, I want synthetic data to improve a router trained with a small real-label budget compared with a real-only model using exactly the same real rows.

### Story 2 — Detect harmful transfer

As an operator, I want the system to detect when synthetic task mix, model pair, answer keys or verifier behavior diverge from real traffic and make performance worse.

### Story 3 — Keep synthetic truth separate

As a researcher, I want provenance and model-training interfaces that make it impossible to silently treat generated labels as observed real outcomes.

### Story 4 — Correct synthetic bias with real evidence

When Idea 101 supplies propensity-logged real outcomes, use those data to recalibrate/correct the direct model and evaluate policy value honestly.

## Requirements

- **FR-001:** Every training row MUST carry fidelity/provenance (`real_task_native`, `real_randomized`, `benchmark`, `synthetic_r7a`, etc.).
- **FR-002:** Synthetic rows MUST NOT be included in propensity-weighted observed-outcome terms as though they were real logged actions.
- **FR-003:** Always retain a **real-only control at matched real-label budget**.
- **FR-004:** Stage 0 must simulate low/high-fidelity fusion on train-safe data before scaling the generator.
- **FR-005:** Implement at least three controls: real-only; synthetic-only diagnostic; synthetic-pretrain/prior + real recalibration/correction.
- **FR-006:** Preferred causal/OPE integration: synthetic data influences the direct/outcome model; real logged outcomes provide DR/propensity correction.
- **FR-007:** Measure domain/task/model-pair shift between synthetic and real data.
- **FR-008:** Synthetic sample weight/regularization MUST be frozen on train CV; no tuning on real qualification set.
- **FR-009:** Qualification MUST be on real held-out outcomes, never synthetic validation alone.
- **FR-010:** Generator configuration/version and key-validation mode MUST be recorded; R7a strict is the default source, not weaker historical rungs.
- **FR-011:** New synthetic generation spend MUST remain operator-gated and only occur after Stage-0 transfer passes.
- **FR-012:** RouterBench test remains sealed.

## Fusion Methods

Start with simple, interpretable methods:

1. **Synthetic pretrain → real fine-tune/calibration** of a small direct gain/outcome model.
2. **Weighted joint training** with synthetic weight `w_syn < 1` frozen from train CV.
3. **Hierarchical prior:** synthetic estimates initialize prior parameters; real rows update posterior.
4. **DR direct-model augmentation:** use synthetic+real to fit `μ_hat(a,x)` but compute correction/value from real propensity-logged outcomes only.

Do not start with large foundation-model fine-tuning. The question is whether low-fidelity labels improve routing sample efficiency, not whether a large model can memorize generated tasks.

## Stage 0 — Cheapest Falsification

Before any scaled generator spend, create a controlled multi-fidelity experiment from train-safe data. Two valid approaches:

- use existing R7a synthetic rows plus a held-out slice of real RouterBench/train outcomes with no test access; and/or
- construct a deliberately biased low-fidelity view from a full-information train matrix to validate the fusion machinery under known bias.

Evaluate real-label budgets such as 0.5%, 1%, 2%, 5%, 10% (frozen). At each budget compare real-only vs fusion using the **same selected real rows**.

The idea survives only if:

- fusion beats real-only on real held-out policy utility at >= **3/5 real-label budgets**, including at least one budget <=2%;
- at the best low-budget point it achieves >= **0.5pp quality gain at matched cost**, >= **3% cost reduction at matched quality**, or reduces real-label need by >= **25%** to reach the same frozen target utility;
- synthetic-only is not used for promotion and any gap between synthetic validation and real validation is reported;
- harmful-transfer detector/diagnostic identifies at least the deliberately biased synthetic control as lower trust;
- benefits survive >=8/10 seeds/resamples or have uncertainty excluding zero at the primary point.

If synthetic data helps only when real labels are already abundant, the economic case must include generator/maintenance cost. If fusion hurts, kill it and use real-only learning.

## Shift Diagnostics

Measure synthetic vs real:

- embedding/task distribution distance;
- label/need-strong prevalence;
- model-pair success/rescue rates;
- verifier/key type distribution;
- response length/format;
- calibration of direct model separately on each source.

Use these as diagnostics/weights only if preregistered; do not post-hoc discard hard synthetic rows until results improve.

## Stage 1 — Identified Real Correction

Requires 101 data with valid propensities/outcomes. Freeze a temporal split and real-label budget. Train direct model with synthetic assistance, then evaluate/correct with real OPE/DR. Synthetic annotations never create action support.

## Expected Benefit

If successful, this converts the generator factory into a cheap prior/sample-efficiency tool while preserving real evidence as the authority, potentially making frequent router refresh economically viable.

## Stackability / Exclusivity

- Depends on 101 for real deployment claims; can feed 102's direct/nuisance model.
- Stacks with 103 as a prior only after provenance-aware ablation.
- **Synthetic-only promotion is mutually exclusive and forbidden.**
- R7a strict vs any future generator configuration are alternative low-fidelity sources and must be compared/versioned, not pooled silently.
- If real-only wins at matched real budget, 108 is killed even if synthetic metrics look excellent.