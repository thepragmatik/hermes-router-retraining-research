# Router Innovation Program — Integration Recommendation

**Program branch:** `research/router-innovation-2026-09-08`
**Date:** 2026-09-09
**Orchestration:** plan v3 (`.hermes/plans/2026-09-08_233156-router-innovation-orchestration-v3-speckit.md`); nine Spec Kit packages executed by isolated child agents in per-idea git worktrees; every verdict prereg-frozen before pipeline code and compliance-checked on return (specs untouched, prereg predates report, verdict vocabulary matches package).
**Total program spend: $0.00.** No paid API/model call was made by any child. RouterBench test split was never loaded by any child (membership count 3,678 via split table only).

## 1. Status of all nine ideas

| ID | Idea | Status | Report |
|---|---|---|---|
| 101 | Counterfactual Shadow Telemetry | **STAGE0_PASS** | `results/101/STAGE0_OPE.md` (sha 307beda) |
| 102 | Doubly Robust Uplift Router | **KILLED** | `results/102/STAGE0_REPORT.md` (sha 739e091) |
| 103 | Bayesian Semantic Performance Memory | **KILLED** | `results/103/` final report (sha d124b51) |
| 104 | Whitened Latent Marginal-Gain Probe | **KILLED** | `results/104/stage0_report.md` (sha 59951e7) |
| 105 | Conformal Safety Envelope | **V1_SAFE_SLICE** | `results/105/STAGE0_REPORT.md` (sha fedbc92) |
| 106 | Sequential VOI Controller | **BLOCKED_PREREQ_NOT_MET** (not launched) | gate evaluation recorded in `ideas/STATUS.md` |
| 107 | Diversity-Optimized Model Portfolio | **ORACLE_ONLY_PORTFOLIO** | `results/107/` report (sha bbf52b8) |
| 108 | Multi-Fidelity Synthetic→Real Fusion | **KILLED** | `results/108/stage0_report.md` (sha c2af65e) |
| 109 | Hermes Stage-Aware Agent Router | **TRACE_DATA_INSUFFICIENT** (blocked, not killed) | `results/109/report.md` + `TELEMETRY_GAP_CONTRACT.md` (sha af16541) |

Ledger of record: `ideas/STATUS.md` (rows cite spec sources and branch SHAs; failed rows preserved).

## 2. Cost/spend and evidence tier per idea

All nine ideas: **$0.00**.

Evidence tiers (per STATUS.md vocabulary — none promoted by implication):

- 101, 102, 103, 104, 105, 107, 108: `train retrospective` (historical frozen train data, prereg-gated, test-sealed).
- 106: `research/spec` (never ran).
- 109: `research/spec` (trace audit; the audited log itself is operational-only traffic).

Nothing in the program reached `shadow randomized/identified` or `live randomized/identified` — the live phases of 101/102/108 stayed locked by design, and no operator prereg for live collection was requested or granted during this program.

## 3. Independently qualified components

Exactly one routing-relevant component qualified:

- **105 Conformal Safety Envelope (`V1_SAFE_SLICE`)** — wrapped around the frozen V1 score: held-out risk ≤ α in 9/10 folds at every frozen α ∈ {0.01, 0.025, 0.05} (exact one-sided Clopper–Pearson bound, δ=0.05); cheap-acceptance coverage 22–25% (gate ≥10%); 55–60% cost saving vs always-strong at ≤0.8pp accuracy gap (gate ≥3%); drift/adversarial alarms (task-mix reweight, score shift, OOD families, score noise, adversarial score push) all fire and disable the envelope, silent in-distribution.

Additionally qualified as **measurement infrastructure** (not a routing component):

- **101 OPE harness (`STAGE0_PASS`)** — the counterfactual estimator is statistically trustworthy (ordering 10/10 seeds, |err| ≤ 0.0031 vs gate 0.015, CI coverage 10/10, alarms on unsupported policies and corrupted propensities). It validates *future* live telemetry evaluation; it produced no training data itself.

## 4. Failed/killed ideas and why

- **102 DR Uplift Router — KILLED.** After the single preregistered correction (isotonic recalibration of OOF DR pseudo-outcomes), G1/G2/G4/G5 passed but G3 failed both branches: the best cost-nonincreasing DRL-π point (Q 0.63641 @ $0.0013795/row) missed the frozen bar (Q ≥ 0.65031 AND C ≤ 0.0011442) and was dominated by a **zero-cost threshold on the same V1 `p_strong` score**. The oracle's +3.1pp headroom sits in mass that τ̂ cannot act on at matched cost. `NEEDS_101_COVERAGE` was considered and rejected: support is benign (max|w| ≤ 10, ESS/n ≈ 0.9) and there is no actionable uplift whose coverage could be improved.
- **103 Bayesian Semantic Memory — KILLED.** Hierarchical shrinkage beat kNN and task-prior baselines 9/10 folds (modeling works), but delivered **0.0pp quality and 0.0% cost gain vs the plain task prior at matched cost** (Gate B). The cheap prior wins; per-prompt semantic retrieval adds nothing on this traffic.
- **104 Whitened Latent Probe — KILLED.** Feasibility passed (local SmolLM2-360M hidden states accessible, $0), full 29,193-row capture ran, but best whitened-latent OOF AUROC 0.7399 vs prompt-BGE 0.7396 (Δ ≤ 0.0003; gate ≥ 0.03) and a **task-identity-only baseline (0.7486) beat everything** — the "latent signal" is task identity, which BGE already carries.
- **107 Diversity Portfolio — ORACLE_ONLY_PORTFOLIO.** Frontier quality/cost gates passed, but pool-overlap realizability is **< 35% of oracle gain** (G3 fail): the complementarity exists only against models we do not actually have at historical prices.
- **108 Multi-Fidelity Fusion — KILLED.** Fusion (pretrain→update and weighted-joint, synthetic weight CV-frozen) **ties real-only exactly at all 4 valid budgets** (0/10 bootstrap wins, CI [0,0]) — R7a synthetic items are weak-solvable (92.3% weak_ok), label-inverted vs decisive real traffic (94.1% need-strong). The known-bias machinery itself passed (Gate 2: Prop-Sim beats real-only(146), Flip-Sim rejected with w_syn→0.05 and correctly lower trust), so the *methodology* is sound; the *synthetic data* has no routing value. LOW_FIDELITY_PRIOR_ONLY inapplicable (pretrain never beat real-only). Generator scaled-batch request NOT drafted.
- **106 VOI Controller — BLOCKED_PREREQ_NOT_MET.** Prereq ≥ 2 qualifying signals from {103, 104, 105, 107}; measured 1/4 (105 only). Not launched, per manifest dependency.

## 5. Stackability / error-overlap findings

- The stack {V1 frozen score} ⊕ {105 envelope} is the **only** measured stack: it is exactly 105's G1–G4 result. It is stackable by construction (wrapper) and already drift-hardened.
- No second qualified score exists to stack (105's own T014 recorded: no independently qualified 102/103/104 score; single-envelope rule documented). The planned 105-wraps-finalists expansion is **vacuous this cycle** — 102/103/104 all failed to produce a wrappable score.
- Error-overlap lesson from the kills: 102, 103, and 104 all independently converged on the same finding — **on this traffic, nearly all routable signal is task identity already captured by the V1 score** (102: threshold-on-p dominates the uplift frontier; 104: task-only baseline beats latent+BGE; 103: task prior unbeaten). Three different decision-mathematics, one shared conclusion.
- 107's oracle gap and 108's synthetic failure are both **data-pool failures**, not method failures: complementarity exists only against absent models; synthetic labels select the wrong item mix.

## 6. Selected model portfolio

**None selected.** 107 returned ORACLE_ONLY_PORTFOLIO: no realizable portfolio change qualifies. The incumbent frozen pair stays: WEAK = `mistralai/mistral-7b-chat`, STRONG = `gpt-4-1106-preview`, as frozen in V1. A current-price/current-model pool refresh is the one documented path to revisit 107 (STATUS.md row), but it requires new preregistration and is not justified by current evidence of headroom.

## 7. Recommended single-turn architecture

**Frozen V1 router (mf_router.pt, threshold 0.30, engine `router-v1-frozen`) + the 105 conformal safety envelope, with V1's weights/threshold untouched.**

- This is a **negative program conclusion, and it is valid**: eight alternative mechanisms (causal uplift, semantic memory, latent probes, portfolio diversification, synthetic fusion) all failed to beat the incumbent score or a plain threshold on it, at $0 spend, under preregistered gates that were never weakened.
- The envelope adds measurable value over raw V1: bounded risk at chosen α, 55–60% cost saving at ≤0.8pp accuracy gap, and automatic disablement under drift/adversarial score manipulation (directly answers the AGENTS.md adversarial cost-manipulation requirement for any promoted router component).
- V1's known operational gaps (G1–G5 in `results/V1_BASELINE_GAPS.md`: hardcoded prompt_id, no service logging, no outcome capture) are **not** fixed by this program — see §9.

## 8. Recommended Hermes agentic-stage architecture

**None available.** 109 returned TRACE_DATA_INSUFFICIENT: the only trace surface (shadow log, 69 rows) is health/probe traffic with 0 missions, 0 stage decisions, 0 outcome capture, and a 0% join-key floor (prompt_id hardcoded to 0, no content hash). No stage-aware policy can be estimated or even feasibility-checked from this. The audit is the deliverable: `results/109/TELEMETRY_GAP_CONTRACT.md` defines gaps C1–C7, a binding future trace schema, and frozen re-audit gates. 109 is **blocked on identified telemetry, not killed** — it can re-enter cheaply once 101-style collection exists.

## 9. Data/telemetry improvements valuable regardless of router choice

1. **101 T030+ live telemetry plumbing** — prompt content hash, session/message linkage, outcome join keys, service-logging parity. This is the single highest-leverage improvement: it simultaneously unblocks 109's re-audit, 102's real-data phase, 108's real phase, and gives every future router change an unbiased offline evaluation path. The harness to trust that data already exists and is validated (101 STAGE0_PASS). Requires a fresh preregistration + operator authorization before any code (program rule).
2. **109 telemetry-gap contract as the binding schema** — adopt its C1–C7 field requirements (content hash, mission/stage/step identity, outcome capture, retry/tool fields, join-key floor) so traces are collected once, correctly.
3. **105 drift-alarm runtime** — even without any new model work, the envelope's KS/realized-risk alarms convert silent V1 degradation into a loud failure signal.
4. **Synthetic data remains prior-only, never authority** — 108's structural-shift evidence (label mix, length log-ratio −1.0, task strata) is a durable negative: any future synthetic factory must target the *decision-relevant* item distribution, not solvable-item yield.

## 10. Exact next action — or stop

This is an **operator decision point**; the program does not self-authorize live work.

- **Recommended next action (highest value):** draft and preregister the **101 live shadow-telemetry plumbing** (T030+ per 101's spec, schema per 109's contract, gates frozen before code, $0 — it is logging plumbing, not model calls). This converts the program's one validated-harness + one qualified-wrapper result into a live evidence engine and re-opens 109/102/108 on real data.
- **Parallel cheap action if the operator prefers no new plumbing:** re-run **107 with a refreshed current-price model snapshot** (new prereg required; $0 on historical data) — the only killed idea whose blocker is an artifact-staleness problem rather than a negative result.
- **Otherwise: stop routing work.** The evidence supports the simpler policy: frozen V1 (+ envelope when deployed) is the best known configuration, and no explored mechanism beat it. Per the program's definition of done, a negative conclusion is valid — and this one is well-evidenced, cheaply obtained, and fully documented.

## Validation exposures (honesty appendix)

- Every Stage-0 result is train-retrospective only; no test-split row was ever loaded (each child asserted the seal; 109 additionally confirmed RouterBench untouched).
- Historical validation remained finalists-only; development used train-only holdouts with recorded seeds/splits in each PREREG.
- Two preregistered single diagnostic corrections were consumed program-wide (102: isotonic recalibration; 108: shift-flag correction) — both declared in their CORRECTION_LOG/ERRATUM before the corrected run, neither changed a terminal verdict.
- One prereg erratum set (108, E1–E6) was committed pre-results, before any gate evaluation.
