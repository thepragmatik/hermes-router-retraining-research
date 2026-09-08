# Adversarial Review — Router Innovation Candidates

**Date:** 2026-09-08  
**Review standard:** an idea survives only if it is materially different from failed project work, has a plausible causal/mechanical path to improvement, can be falsified early, and does not depend on oracle information at deployment.

## Review lenses

Each candidate was attacked from eight directions:

1. **Novelty relative to this repo:** is it actually new or a renamed failed experiment?
2. **Identification/information:** does the data contain what the method needs to know?
3. **Economic mechanism:** why would it improve total cost/quality rather than a proxy metric?
4. **Robustness:** what happens under OOD/task variation/adversarial input?
5. **Synthetic/judge contamination:** could noisy low-fidelity evidence dominate real outcomes?
6. **Implementation burden:** can we prove or kill it before expensive systems work?
7. **Composition:** does it add independent information or duplicate another survivor?
8. **Project fit:** does it help Hermes rather than merely score well on a routing paper benchmark?

## Summary verdict

Nine candidates survive research review. Survival means **worth a disciplined implementation test**, not likely-successful by assumption.

| ID | Idea | Novelty | Earliest cheap falsification | Research verdict | Stack role |
|---|---|---|---|---|---|
| 101 | Counterfactual Shadow Telemetry | very high project relevance | full-information replay → pretend bandit logs → OPE reconstruction | **SURVIVE / prerequisite** | foundation |
| 102 | DR Causal Uplift Router | high if powered by 101 | simulated logged feedback vs full-info policy value | **SURVIVE** | core learner |
| 103 | Bayesian Semantic Performance Memory | high vs failed clusters | 1–5% outcome-memory CV + support calibration | **SURVIVE** | evidence signal |
| 104 | Whitened Latent Gain Probe | high; true internal states never tested | representation geometry/separability + train CV | **SURVIVE, conditional** | alternative signal |
| 105 | Conformal Safety Envelope | high as deployment wrapper | calibrate V1 score and measure useful risk/coverage | **SURVIVE** | safety wrapper |
| 106 | Sequential VOI Controller | high | retrospective action-value replay after signals exist | **SURVIVE, delayed** | meta-controller |
| 107 | Diversity-Optimized Model Portfolio | high with current pool | public/stored matrix greedy subset vs baselines | **SURVIVE** | model-pool alternative |
| 108 | Multi-Fidelity Synthetic→Real | high relative to R7a | synthetic vs real-only matched-label transfer test | **SURVIVE, depends on 101** | data augmentation |
| 109 | Hermes Stage-Aware Router | very high strategic relevance | mission-trace heuristic replay | **SURVIVE, separate estimand** | agentic track |

---

# Survivor reviews

## 101 — Counterfactual Shadow Telemetry

### Strongest case against

“Telemetry does not improve the router. It is plumbing. We could spend weeks building logging infrastructure and still have no better model.”

### Response

That criticism is correct if the telemetry is ordinary logging. It is wrong for **identified experimental telemetry**.

The existing project cannot learn real treatment/model effects from its shadow stream because the live route path was not logged and outcomes are not joinable. A deterministic log without known action probabilities also cannot reliably evaluate policies that choose actions outside its support. In this project, the data limitation is now a direct blocker to several otherwise plausible ideas.

The spec therefore defines 101 as a **statistical substrate feature**, not an ops cleanup. It must prove on a full-information replay that the logging schema + estimators can recover known policy values before any live work.

### Failure modes

- sentinel traffic too sparse → high-variance estimates;
- propensities accidentally omitted or recomputed incorrectly;
- delayed outcomes cannot be joined;
- user-visible randomized actions cause harm;
- randomization distribution gives poor overlap for candidate policies;
- logging itself introduces privacy/security issues.

### Mitigation / kill

Prefer shadow dual-evaluation where possible; cap live randomized sentinel rates; exclude high-risk traffic; write propensity unit tests; simulate OPE coverage first. Kill the causal-use claim if replay estimators cannot rank known candidate policies with acceptable error/interval coverage.

### Verdict

**SURVIVE — highest priority.** It fixes a demonstrated project defect and enables better science even if no router ultimately wins.

---

## 102 — Doubly Robust Causal Uplift Router

### Strongest case against

“This is just FEV with more statistics vocabulary. Sparse-label FEV already failed.”

### Response

This would indeed be a disguised rerun if trained on the same sparse deterministic labels with the same assumptions.

The survivor is explicitly conditional on a different identification regime:

- known-propensity randomized/dual outcomes from 101;
- cross-fitted direct reward models;
- propensity correction/DR estimation;
- support diagnostics;
- policy selection by off-policy value, not ordinary classifier accuracy.

The target is still conceptually related to escalation value because that is the economically correct question; the innovation is **how that effect is identified and estimated under deployment-like partial feedback**.

### Failure modes

- weak overlap makes weights explode;
- reward proxy is not accepted-work quality;
- treatment effects too heterogeneous/noisy to learn;
- confounding if supposedly randomized choices are not actually randomized;
- cost changes make fixed utility weights stale;
- OPE model-selection optimism from comparing many policies.

### Mitigation / kill

Use randomized propensities, clipping/shrinkage/SWITCH diagnostics, cross-fitting, held-out OPE, simultaneous/confident bounds for finalist comparison, and sensitivity to reward definition. Kill if simulated partial-feedback training cannot recover a meaningful fraction of the full-information policy frontier before live use.

### Verdict

**SURVIVE — core learner, but only after 101.**

---

## 103 — Bayesian Semantic Performance Memory

### Strongest case against

“Semantic routing already failed. kNN on embeddings is another semantic router and will just reproduce the same failure.”

### Response

This is the most important semantic distinction in the review.

The failed pattern assigns a route based on cluster/representation membership. The proposed memory retrieves **measured model outcomes** from similar historical cases, estimates local action performance, reports effective support, and shrinks sparse local estimates toward task/global priors.

It is therefore closer to case-based empirical performance estimation than semantic classification. ContextualRouter and DecoR provide current evidence for this historical-matching pattern, including OOD/capability-decomposition motivation.

### Failure modes

- embedding neighborhood is surface-similar but capability-different;
- high-dimensional distance concentration/anisotropy;
- repeated templates make CV look better than real generalization;
- sparse neighborhoods produce extreme noisy rates;
- history becomes stale after model/version changes;
- rare but high-impact requests have no neighbors.

### Mitigation / kill

Capability decomposition; dedupe by template/source; time/model-version keyed memory; empirical-Bayes shrinkage; effective-sample-size thresholds; OOD fallback; compare plain kNN, capability kNN and partial pooling. Kill if local-history features fail to improve performance estimation/calibration at 1–5% memory or if gains vanish under template-grouped/OOD splits.

### Verdict

**SURVIVE — semantic routing in a materially different role.**

---

## 104 — Whitened Latent Marginal-Gain Probe

### Strongest case against

“We tried BERT/embeddings and an answer-aware probe. A hidden-state probe is another classifier with prettier features.”

### Response

The repository's P3 explicitly says true hidden states/logprobs were unavailable and were not tested. LatentGate provides evidence that the geometry of ordinary embeddings can collapse functional distinctions and that PCA whitening can materially change OOD separability in an agent-routing task.

This is still a learned classifier/probe and therefore carries high falsification risk. It survives because it accesses **new information** (frozen causal-LM internal representations) and uses a decision-aligned marginal-gain/ranking target rather than ordinary task difficulty.

### Failure modes

- latent representation predicts topic rather than correctness/gain;
- signal is task-specific and absent on math/coding;
- probe overfits benchmark templates;
- whitening fit leaks validation distribution;
- local inference overhead removes savings;
- model upgrade changes representation geometry and requires refresh.

### Mitigation / kill

Train-only PCA; grouped/OOD splits; compare BGE vs raw latent vs PCA vs whitened latent; per-task ablation; record inference latency; probe marginal gain and pairwise ranking, not only correctness. Kill before any live integration if whitened representation provides no stable out-of-fold lift over V1/BGE on decision-aligned metrics.

### Verdict

**SURVIVE, conditional and high-risk/high-upside.** Do not build a large neural router around it before the tiny probe proves signal.

---

## 105 — Conformal Safety Envelope

### Strongest case against

“Calibration cannot create information. If the underlying router is mediocre, conformal calibration just sends everything strong.”

### Response

Correct. This is not an uplift method. It survives because **deployability and risk control are a different requirement from ranking quality**.

A useful score may be unsafe under arbitrary threshold tuning; a conformal envelope can expose the coverage at which cheap routing meets a declared risk tolerance. If coverage is near zero, that is valuable negative evidence.

### Failure modes

- exchangeability broken by time drift;
- too little calibration data in task strata;
- marginal guarantee hides subgroup failure;
- operator chooses an alpha too permissive for the use case;
- repeated threshold experimentation consumes calibration validity.

### Mitigation / kill

Time-split calibration checks; hierarchical/Mondrian strata only with adequate sample size; calibration exposure log; fallback to strong/OOD; report coverage and subgroup empirical risk. Kill as an active layer if it cannot retain useful cheap coverage at the required risk; it may remain an evaluation tool.

### Verdict

**SURVIVE — wrapper, not router replacement.** It is stackable with any score and should never be credited for ranking uplift.

---

## 106 — Sequential Value-of-Information Controller

### Strongest case against

“This is a complexity explosion. The previous stack already showed that adding layers can cost more and get worse.”

### Response

That is exactly why this method is **delayed**. A static stack pays for layers whether or not they are useful. A VOI controller is only justified after individual evidence sources/actions show measurable value. Its purpose is to avoid paying the whole stack.

The literature on adaptive sampling/BEST-Route and resample-vs-reroute supports treating compute choices as a sequential budget-allocation problem.

### Failure modes

- badly calibrated action values cause expensive loops;
- independence assumptions double-count correlated evidence;
- latency from sequential calls dominates token savings;
- controller becomes a hard-to-debug POMDP;
- verifier quality is insufficient, repeating P1/P2 failures.

### Mitigation / kill

Start with a one-step myopic VOI approximation and no more than 3–4 actions; enforce max-call/max-latency budget; learn action values from held-out replay; compare against simple static policies; add evidence sources one at a time. Kill if a myopic controller cannot beat the best static policy on retrospective data; do not escalate to RL/planning complexity.

### Verdict

**SURVIVE, but Wave C only.** It is not permission to rebuild a seven-layer stack.

---

## 107 — Diversity-Optimized Model Portfolio

### Strongest case against

“We already screened a model pool in P0 and chose Yi. Adding more models will just increase cost and decision complexity.”

### Response

P0 was useful and should be kept as evidence. The new hypothesis is more specific:

- use current/public many-model outcome matrices;
- optimize **subset complementary coverage under cost**, not individual rescue-per-dollar only;
- test small portfolio sizes (2–4), not large ensembles;
- optionally use pairwise/listwise ranking aligned to the final decision.

Unified 2026 benchmarks suggest model complementarity is real while router-algorithm differences are often surprisingly small, which increases the prior that pool curation is a high-leverage variable.

### Failure modes

- public matrices do not transfer to Hermes;
- benchmark-selected specialists are unavailable/routeability-constrained;
- diversity objective selects expensive eccentric models;
- model/version churn makes pool optimization stale;
- more candidates increase routing collapse/noise.

### Mitigation / kill

Hard maximum portfolio size; provider/privacy constraints in the objective; current price snapshot; public $0 Stage 0 followed by tiny real-current validation; penalize redundancy and switching cost. Kill if a compact pool cannot beat the historical pair's oracle/realizable frontier in public stress tests or if real-current candidates are too correlated.

### Verdict

**SURVIVE — plausible alternative to router-side complexity.**

---

## 108 — Multi-Fidelity Synthetic→Real Fusion

### Strongest case against

“The generator already produced wrong answer keys. Synthetic data can poison the router, and a strict filter with 26% yield may only select easy/unnatural questions.”

### Response

Both objections are accepted. This is why the standalone synthetic-router idea is rejected.

The survivor treats R7a output as low-fidelity auxiliary information and makes **real transfer** the primary gate. CANDOR provides a useful statistical template: imperfect counterfactual annotations can hurt, while using them inside the direct/reward-model component of a DR estimator is more robust than treating them like observed outcomes.

### Failure modes

- synthetic distribution mismatch;
- strict filtering creates selection bias toward easy/mechanical tasks;
- generator/model-family artifacts become shortcut features;
- key accuracy audit is too small;
- synthetic volume overwhelms real labels;
- synthetic model pair differs from deployment pool.

### Mitigation / kill

Synthetic/real source flag; source-balanced training; reliability weights by capability; dedupe/domain-distance audits; real-only control at identical real-label budget; use synthetic data as representation/prior/DM input, not propensity outcome. Kill if synthetic+real does not beat real-only on **real** holdout at matched real supervision.

### Verdict

**SURVIVE only as multi-fidelity fusion. Standalone synthetic training is REJECTED.**

---

## 109 — Hermes Stage-Aware Router

### Strongest case against

“This abandons the original RouterBench problem instead of solving it. Agent trajectories also introduce delayed rewards and confounding.”

### Response

It is intentionally a separate track because Hermes' true cost unit is a multi-turn mission. Single-turn routing may have limited realizable headroom while mission-stage allocation can still be valuable.

MTRouter and LLM-as-Scheduler provide recent evidence that turn/history/workflow state can support cost-aware decisions. More importantly, Hermes has signals unavailable in RouterBench: tool/test outcomes, repeated failures, no-progress loops, stage, context length and accepted mission results.

### Failure modes

- no stable mission-success label;
- logged trajectories are confounded by existing policy/model choices;
- stronger models alter future state, making one-step replay invalid;
- switching models harms coherence;
- stage features become brittle implementation heuristics.

### Mitigation / kill

Start with descriptive causal audit and simple heuristic replay; measure strong-call contribution by stage; avoid claiming counterfactual causality from deterministic logs; use randomized/shadow stage interventions only after telemetry design; count switches/retries/latency. Kill if expensive calls are not concentrated in identifiable stages or simple stage rules cannot improve mission cost without quality loss.

### Verdict

**SURVIVE as an independent strategic track.** It can coexist with per-turn routing but has separate qualification.

---

# Rejected / parked ideas

## R1 — Pure semantic clustering / graph routing

**REJECT.** Too close to prior failed semantic/cluster work. Graph construction adds complexity without solving the missing outcome/identification issue. Revisit only if 103 demonstrates local outcome-memory value and graph structure supplies a clear incremental signal.

## R2 — Generic LLM judge arbiter

**REJECT as primary mechanism.** The project already measured asymmetric judge errors and a judge-trained router regression. Judges may appear only as selective/calibrated low-fidelity evidence with an abstention/error audit.

## R3 — Entropy-only active learning

**REJECT.** Prior entropy-guided acquisition underperformed uniform/anchor controls. If exploration is needed, use known-propensity sentinel designs or coverage/diversity selection, not uncertainty score alone.

## R4 — Bigger prompt-only classifier / embedding replacement

**REJECT.** It does not materially change the information set. LLMRouterBench also warns that many complex routers fail to exceed simple baselines and embedding-backbone choice often has limited leverage.

## R5 — Standalone synthetic router

**REJECT.** Generator-key failures in-project plus generated-data literature make transfer too uncertain. Only 108's real-corrected multi-fidelity design survives.

## R6 — Large model ensemble

**REJECT.** Portfolio size must stay small and cost-aware. 107 optimizes complementarity explicitly; “more models” is not a hypothesis.

## R7 — Full RL/POMDP controller immediately

**REJECT as first implementation.** 106 starts with a myopic/finite-action VOI policy. Escalating to RL requires evidence that sequential allocation itself pays.

---

# Exclusivity / composition conclusions

1. **101 is foundational, not optional, for real causal learning.** It can be implemented even if every router idea fails because it fixes the current shadow-data defect.
2. **102 and a pure deterministic supervised router are alternative training paradigms on the same real traffic.** Compare them; do not combine propensities into a model and call it causal without an OPE design.
3. **103 and 104 are potentially stackable but likely redundant.** First compare independently. Only combine if error-overlap shows unique value.
4. **105 stacks with any score** but contributes safety/calibration, not ranking lift.
5. **106 consumes other components; it should not exist if there is only one useful action/signal.**
6. **107 changes the action/model set.** Results from the historical pair cannot be mechanically carried forward; downstream routers need recalibration/retraining.
7. **108 synthetic-only and synthetic+real promotion are mutually exclusive: synthetic-only is already rejected.**
8. **109 is a separate evaluation track.** It may coexist operationally with single-turn routing, but its evidence is mission-level and must stay separate.

# Final research recommendation

Start with **101, 107, 103, 104 and 105** because their earliest tests are cheap and answer different questions. Use those results to decide whether **102** has a strong real-current signal worth learning. Only then consider **108** and **106**. Run **109** independently as soon as usable Hermes trajectories exist.

The program should prefer a decisive kill over repeated tuning. The highest-value outcome is not “nine ideas implemented”; it is identifying the smallest set of mechanisms that genuinely changes the router's information or action frontier.
