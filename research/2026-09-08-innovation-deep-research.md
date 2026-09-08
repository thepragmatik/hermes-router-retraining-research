# Deep Research — Router Innovation After the Uplift Failures

**Date:** 2026-09-08  
**Status:** research synthesis; implementation claims require their Spec Kit gates to pass  
**Audience:** operator + execution agents

## Executive answer

There is still a credible research case for routing, but the next phase should **not** be another attempt to squeeze signal from the same prompt-only classification setup.

The repository tells a more specific story:

- V1 contains real selection signal and materially beats cost-matched random routing.
- The attempted uplift layers failed because the runtime evidence was weak, redundant or absent.
- The oracle model pool repeatedly showed meaningful headroom, but the deployable system lacked a trustworthy way to identify the winning action.
- The attempted shadow period did not create joinable outcome data, so it could not close that information gap.
- The synthetic generator factory has become cheap and relatively high-integrity, but it has not proved that synthetic routing labels transfer to real Hermes traffic.

The research therefore pivots around three questions:

1. **Can we collect statistically useful real feedback without paying for exhaustive counterfactual labels?**
2. **Can we estimate model/action value with methods aligned to the actual decision instead of generic difficulty?**
3. **Is the biggest saving actually in model-pool design or agent workflow-stage routing rather than the original binary weak/strong decision?**

Nine ideas survived desk research and adversarial review. They are intentionally complementary rather than nine classifier variants.

---

## 1. Counterfactual Shadow Telemetry + Off-Policy Evaluation

### Plain-English idea

The shadow router should behave more like a carefully designed experiment than a debug log.

For a small, safe sample of traffic, record **which alternatives could have been chosen, the probability with which the logged policy chose the action, and a joinable outcome**. That makes it possible to ask: “Would a different routing policy have done better?” without running every model on every request forever.

### Why this is fresh for this repository

The existing shadow wrapper did not log the real HTTP route path, used `prompt_id=0`, had no content hash/join key, and did not join model outcomes. That data cannot support counterfactual learning.

The statistical literature on contextual bandits is explicit: off-policy evaluation relies on the behavior/logging policy and its action propensities. Inverse-propensity (IPS), doubly robust (DR), SWITCH and shrinkage estimators trade bias and variance differently. DR combines a learned reward model with propensity weighting; shrinkage can improve finite-sample behavior.

Relevant sources:

- Wang, Agarwal & Dudík, *Optimal and Adaptive Off-policy Evaluation in Contextual Bandits*, ICML 2017: https://proceedings.mlr.press/v70/wang17a.html
- Su et al., *Doubly robust off-policy evaluation with shrinkage*, ICML 2020: https://proceedings.mlr.press/v119/su20a.html
- Panda et al., *Adaptive LLM Routing under Budget Constraints (PILOT)*, EMNLP Findings 2025: https://aclanthology.org/2025.findings-emnlp.1301/
- Wei et al., *Learning to Route LLMs from Bandit Feedback (BaRP)*, 2025 preprint: https://arxiv.org/abs/2510.07429

### Mathematical stitch

Let `x` be request context, `a` the chosen model/action, `r` the observed quality-minus-cost reward, and `π0(a|x)` the logging propensity. A target policy `π` can be evaluated with IPS:

`V_IPS = mean[ π(a_i|x_i) / π0(a_i|x_i) * r_i ]`

or a DR estimator combining a reward model `m(x,a)` with the propensity correction. The critical point is not the exact estimator—it is that **the propensity and outcome join must exist**.

### Expected benefit

- creates reusable real-current training/evaluation data;
- allows candidate routers to be evaluated before deployment;
- makes model price/model-pool changes easier to simulate;
- provides the real-data anchor needed to use synthetic labels safely;
- transforms shadowing from “health telemetry” into a learning flywheel.

### Important caveat

Exploration can harm users if done carelessly. The spec therefore starts with an offline simulator on RouterBench/full-information matrices and prefers shadow dual-evaluation or low-risk sentinel traffic before any live randomized behavior.

---

## 2. Doubly Robust Causal Uplift Router

### Plain-English idea

Stop asking “is this question hard?” Ask the more useful causal question:

> **What is the expected improvement if I spend the extra money on model B instead of model A for this request?**

This is treatment-effect/uplift estimation applied to routing.

### Why it differs from failed FEV

The project already explored Factorized Escalation Value with sparse/offline labels. The new idea is not “FEV again.” The difference is the **data-generating design and estimator**:

- randomized/known-propensity real feedback from Spec 101;
- causal/DR pseudo-outcomes rather than treating sparse labels as ordinary supervised truth;
- explicit support/overlap diagnostics;
- off-policy evaluation before adoption.

RouteLMT independently reaches a related decision-level conclusion in machine translation: predicting the large-over-small **marginal gain** is better aligned to budgeted routing than estimating absolute quality/difficulty.

Source:

- Luo et al., *RouteLMT: Learned Sample Routing for Hybrid LLM Translation Deployment*, 2026 preprint: https://arxiv.org/abs/2604.22520

### Mathematical stitch

For two actions, estimate conditional treatment effect:

`τ(x) = E[Y(strong) - Y(cheap) | X=x]`

Then route strong when:

`τ(x) > λ * Δcost`

where `λ` reflects the operator's quality/cost exchange rate. In multi-model settings, estimate pairwise/net action advantages and rank feasible actions.

Use cross-fitting and DR/R-learner style pseudo-outcomes so imperfect reward models are corrected by randomized propensity information when overlap exists.

### Expected benefit

- targets the *decision* instead of absolute difficulty;
- naturally adapts to price changes through the decision threshold;
- can learn from partial real feedback rather than all-model labels;
- produces uncertainty/support diagnostics that expose where the router cannot know.

### Caveat

If exploration probabilities are too small or deterministic logging has no overlap, treatment effects are not identifiable. Spec 102 therefore cannot claim live causal value until Spec 101 produces suitable data.

---

## 3. Bayesian Semantic Performance Memory

### Plain-English idea

Use semantics like a **case library**, not a horoscope.

When a new request arrives, retrieve previous *similar-capability* requests and ask: “How did each model actually perform on these kinds of jobs?” Then combine the local evidence with broader task/global evidence, weighting the result by how much support exists.

### Why semantic routing remains viable

The failed semantic family mapped clusters/representations toward route labels. Two 2026 papers point to a materially different pattern:

- **ContextualRouter** retrieves similar historical queries and estimates each model's performance from measured past outcomes; even simple kNN performs competitively and remains useful with sparse history.
- **DecoR** argues direct surface-query mapping falls into a memorization trap and instead decomposes queries into capability requirements before historical matching.

Sources:

- Varangot-Reille et al., *Generalising LLM Routing using Past Performance Retrieval*, EACL 2026: https://aclanthology.org/2026.eacl-srw.22/
- Lv et al., *Beyond Query Memorization: ... Query Decomposition and Historical Matching (DecoR)*, ACL 2026: https://aclanthology.org/2026.acl-long.1852/

### Statistical stitch: hierarchical partial pooling

A naive kNN mean is noisy in sparse neighborhoods. Add empirical-Bayes/hierarchical shrinkage:

`local_estimate = w(n_eff) * neighbor_rate + (1-w(n_eff)) * task/global_prior`

where `w` rises with effective neighborhood support and falls with distance/dispersion. Maintain a posterior or interval per model/action rather than one naked score.

Capabilities (reasoning, code, extraction, tool use, long-context, etc.) should be represented separately where possible so two linguistically similar prompts with different functional demands are not assumed equivalent.

### Expected benefit

- continually improves as real outcomes accumulate;
- adapts to new models with less retraining than a monolithic classifier;
- offers human-auditable evidence (“these similar jobs had these outcomes”);
- naturally supplies OOD/support signals;
- can feed the causal router or sequential controller.

### Caveat

Similarity can be confidently wrong, especially under embedding anisotropy or surface-form shortcuts. Low-support regions must shrink toward conservative priors, and capability-decomposition must be ablated against plain retrieval.

---

## 4. Whitened Latent Marginal-Gain Probe

### Plain-English idea

The previous “answer-aware” test did **not** actually look inside the cheap model—it only saw stored response shape, weak verifiers and V1's score.

A fresh test can inspect the cheap/local model's internal representation, correct the geometry, and train a tiny probe to estimate **which model would add value**.

### Research basis

LatentGate finds that ordinary embedding routers can collapse because hidden representations are anisotropic; it uses frozen SLM hidden states, PCA whitening and a lightweight probe, with a particularly large OOD ablation hit when whitening is removed. Self-REF separately shows that learned confidence signals can improve routing/rejection versus verbal or token-probability baselines.

Sources:

- Ratnakar et al., *LatentGate*, ACL Industry 2026: https://aclanthology.org/2026.acl-industry.153/
- Chuang et al., *Learning to Route LLMs with Confidence Tokens (Self-REF)*, ICML 2025: https://proceedings.mlr.press/v267/chuang25b.html

### Mathematical stitch

Extract hidden representation `h(x)` from a frozen cheap SLM, then transform:

`z = Λ^{-1/2} U^T (h - μ)`

using PCA eigenvectors/eigenvalues fitted on **train-only** data. A linear/listwise probe predicts marginal gain or pairwise model preference.

Do not default to “is weak correct?”; use the decision-aligned target where full labels allow it.

### Expected benefit

- genuinely new representation relative to BGE prompt embeddings and P3 response-shape features;
- lightweight inference/retraining if a small frozen model is used;
- may expose functional distinctions lost in sentence-embedding geometry;
- can be task-conditioned and fused with semantic memory/causal estimates.

### Caveat

Internal signals are task-dependent. A 2026 line of work on self-knowledge suggests hidden-state correctness information can be stronger in some factual settings than math. A probe must be allowed to be disabled per task family. No “latent magic” assumption.

---

## 5. Conformal Safety Envelope

### Plain-English idea

This idea does not try to make the router smarter. It tries to make **using a router safer**.

Given any score saying “cheap model is probably safe,” calibrate a threshold so the system can control the empirical error rate among cheap-routed cases, with an explicit confidence target—then abstain/escalate when support is inadequate.

### Research basis

Uddin & Bauer's ACL 2026 work applies conformal calibration to LLM routing and controls the violation rate among cheap-routed queries under stated assumptions; routability varies substantially by task/model pair.

Source:

- Uddin & Bauer, *Conformal LLM Routing with Distribution-Free Safety Guarantees*, ACL 2026: https://aclanthology.org/2026.acl-srw.70/

Selective conformal judging work such as SCOPE also supports the broader principle that an uncertain evaluator should abstain rather than force every example into a label:

- Badshah et al., *SCOPE*, 2026 preprint: https://arxiv.org/abs/2602.13110

### Statistical stitch

For a calibrated score and a target violation rate `α`, choose an acceptance threshold using a finite-sample binomial/Clopper-Pearson procedure at confidence `1-δ`. For heterogeneous tasks, use Mondrian/group calibration only where there is enough calibration mass; otherwise fall back to a broader group.

### Expected benefit

- converts a score into an explicit risk/coverage trade-off;
- provides a deployable abstention policy instead of arbitrary threshold tuning;
- useful with V1, semantic memory, latent probes or causal scores;
- especially valuable when distribution shift means “confidence” should reduce coverage rather than silently fail.

### Caveat

Conformal guarantees rely on assumptions about calibration/deployment exchangeability. Under temporal drift they are not timeless guarantees. Spec 105 requires time-split/drift analysis and describes the result as a calibrated envelope for a defined population, not a universal safety certificate.

---

## 6. Sequential Value-of-Information (VOI) Controller

### Plain-English idea

Instead of one routing decision, ask repeatedly:

> **What is the cheapest next action that is worth buying?**

Possible next actions include: accept the cheap answer, sample the cheap model again, run a calculator/test/tool, query a different cheap model, call a mid-tier model, or escalate to frontier.

### Research basis

BEST-Route jointly decides model and test-time sample count and reports substantial cost reductions in its evaluated datasets. Confidence-informed/adaptive self-consistency methods show repeated sampling does not need to be fixed-N. A 2026 preprint explicitly frames “resample or reroute” as competing uses of the same per-query budget and optimizes marginal correctness per unit cost.

Sources:

- Ding et al., *BEST-Route*, ICML 2025: https://proceedings.mlr.press/v267/ding25d.html
- Taubenfeld et al., *Confidence Improves Self-Consistency*, ACL Findings 2025: https://aclanthology.org/2025.findings-acl.1030/
- Kim et al., *Reliability-Aware Adaptive Self-Consistency*, ACL Findings 2026: https://aclanthology.org/2026.findings-acl.1085/
- Chen, *Resample or Reroute?*, 2026 preprint: https://arxiv.org/abs/2607.08665

### Mathematical stitch

At state `s` (prompt + evidence collected so far), estimate for each available information/action `a`:

`VOI(a|s) = E[best downstream utility after observing a | s] - current best utility - cost(a)`

Choose the action with positive highest VOI; stop when no action has positive expected value or a risk envelope forces escalation.

An approximate implementation can use calibrated action-value regressions rather than solve a full POMDP.

### Expected benefit

- avoids paying for every layer on every request;
- naturally arbitrates “resample vs reroute vs verify”;
- can turn modest independent signals into an efficient adaptive policy;
- price changes can update action costs without retraining every feature.

### Caveat

A VOI controller amplifies bad probability estimates. It must not be built first. It is a composition layer after at least one or two useful evidence/action-value signals exist.

---

## 7. Diversity-Optimized Model Portfolio + Select-then-Route

### Plain-English idea

A router cannot create complementarity that the model pool does not have. Before optimizing the router, choose a **small portfolio whose mistakes differ**.

The best third model is not necessarily the third-highest leaderboard model—it is the one that cheaply solves cases the current models miss.

### Research basis

LLMRouterBench (400K+ instances, 21 datasets, 33 models) confirms strong model complementarity but finds many sophisticated routers surprisingly similar and some fail simple baselines. Select-then-Route narrows the model pool by task taxonomy before routing. Recent 2026 selection-valid diagnostics also formalize compact-pool building as a complementary-coverage/submodular problem with a greedy `(1-1/e)` guarantee under the stated formulation.

Sources:

- Li et al., *LLMRouterBench*, ACL Findings 2026: https://aclanthology.org/2026.findings-acl.1881/
- Shah & Shridhar, *Select-then-Route*, EMNLP Industry 2025: https://aclanthology.org/2025.emnlp-industry.28/
- Shihab et al., *Opportunity Is Not Realizability*, 2026 preprint: https://arxiv.org/abs/2608.08265
- Lai & Ye, *When Routing Collapses / EquiRouter*, 2026 preprint: https://arxiv.org/abs/2602.03478

### Mathematical stitch

Define a set function for portfolio `S` such as:

`F(S) = weighted expected complementary success/rescue coverage - λ * expected cost - γ * redundancy`

For coverage-like monotone submodular formulations, greedy addition chooses the model with largest marginal gain per cost at each step. Then train/evaluate routing **within** the curated small pool, possibly with pairwise/listwise ranking rather than pointwise scalar regression.

### Expected benefit

- may make the original historical Mistral/GPT-4 boundary irrelevant;
- reduces decision complexity and provider switching;
- creates a more learnable pool with genuine niches;
- can lower both routing error and runtime cost even before a fancy router.

### Caveat

Current model prices/performance change quickly. Public benchmark matrices are stress-test evidence, not Hermes truth. A tiny current-pool real pilot remains necessary before operational conclusions.

---

## 8. Multi-Fidelity Synthetic→Real Label Fusion

### Plain-English idea

Keep the synthetic factory, but stop asking it to be the judge and jury.

Treat its labels as **cheap hints**. Use a smaller amount of real, propensity-logged Hermes outcome data to correct the synthetic model and measure whether synthetic data actually saves real labeling.

### Research basis

ACL 2026 work on routing with generated data finds that generated-data routers depend strongly on generator quality; effective generators must answer their own questions accurately and generate questions that differentiate the model pool. That resonates directly with this repo's R4 wrong-key discovery and R7a strict self-consistency filtering.

Source:

- *Routing with Generated Data: Annotation-Free LLM Skill Estimation and Expert Selection*, ACL 2026: https://aclanthology.org/2026.acl-long.1498/

CANDOR provides a useful statistics lesson from another domain: imperfect counterfactual annotations can make off-policy estimates worse; incorporating imperfect annotations only into the direct/reward-model component of a doubly robust estimator is more robust than using them as if they were observed outcomes.

- Mandyam et al., *CANDOR*, CHIL/PMLR 2026: https://proceedings.mlr.press/v333/mandyam26a.html

### Mathematical stitch

Model fidelity explicitly. Let `Y_real` be the target outcome and `Y_syn` a noisy auxiliary label. Learn a direct model with both, optionally with a per-capability reliability weight, but compute policy value/correction from real randomized outcomes:

`DR(real propensities, reward_model(real + synthetic features/prior))`

This prevents cheap synthetic labels from directly carrying the statistical authority of real outcomes.

### Expected benefit

- may turn the R7a generator work into useful leverage instead of discarding it;
- could reduce real counterfactual sample requirements;
- cheap synthetic data can improve representations and rare-capability coverage;
- reliability can be learned by capability/task bucket.

### Caveat

This idea is killed immediately if synthetic+small-real does not beat a real-only model at the **same real-label budget** on real holdout/outcome data. Synthetic-only success does not count.

---

## 9. Hermes Stage-Aware Routing / Workflow Scheduling

### Plain-English idea

The most valuable router may not answer “which model handles this whole user prompt?”

For an agent, the better question can be:

> **At what moments in the mission is expensive intelligence actually worth it?**

A cheap model may be perfectly adequate for file reads, mechanical edits and routine tool calls, while strong reasoning matters at planning, synthesis, repeated failure, recovery or high-impact review.

### Research basis

MTRouter learns turn-level utility from logged multi-turn trajectories and reports strong performance/cost gains in ScienceWorld/HLE. LLM-as-Scheduler chooses workflow depth dynamically and reports 43% fewer tokens and >36% lower latency with limited accuracy loss in its evaluation.

Sources:

- Zhang et al., *MTRouter*, ACL 2026: https://aclanthology.org/2026.acl-long.2045/
- Xiang et al., *LLM-as-Scheduler*, ACL 2026: https://aclanthology.org/2026.acl-long.581/

### Mathematical stitch

Treat the agent trajectory as a state sequence. Estimate the advantage of strong capability at stage `t` conditional on state/history:

`A_strong(s_t) = E[mission_utility | strong at t, s_t] - E[mission_utility | cheap at t, s_t]`

State features can include progress, repeated failures, tool/test outcomes, context length, task phase and model switches. Start with interpretable heuristics before learned stage policies.

### Expected benefit

- attacks the cost unit that Hermes actually pays across long missions;
- can save more than single-turn routing if expensive calls cluster at a few critical stages;
- uses real tool/test/progress signals unavailable in RouterBench;
- may remain valuable even if single-turn prompt routing plateaus.

### Caveat

This is a separate estimand. It needs replayable or shadow Hermes trajectories and mission-level acceptance outcomes. RouterBench APGR cannot qualify it.

---

## Cross-cutting security finding

A 2026 ACL paper demonstrates that cost-aware routers can be attacked with adversarial suffixes that bias them toward expensive models. Any promoted routing policy exposed to user text should therefore include cost-manipulation robustness tests rather than assume economic routing is purely an accuracy problem.

Source:

- Tang et al., *Route to Rome Attack*, ACL 2026: https://aclanthology.org/2026.acl-long.2051/

---

## Why these nine survive as a portfolio of ideas

They address different bottlenecks:

| Bottleneck | Surviving idea |
|---|---|
| no trustworthy live counterfactual data | 101 telemetry/OPE |
| wrong supervised target / biased partial feedback | 102 causal uplift |
| semantics not tied to outcomes | 103 Bayesian performance memory |
| prompt embeddings lack functional information | 104 latent whitened probe |
| score thresholds have uncontrolled risk | 105 conformal envelope |
| static stacks pay for unnecessary evidence | 106 VOI controller |
| historical model pair/pool may be obsolete | 107 portfolio optimization |
| synthetic factory may help but is not truth | 108 multi-fidelity fusion |
| prompt-level routing may be the wrong unit | 109 stage-aware agent routing |

This is also why they should not all be built at once. The roadmap orders them by prerequisite and early falsifiability.

## Overall research thesis

The strongest remaining hypothesis is **not** that one new architecture will suddenly predict the oracle.

It is that router improvement becomes more plausible when the system:

1. collects identified real feedback;
2. predicts incremental action value rather than generic difficulty;
3. retrieves measured local outcomes with calibrated uncertainty;
4. uses richer internal/state representations only where they add information;
5. chooses a compact complementary model portfolio;
6. buys additional evidence only when its value exceeds its cost;
7. treats synthetic data as low-fidelity auxiliary evidence;
8. routes agentic capability at the stage where it changes mission outcomes.

If these approaches fail under their early gates, the failure will be more decisive than another classifier failure: it would imply the remaining oracle opportunity is not realistically recoverable from affordable observables/feedback, and the project should simplify rather than keep searching.
