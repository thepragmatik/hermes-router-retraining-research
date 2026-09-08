# Router Innovation Ideas — Execution Index

This folder is the human/orchestrator entrypoint for the 2026-09-08 router innovation program.

The actual GitHub Spec Kit packages live under `../specs/<idea>/` so they retain the conventional spec layout. Every package contains:

- `spec.md` — problem, requirements, data boundaries, success/kill gates, expected benefit and stackability;
- `plan.md` — implementation architecture, statistics, cost discipline, rollback logic and deliverables;
- `tasks.md` — ordered cheapest-falsification-first implementation checklist;
- `PROMPT.md` — ready-to-paste prompt for a dedicated execution agent.

Use [`META_PROMPT.md`](META_PROMPT.md) to launch an orchestrator over the whole program.

## Ideas

| ID | Idea | Role | Dependencies | Execution prompt |
|---|---|---|---|---|
| 101 | Counterfactual Shadow Telemetry | foundational learning substrate | none | [`../specs/101-counterfactual-shadow-telemetry/PROMPT.md`](../specs/101-counterfactual-shadow-telemetry/PROMPT.md) |
| 102 | Doubly Robust Uplift Router | causal marginal-gain policy | 101 for real claims | [`../specs/102-doubly-robust-uplift-router/PROMPT.md`](../specs/102-doubly-robust-uplift-router/PROMPT.md) |
| 103 | Bayesian Semantic Performance Memory | measured-outcome semantic retrieval | historical outcomes; 101 improves currency | [`../specs/103-bayesian-semantic-memory/PROMPT.md`](../specs/103-bayesian-semantic-memory/PROMPT.md) |
| 104 | Whitened Latent Marginal-Gain Probe | true model-internal signal | accessible local hidden states + paired outcomes | [`../specs/104-whitened-latent-gain-probe/PROMPT.md`](../specs/104-whitened-latent-gain-probe/PROMPT.md) |
| 105 | Conformal Safety Envelope | risk/coverage wrapper | any candidate score | [`../specs/105-conformal-safety-envelope/PROMPT.md`](../specs/105-conformal-safety-envelope/PROMPT.md) |
| 106 | Sequential VOI Controller | adaptive evidence/action purchasing | >=2 independently useful actions/signals | [`../specs/106-sequential-voi-controller/PROMPT.md`](../specs/106-sequential-voi-controller/PROMPT.md) |
| 107 | Diversity-Optimized Model Portfolio | upstream model-pool selection | outcome matrices + current model metadata | [`../specs/107-diversity-model-portfolio/PROMPT.md`](../specs/107-diversity-model-portfolio/PROMPT.md) |
| 108 | Multi-Fidelity Synthetic→Real Fusion | sample-efficiency / label economics | R7a + 101 for real qualification | [`../specs/108-multifidelity-synthetic-real/PROMPT.md`](../specs/108-multifidelity-synthetic-real/PROMPT.md) |
| 109 | Hermes Stage-Aware Agent Router | mission-stage routing | replayable Hermes traces | [`../specs/109-hermes-stage-router/PROMPT.md`](../specs/109-hermes-stage-router/PROMPT.md) |

## Recommended waves

### Wave A — cheap/foundational, may run mostly in parallel

- 101 Stage-0 simulator and telemetry contract;
- 107 model-portfolio audit;
- 103 semantic-memory retrospective experiment;
- 104 latent separability feasibility/Stage 0;
- 105 calibration on V1/current scores.

These are intentionally cheap and reveal whether the program has useful data, a better pool, a better signal, or at least a safe coverage slice.

### Wave B — depends on evidence

- 102 after its $0 replay passes; real claims wait for 101 data;
- 108 after retrospective fusion passes; real qualification waits for 101;
- 105 can wrap any qualified candidate.

### Wave C — composition / alternate unit

- 106 only after at least two actions/signals independently pay;
- 109 may run independently whenever sufficient Hermes traces exist.

## Exclusivity / non-stackable notes

- Semantic **cluster→fixed model** is not part of 103 and remains retired.
- 104 raw/PCA/whitened variants compete; promote one simple winner.
- 105 global vs stratified calibration compete; one envelope per candidate.
- 106 myopic vs depth-2 compete; no RL unless simple VOI first passes and a residual long-horizon gap is demonstrated.
- 107 selected model portfolio replaces the candidate action set for downstream calibration; do not reuse historical router thresholds unchanged.
- 108 synthetic-only promotion is forbidden; real-only vs real+synthetic are competing policies at matched real-label budget.
- 109 heuristic vs learned stage policy compete; keep heuristic if equivalent.
- 109 is a separate estimand from single-turn router ideas and can succeed independently.

## Shared governing documents

- [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md)
- [`../specs/router-innovation-2026-09-08/roadmap.md`](../specs/router-innovation-2026-09-08/roadmap.md)
- [`../research/2026-09-08-innovation-deep-research.md`](../research/2026-09-08-innovation-deep-research.md)
- [`../research/2026-09-08-adversarial-review.md`](../research/2026-09-08-adversarial-review.md)
- [`../research/2026-09-08-branch-evidence-map.md`](../research/2026-09-08-branch-evidence-map.md)

The governing operational principle is: **falsify cheaply, qualify independently, then stack only measured complementary gains.**