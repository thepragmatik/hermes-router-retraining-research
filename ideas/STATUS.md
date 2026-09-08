# Router Innovation Program Status

**Program branch:** `research/router-innovation-2026-09-08`  
**Last updated:** 2026-09-09 — Wave A COMPLETE (5/5 Stage 0 done). Qualifying signals for 106: 1 of 4 (105 V1_SAFE_SLICE). Launching Wave B.

The orchestrator MUST update this table before/after launching child idea agents. Do not infer completion from commit count alone.

| ID | Idea | Stage | Status | Latest SHA | Spend | Evidence tier | Primary result | Blocker / next action |
|---|---|---|---|---|---:|---|---|---|
| 101 | Counterfactual Shadow Telemetry | Stage 0 done | STAGE0_PASS | 307beda | $0 | train retrospective | OPE harness: policy ordering 10/10 seeds; |err|<=0.0031 (gate 0.015); CI coverage 10/10; unsupported-policy + corrupted-propensity alarms fire | T030+ live plumbing gated on operator-approved shadow prereg |
| 102 | Doubly Robust Uplift Router | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | run retrospective Stage 0; real phase waits for 101 |
| 103 | Bayesian Semantic Performance Memory | Stage 0 done | KILLED | d124b51 | $0 | train retrospective | Hierarchical shrinkage beat kNN/task-prior 9/10 folds but 0.0pp quality + 0.0% cost gain vs task prior at matched cost (Gate B fail) | none — negative result final; frozen spec not weakened |
| 104 | Whitened Latent Marginal-Gain Probe | Stage 0 done | KILLED | 59951e7 | $0 | train retrospective | Latent OOF AUROC 0.7399 vs prompt-BGE 0.7396 (delta <=0.0003; gate >=0.03); task-only baseline 0.7486 beats everything — signal is task identity | none — frozen spec not weakened; latent adds nothing over BGE |
| 105 | Conformal Safety Envelope | Stage 0 done | V1_SAFE_SLICE | fedbc92 | $0 | train retrospective | Held-out risk <= alpha 9/10 folds at all alpha in {0.01,0.025,0.05}; 22-25% coverage; 55-60% cost saving at <=0.8pp acc gap; drift alarms disable envelope | wrap future qualified candidate scores; recalibrate on any new pool |
| 106 | Sequential VOI Controller | blocked by evidence | SURVIVED-RESEARCH | — | $0 | research/spec | — | wait for >=2 useful actions/signals |
| 107 | Diversity-Optimized Model Portfolio | Stage 0 done | ORACLE_ONLY_PORTFOLIO | bbf52b8 | $0 | train retrospective | Frontier quality/cost gates pass but pool-overlap realizability <35% of oracle gain (G3 fail) | none — historical-pool complementarity not realizable; needs current-price pool refresh to revisit |
| 108 | Multi-Fidelity Synthetic→Real Fusion | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | retrospective fusion first; real phase waits for 101 |
| 109 | Hermes Stage-Aware Agent Router | dependency check | SURVIVED-RESEARCH | — | $0 | research/spec | — | inventory trace viability |

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

Record only measured convergence here:

- qualified components:
- killed ideas:
- changed model portfolio:
- dependencies newly unblocked:
- mutually exclusive winners:
- current best single-turn stack:
- current best agentic-stage policy:
- cumulative paid spend:
- validation exposures:

The orchestrator should preserve failed rows rather than deleting them.