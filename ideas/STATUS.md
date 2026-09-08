# Router Innovation Program Status

**Program branch:** `research/router-innovation-2026-09-08`  
**Last updated:** initialize when orchestration begins.

The orchestrator MUST update this table before/after launching child idea agents. Do not infer completion from commit count alone.

| ID | Idea | Stage | Status | Latest SHA | Spend | Evidence tier | Primary result | Blocker / next action |
|---|---|---|---|---|---:|---|---|---|
| 101 | Counterfactual Shadow Telemetry | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | run Stage 0 simulator |
| 102 | Doubly Robust Uplift Router | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | run retrospective Stage 0; real phase waits for 101 |
| 103 | Bayesian Semantic Performance Memory | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | run train-only measured-outcome retrieval |
| 104 | Whitened Latent Marginal-Gain Probe | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | confirm latent accessibility |
| 105 | Conformal Safety Envelope | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | calibrate V1 first |
| 106 | Sequential VOI Controller | blocked by evidence | SURVIVED-RESEARCH | — | $0 | research/spec | — | wait for >=2 useful actions/signals |
| 107 | Diversity-Optimized Model Portfolio | not started | SURVIVED-RESEARCH | — | $0 | research/spec | — | refresh current model snapshot + Stage 0 |
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