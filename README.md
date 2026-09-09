# Hermes Router Retraining Research

Research on **cost-effective, adaptive LLM and agentic routing** for [`thepragmatik/hermes-pi-agentic-stack`](https://github.com/thepragmatik/hermes-pi-agentic-stack).

## Current branch status — Router Innovation Program (2026-09-08) — CONVERGED (2026-09-09)

The nine-idea program has **converged** (total paid spend: **$0.00**). Final verdicts:

- **101 Counterfactual Shadow Telemetry — `SHADOW_READY`, deployed to production.** Stage-1 gates all PASS; Phase 2-5 merged (`70d46ca`) and live as the launchd service `com.rath.router-shadow-v1` on 127.0.0.1:8765, verified logging real route decisions with sha256 join keys (no raw prompt text; exploration disabled). See [`results/101/DEPLOY_VERIFICATION.md`](results/101/DEPLOY_VERIFICATION.md).
- **105 Conformal Safety Envelope — `V1_SAFE_SLICE`** (the only qualified routing-relevant component).
- **102, 103, 104, 107, 108 — killed** (negative results, prereg-gated, no thresholds weakened); **106 — `BLOCKED_PREREQ_NOT_MET`**; **109 — `TRACE_DATA_INSUFFICIENT`** (blocked on identified telemetry, not killed).

The frozen V1 router (threshold 0.30, engine `router-v1-frozen`) remains the only deployed router; the best qualified stack is **V1 + the 105 envelope** (not yet wrapped into production). Telemetry now logs real traffic decisions but has **no joined real outcomes yet** (fixtures only) — 102/108 real-data phases stay locked until outcomes accumulate; live exploration is implemented but disabled and requires an operator-countersigned prereg (`experiments/101-live-exploration-prereg.md`). Full detail: [`ideas/INTEGRATION_RECOMMENDATION.md`](ideas/INTEGRATION_RECOMMENDATION.md).

Program origin (historical): this branch was created after:

- the previous router-uplift experiment program mostly failed its frozen gates;
- frozen V1 nevertheless demonstrated real routing value versus weak/random baselines;
- operationalisation showed V1 can run cheaply as an HTTP/in-process shadow service;
- the attempted shadow data collection proved unusable for training because the live HTTP path did not log joinable decisions/outcomes;
- the generator branch improved synthetic-label integrity substantially by R7a, but synthetic evidence remains lower fidelity than real outcomes.

The current objective is **not another large prompt classifier**. The program explores nine materially different mechanisms that change the information source, decision mathematics, model pool, supervision fidelity, or unit of routing.

### Start here

- **Orchestrator launch prompt:** [`ideas/META_PROMPT.md`](ideas/META_PROMPT.md)
- **Idea/dependency index:** [`ideas/README.md`](ideas/README.md)
- **Program status ledger:** [`ideas/STATUS.md`](ideas/STATUS.md)
- **Agent entrypoint:** [`AGENTS.md`](AGENTS.md)
- **Research constitution:** [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- **Spec-of-specs roadmap:** [`specs/router-innovation-2026-09-08/roadmap.md`](specs/router-innovation-2026-09-08/roadmap.md)
- **Deep research synthesis:** [`research/2026-09-08-innovation-deep-research.md`](research/2026-09-08-innovation-deep-research.md)
- **Adversarial review:** [`research/2026-09-08-adversarial-review.md`](research/2026-09-08-adversarial-review.md)
- **Branch evidence map:** [`research/2026-09-08-branch-evidence-map.md`](research/2026-09-08-branch-evidence-map.md)

## Nine implementation-ready Spec Kit ideas

Every idea lives in its own `specs/<idea>/` folder and contains `spec.md`, `plan.md`, `tasks.md`, and a ready-to-paste `PROMPT.md`.

1. **101 Counterfactual Shadow Telemetry** — make shadow traffic statistically learnable with joinable outcomes, exact propensities, safe exploration and off-policy evaluation.
2. **102 Doubly Robust Uplift Router** — learn the marginal benefit of choosing the strong action rather than generic prompt difficulty.
3. **103 Bayesian Semantic Performance Memory** — semantic retrieval of measured historical model outcomes with partial pooling, support and OOD fallback; not cluster→model routing.
4. **104 Whitened Latent Marginal-Gain Probe** — test true local-model hidden states/logits and PCA whitening as a low-cost escalation-value signal.
5. **105 Conformal Safety Envelope** — convert an imperfect router score into explicit risk-vs-coverage selective routing/abstention.
6. **106 Sequential Value-of-Information Controller** — buy the next model/sample/tool/verifier action only when expected information value exceeds cost.
7. **107 Diversity-Optimized Model Portfolio** — choose a small complementary model pool before routing; a better pool may dominate a better router.
8. **108 Multi-Fidelity Synthetic→Real Fusion** — use the R7a generator as low-fidelity prior/direct-model data while real propensity-corrected outcomes remain authoritative.
9. **109 Hermes Stage-Aware Agent Router** — route intelligence by agent workflow stage/state rather than selecting one model for the whole mission.

Use [`ideas/README.md`](ideas/README.md) for prompt links, dependencies, stackability and recommended waves.

## Recommended execution strategy

### Wave A — cheapest information first

Run mostly independently:

- 101 Stage-0 OPE/telemetry simulator;
- 107 current model-portfolio audit;
- 103 train-only semantic performance memory;
- 104 latent representation feasibility/Stage 0;
- 105 safety envelope on V1/current scores.

These are designed to be `$0` API-spend experiments first.

### Wave B — identified learning

- 102 can run retrospective causal replay immediately, but real-data qualification waits for 101;
- 108 can run retrospective synthetic→real transfer immediately, but real deployment claims wait for 101;
- 105 can wrap independently qualified candidates.

### Wave C — composition / different routing unit

- 106 starts only after at least two actions/signals independently pay;
- 109 runs when Hermes mission traces meet its trace-quality gate and remains a separate agentic estimand.

## Governing principle

> **Falsify cheaply, qualify independently, then stack only measured complementary gains.**

A literature-supported idea is not a qualified component. A retrospective replay is not live evidence. Synthetic labels are not real outcomes. Oracle complementarity is not deployability. A failed gate is recorded and stopped rather than relaxed after the result.

## Core guardrails

- RouterBench **test remains sealed**.
- Frozen V1 remains a mandatory control where applicable.
- Historical validation is finalists-only; iteration uses train-only development/holdout protocols.
- Default paid research spend is **$0**. No current idea prompt authorizes paid calls.
- Any paid work requires a new preregistration, current model/provider pricing, explicit cap and fail-closed operator authorization.
- Current model ids/prices must be refreshed at execution time; historical GPT-4/Mistral pairs are historical evidence.
- External/public datasets are evidence amplifiers, not silent exact-pair truth.
- Synthetic data must beat a matched real-only control on real held-out outcomes to earn promotion.
- Semantics may retrieve measured evidence, but semantic cluster→fixed model routing remains retired.
- User-controlled text routing must receive basic adversarial cost-manipulation testing before promotion.

## Historical evidence retained

The 2026-09-06 stackable routing mission remains valuable **historical negative evidence**, not the active execution program on this branch.

Key historical artifacts:

- [`PIVOT_FINAL_RECOMMENDATION.md`](PIVOT_FINAL_RECOMMENDATION.md)
- [`MISSION_LOG.md`](MISSION_LOG.md)
- [`results/P0_MODEL_POOL.md`](results/P0_MODEL_POOL.md)
- [`results/P1_CHEAP_SAMPLING.md`](results/P1_CHEAP_SAMPLING.md)
- [`results/P2_VERIFIERS.md`](results/P2_VERIFIERS.md)
- [`results/P3_INTERNAL_CONFIDENCE.md`](results/P3_INTERNAL_CONFIDENCE.md)
- [`results/P4_TRUST_STACK.md`](results/P4_TRUST_STACK.md)
- [`results/P5_THREE_TIER.md`](results/P5_THREE_TIER.md)
- [`results/P6_WEAK_UPLIFT.md`](results/P6_WEAK_UPLIFT.md)

The generator/shadow operational evidence is preserved on/inherited from `feat/generator-pivot-r0`, including `GENERATOR_PREREG.md` and `results/V1_BASELINE_GAPS.md`.

## Dataset policy

Read [`DATASETS.md`](DATASETS.md) before introducing external data. The current program is especially strict about separating:

- exact-pair/local evidence;
- real current traffic;
- public transfer/stress evidence;
- synthetic low-fidelity evidence.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).