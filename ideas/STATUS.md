# Router Innovation Program Status

**Program branch:** `research/router-innovation-2026-09-08`  
**Last updated:** 2026-09-09 — Wave A batch 1 complete (101 STAGE0_PASS, 103 KILLED, 107 ORACLE_ONLY_PORTFOLIO); 104+105 launching.

The orchestrator MUST update this table before/after launching child idea agents. Do not infer completion from commit count alone.

| ID | Idea | Stage | Status | Latest SHA | Spend | Evidence tier | Primary result | Blocker / next action |
|---|---|---|---|---|---:|---|---|---|
| 101 | Counterfactual Shadow Telemetry | Stage 0 done | STAGE0_PASS | 307beda | $0 | train retrospective | OPE harness: policy ordering 10/10 seeds; |err|<=0.0031 (gate 0.015); CI coverage 10/10; unsupported-policy + corrupted-propensity alarms fire | T030+ live plumbing gated on operator-approved shadow prereg |
| 102 | Doubly Robust Uplift Router | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | run retrospective Stage 0; real phase waits for 101 |
| 103 | Bayesian Semantic Performance Memory | Stage 0 done | KILLED | d124b51 | $0 | train retrospective | Hierarchical shrinkage beat kNN/task-prior 9/10 folds but 0.0pp quality + 0.0% cost gain vs task prior at matched cost (Gate B fail) | none — negative result final; frozen spec not weakened |
| 104 | Whitened Latent Marginal-Gain Probe | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | confirm latent accessibility |
| 105 | Conformal Safety Envelope | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | calibrate V1 first |
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