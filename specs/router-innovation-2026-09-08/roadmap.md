# Roadmap: Router Innovation 2026-09-08

This roadmap is the **Spec Kit spec-of-specs** for the post-uplift research phase. It decomposes the broad router problem into independently falsifiable sub-features. Each sub-feature has its own `spec.md`, `plan.md`, and `tasks.md`, and may be implemented or killed without forcing the others to continue.

The roadmap is intentionally ordered by **information value and prerequisite structure**, not by novelty.

**Status legend:** `survived-research` · `blocked` · `implementing` · `killed` · `qualified`

## Program objective

Find one or more practical mechanisms that improve the quality/cost/risk frontier beyond frozen V1, **or** establish that the best savings opportunity lies at a different routing unit (current model portfolio or Hermes workflow stage).

The program does not assume gains add. A composition is promoted only after its components have independent evidence and their overlap is measured.

## Sub-feature roadmap

| ID | Sub-feature | Core mechanism | Scope boundary | Depends on | Status | Sub-spec |
|---|---|---|---|---|---|---|
| 101 | Counterfactual Shadow Telemetry | randomized sentinels + known propensities + joinable outcomes | learning substrate; does not train the final router | none | implementing (Stage 0 `STAGE0_PASS`; Phase 2-4 telemetry plumbing landed: service/CLI decision logging with join keys, outcome join, data-quality gates, exploration dry-run `disabled`-default; Stage-1 gates measured in `results/101/STAGE1_DATA_QUALITY.md`) | [`../101-counterfactual-shadow-telemetry/spec.md`](../101-counterfactual-shadow-telemetry/spec.md) |
| 102 | Doubly Robust Uplift Router | causal treatment-effect / marginal-gain learning + OPE | current-traffic route-value estimation | 101 for real deployment data | survived-research | [`../102-doubly-robust-uplift-router/spec.md`](../102-doubly-robust-uplift-router/spec.md) |
| 103 | Bayesian Semantic Performance Memory | capability decomposition + measured-outcome retrieval + hierarchical partial pooling | semantics retrieves evidence; never cluster→fixed route | useful outcome history; 101 improves it | survived-research | [`../103-bayesian-semantic-memory/spec.md`](../103-bayesian-semantic-memory/spec.md) |
| 104 | Whitened Latent Marginal-Gain Probe | frozen SLM hidden states + PCA whitening + gain/ranking target | true internal representation; not stored-response shape proxy | labeled train/public data | survived-research | [`../104-whitened-latent-gain-probe/spec.md`](../104-whitened-latent-gain-probe/spec.md) |
| 105 | Conformal Safety Envelope | finite-sample selective-risk calibration/abstention | safety wrapper; does not create ranking signal | any candidate score | survived-research | [`../105-conformal-safety-envelope/spec.md`](../105-conformal-safety-envelope/spec.md) |
| 106 | Sequential Value-of-Information Controller | optimal stopping / marginal correctness-per-cost over actions | decides *what evidence/action to buy next* | candidate signals/verifiers; optional 103/104/105 | survived-research | [`../106-sequential-voi-controller/spec.md`](../106-sequential-voi-controller/spec.md) |
| 107 | Diversity-Optimized Model Portfolio | submodular complementary coverage + rank/select-then-route | changes the candidate model pool before routing | current/public outcome matrices | survived-research | [`../107-diversity-model-portfolio/spec.md`](../107-diversity-model-portfolio/spec.md) |
| 108 | Multi-Fidelity Synthetic→Real Fusion | synthetic as low-fidelity prior + real propensity-corrected truth | uses R7a factory but forbids synthetic-only promotion | 101 + generator factory | survived-research | [`../108-multifidelity-synthetic-real/spec.md`](../108-multifidelity-synthetic-real/spec.md) |
| 109 | Hermes Stage-Aware Router | trajectory/state routing or workflow scheduling | agent mission economics, not RouterBench APGR | replayable/shadow Hermes traces | survived-research | [`../109-hermes-stage-router/spec.md`](../109-hermes-stage-router/spec.md) |

## What was explicitly rejected before specification

The following were researched/reconsidered and **not** promoted to standalone specs:

- **semantic cluster → fixed model**: materially overlaps the already-failed semantic/cluster family and ignores measured local outcomes;
- **generic LLM judge as the arbiter**: prior project evidence shows harmful asymmetric label behavior; selective/conformal judge use may appear only as a bounded evidence source;
- **entropy-only active labeling**: project exp009 falsified the acquisition logic; exploration must instead be identifiable/randomized or coverage/diversity driven;
- **bigger prompt-only classifier / embedding swap**: does not change the information available and is contradicted by both project results and unified routing benchmarks;
- **standalone synthetic-trained router**: R4–R7 showed generator-key fragility, and 2026 generated-data research warns that router quality degrades with generator quality; synthetic evidence must prove transfer to real traffic;
- **indiscriminately adding more models**: model complementarity is real, but broad pools increase routing difficulty/cost; only a budgeted/diversity-optimized pool survives;
- **graph/contrastive semantic router as first move**: too much complexity before the project has reliable real outcome telemetry; park until simpler semantic memory is falsified.

## Stackability and exclusivity map

### Foundation stack — highest priority

`101 telemetry` → (`102 causal uplift` + `103 semantic memory`) → optional `105 conformal envelope`

This is the most coherent path for learning from real Hermes traffic. 101 is not merely observability; it creates the statistical conditions under which 102 and 108 can be evaluated honestly.

### Representation alternative

`104 latent gain probe` can feed 102 or stand beside 103 as a feature/signal. It is **not** intended to be stacked with another high-capacity prompt classifier by default. If 104 and 103 make the same decisions, retain the cheaper/more robust one.

### Runtime controller stack

`106 VOI controller` may consume posterior/confidence information from 103/104/105 and model-pool choices from 107. It is a **meta-policy**; do not implement it before at least one useful action-value signal exists.

### Model-pool alternative

`107 portfolio` can change the weak/mid/frontier set used by 102/103/106. It may make V1's historical pair obsolete. For this reason, **do not compare a 107-derived portfolio to the historical pair without retraining/recalibrating the candidate router on the same pool**.

### Synthetic augmentation stack

`108 synthetic→real` is only valid on top of a real identified data stream from 101. It is not an alternative to 101. Synthetic-only and real-corrected variants are mutually exclusive promotion candidates; the latter must beat a real-only control at matched real-label budget.

### Agentic track

`109 stage-aware routing` is a **separate estimand**. It can coexist in production with any single-turn router, but its success does not validate 102–108 and their success does not validate 109. Run it independently once replayable Hermes trajectories exist.

## Recommended implementation order

### Wave A — repair the learning substrate and establish cheap retrospective tests

1. **101 Counterfactual Shadow Telemetry** — Stage 0 replay simulator first; no live changes until estimator/reconstruction tests pass.
2. **107 Diversity-Optimized Model Portfolio** — $0 public/stored matrix experiment; tells us whether the historical pair is the wrong problem.
3. **103 Bayesian Semantic Performance Memory** — $0 historical/public retrieval experiment; no live traffic required initially.
4. **104 Whitened Latent Gain Probe** — start with representation separability / CV; no API spend before the representation test passes.
5. **105 Conformal Safety Envelope** — calibrate V1 and any early candidates; cheap and useful even if it only proves coverage is low.

### Wave B — causal/current-traffic learning

6. **102 Doubly Robust Uplift Router** — first in full-information simulation, then on propensity-logged shadow data from 101.
7. **108 Multi-Fidelity Synthetic→Real Fusion** — only after a real-label transfer set exists.

### Wave C — composition and alternate unit of decision

8. **106 Sequential VOI Controller** — after at least two distinct useful evidence/actions exist.
9. **109 Hermes Stage-Aware Router** — whenever sufficient trajectory data is available; may proceed independently of Wave B.

## Program-level promotion gates

A component can be labelled `qualified` only when all of the following hold:

1. its own spec's independent falsification and qualification criteria pass;
2. it beats the relevant simple baseline with uncertainty reported;
3. any live-data result has correct provenance/propensity/outcome joins;
4. no sealed test content was accessed;
5. the result is not solely synthetic or oracle-based;
6. cost/latency/maintenance impact is counted;
7. if user-controlled text affects cost routing, basic adversarial-cost robustness has been tested.

A **stack** can be recommended only after marginal contribution/error-overlap ablation. Standalone gains are never arithmetically added.

## Source-of-truth documents

- Research synthesis: [`../../research/2026-09-08-innovation-deep-research.md`](../../research/2026-09-08-innovation-deep-research.md)
- Adversarial review: [`../../research/2026-09-08-adversarial-review.md`](../../research/2026-09-08-adversarial-review.md)
- Branch/repo evidence map: [`../../research/2026-09-08-branch-evidence-map.md`](../../research/2026-09-08-branch-evidence-map.md)
- Research constitution: [`../../.specify/memory/constitution.md`](../../.specify/memory/constitution.md)

## Spec Kit usage

This decomposition follows GitHub Spec Kit's **spec-of-specs** pattern: the roadmap stays shallow, while each sub-feature carries its own intent, requirements, success criteria, implementation plan, and actionable tasks. Agents should implement one sub-spec at a time and use Spec Kit analysis/convergence against that sub-spec rather than trying to implement the entire roadmap in a single context window.
