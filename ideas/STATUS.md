# Router Innovation Program Status

**Program branch:** `research/router-innovation-2026-09-08`  
**Last updated:** 2026-09-09 — 101 Phase 2-5 SHADOW_READY merged (`70d46ca`), pushed, and deployed to production (launchd restart); live route-logging verified end-to-end.

The orchestrator MUST update this table before/after launching child idea agents. Do not infer completion from commit count alone.

| ID | Idea | Stage | Status | Latest SHA | Spend | Evidence tier | Primary result | Blocker / next action |
|---|---|---|---|---|---:|---|---|---|
| 101 | Counterfactual Shadow Telemetry | Phase 2-5 DONE + deployed to production | SHADOW_READY | 70d46ca | $0 | train retrospective | OPE harness: policy ordering 10/10 seeds; \|err\|<=0.0031 (gate 0.015); CI coverage 10/10; unsupported-policy + corrupted-propensity alarms fire | T030-T063 executing in worktree on branch 101-counterfactual-shadow-telemetry; LIVE_PREREG.md must be committed before any code; all tests on port >=8766; production deploy (8765 launchd) is orchestrator-only after merge |
| 102 | Doubly Robust Uplift Router | Stage 0 done (sim-only) | KILLED | 739e091 | $0 | train retrospective | Gates per specs/102/ plan.md+tasks.md T053: G1/G2/G4/G5 pass after 1 preregistered correction, G3 fail — DR-uplift frontier dominated by zero-cost threshold-on-p control on the same V1 score (best Q 0.63641 vs bar 0.65031); NEEDS_101_COVERAGE rejected (support benign, no actionable uplift) | none — real-data phase stays locked; negative result final |
| 103 | Bayesian Semantic Performance Memory | Stage 0 done | KILLED | d124b51 | $0 | train retrospective | Hierarchical shrinkage beat kNN/task-prior 9/10 folds but 0.0pp quality + 0.0% cost gain vs task prior at matched cost (Gate B fail) | none — negative result final; frozen spec not weakened |
| 104 | Whitened Latent Marginal-Gain Probe | Stage 0 done | KILLED | 59951e7 | $0 | train retrospective | Latent OOF AUROC 0.7399 vs prompt-BGE 0.7396 (delta <=0.0003; gate >=0.03); task-only baseline 0.7486 beats everything — signal is task identity | none — frozen spec not weakened; latent adds nothing over BGE |
| 105 | Conformal Safety Envelope | Stage 0 done | V1_SAFE_SLICE | fedbc92 | $0 | train retrospective | Held-out risk <= alpha 9/10 folds at all alpha in {0.01,0.025,0.05}; 22-25% coverage; 55-60% cost saving at <=0.8pp acc gap; drift alarms disable envelope | wrap future qualified candidate scores; recalibrate on any new pool |
| 106 | Sequential VOI Controller | gate evaluated — not launched | BLOCKED_PREREQ_NOT_MET | — | $0 | research/spec | Prereq >=2 qualifying signals from {103,104,105,107} measured 1/4 (105 V1_SAFE_SLICE only); per manifest dependency the idea does not launch | revisit only if 101 live telemetry later qualifies >=1 more action/signal |
| 107 | Diversity-Optimized Model Portfolio | Stage 0 done | ORACLE_ONLY_PORTFOLIO | bbf52b8 | $0 | train retrospective | Frontier quality/cost gates pass but pool-overlap realizability <35% of oracle gain (G3 fail) | none — historical-pool complementarity not realizable; needs current-price pool refresh to revisit |
| 108 | Multi-Fidelity Synthetic→Real Fusion | Stage 0 done (retrospective) | KILLED | c2af65e | $0 | train retrospective | Gates per specs/108/ tasks.md T062: fusion ties real-only EXACTLY at all 4 valid budgets (0/10 bootstrap wins) — R7a synthetic selects weak-solvable items, label-inverted vs real need-strong traffic; Gate 2 bias machinery PASS; LOW_FIDELITY_PRIOR_ONLY inapplicable (pretrain never beat real-only) | none — generator scaled-batch request NOT drafted; synthetic stays prior-only, never authority |
| 109 | Hermes Stage-Aware Agent Router | Stage 0A done (trace viability) | TRACE_DATA_INSUFFICIENT | af16541 | $0 | research/spec | Spec line 88 terminal: 69 trace rows, 0 missions/0 stage decisions/0 outcome capture/join-key floor 0% — all gates fail; gaps G1-G5 confirmed exactly; telemetry-gap contract written (C1-C7, binding schema, re-audit gates) | BLOCKED on identified telemetry, NOT KILLED — unblock via 101-integrated collection plan in results/109/TELEMETRY_GAP_CONTRACT.md |

## Evidence-tier vocabulary

Use one of:

- `research/spec`
- `train retrospective`
- `public robustness`
- `shadow observational`
- `shadow randomized/identified`
- `live randomized/identified`
- `Hermes mission replay`
- `Hermes shadow`

Never promote an evidence tier by implication.

## Program integration notes

Recorded 2026-09-09 — measured convergence (full detail: `ideas/INTEGRATION_RECOMMENDATION.md`):

- qualified components: 105 conformal envelope (V1_SAFE_SLICE); 101 OPE harness (STAGE0_PASS) as measurement infrastructure
- killed ideas: 102 (dominated by threshold-on-p), 103 (task prior unbeaten), 104 (latent ≈ BGE; task identity is the signal), 107 (oracle-only realizability), 108 (fusion ties real-only; synthetic label-inverted)
- changed model portfolio: none — incumbent WEAK/STRONG pair frozen in V1 stays
- dependencies newly unblocked: none; 109 remains blocked on identified telemetry (contract written), 106 blocked at 1/4 qualifying signals
- mutually exclusive winners: none beyond the V1+105 stack
- current best single-turn stack: frozen V1 router (mf_router.pt, threshold 0.30) + 105 conformal envelope; no explored mechanism beat it
- current best agentic-stage policy: none estimable — TRACE_DATA_INSUFFICIENT
- cumulative paid spend: $0.00 across all nine ideas
- validation exposures: train-retrospective only; test split sealed all program; 2 preregistered corrections consumed (102, 108), neither changed a verdict

The orchestrator should preserve failed rows rather than deleting them.