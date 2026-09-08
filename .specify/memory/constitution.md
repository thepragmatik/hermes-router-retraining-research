# Router Innovation Research Constitution

**Version:** 1.0.0  
**Ratified:** 2026-09-08  
**Scope:** `research/router-innovation-2026-09-08` and all descendant implementation branches/specs.

This constitution governs the next router-innovation phase. It exists because the previous work produced useful negative evidence, but also demonstrated that a technically plausible router experiment can be invalidated by weak supervision, biased logging, incomplete telemetry, noisy synthetic keys, or an evaluation design that asks a question the available data cannot identify.

The governing principle is:

> **Improve the information, the decision mathematics, or the unit of routing — not merely the size of the classifier.**

## I. Frozen evidence is evidence

The following are treated as established project evidence unless a materially different hypothesis is preregistered:

- frozen V1 is a real, useful baseline and must remain reproducible;
- prompt-only/embedding-only variants that simply revisit earlier classifier/cluster ideas are not fresh hypotheses;
- disagreement-as-escalation, broad format/verifier gates, the stored-response P3 probe, and the previous stack composition did not clear their gates;
- generic symmetric LLM-judge supervision has already shown harmful label asymmetry;
- entropy-only acquisition and the prior partial-label families are not to be rerun unchanged;
- the previous shadow wrapper did not create usable training data because its live service did not log joinable decisions/outcomes;
- synthetic labels are not ground truth merely because a generator can emit a verifier/key.

An experiment may revisit a family only when the new spec states precisely what new information, identification assumption, representation, target, or data-generating process makes it materially different.

## II. RouterBench test remains sealed

The RouterBench test split MUST NOT be inspected, scored, deduplicated against, sampled from, embedded for experiment selection, or used indirectly. Hash-only integrity checks are allowed if they do not load content.

Historical validation has already been consulted repeatedly. New work MUST use train-only cross-validation or a deterministic train-derived development/holdout protocol for iteration. Historical validation is reserved for preregistered finalists only, with every exposure logged before results are consumed.

## III. V1 is the mandatory control, not the presumed winner

Every applicable experiment MUST compare against the frozen V1 policy and at least one simple baseline appropriate to the new problem.

V1 may be replaced only by evidence. A new method is not useful merely because it has higher AUROC/F1/NDCG; it must improve an end-to-end quality/cost/risk frontier, unlock trustworthy learning data, or retire a material reliability risk.

## IV. Learning telemetry is part of the algorithm

Any live/shadow learning design MUST be identifiable and joinable by construction.

At minimum, a learning record MUST carry:

- stable request/message/session join key or privacy-preserving content hash;
- timestamp and traffic stratum;
- router/model versions;
- available action set;
- chosen action;
- logging propensity for the chosen action when randomized exploration is used;
- score/decision metadata needed to reproduce the policy;
- model/provider/revision and price snapshot;
- outcome join status and outcome provenance;
- explicit distinction between observed factual outcomes, delayed proxy outcomes, human/user acceptance, model-judge annotations, and synthetic labels.

A shadow stream that records only a decision/confidence without an outcome join is observability, not training data.

## V. Safe exploration before clever learning

Counterfactual learning requires coverage. The preferred mechanism is a small, preregistered randomized sentinel or dual-evaluation slice on policy-safe, low-risk traffic where doing so does not alter user-visible behavior.

Randomization MUST:

- be bounded by explicit rate/cost caps;
- record exact propensities;
- exclude security/high-impact/privacy-sensitive strata unless separately approved;
- use shadow/dual evaluation rather than live behavioral exploration whenever practical;
- have a kill switch and observability tests;
- never be inferred after the fact from deterministic logs.

If the data were not collected with known action probabilities, do not pretend they support unbiased inverse-propensity estimates.

## VI. Outcomes have a reliability hierarchy

Evidence priority for immediate Hermes decisions is:

1. real, task-native accepted outcome / deterministic verification / tests / tools;
2. controlled human or high-quality operational acceptance signal;
3. randomized real model outcomes with a validated grader;
4. trusted benchmark outcomes;
5. calibrated/selective judge labels with measured error;
6. synthetic/generated labels.

Lower-fidelity evidence MAY be used as a prior, representation-learning signal, reward-model feature, or proposal distribution. It MUST NOT silently override higher-fidelity evidence.

The R7a generator factory is therefore a candidate **low-fidelity data source**, not current-truth supervision until transfer is demonstrated.

## VII. Synthetic data must earn transfer

Every synthetic-data use MUST retain a real-data-only control at matched real-label budget.

A synthetic method survives only if it demonstrably reduces the amount of real supervision needed to achieve the same out-of-synthetic performance, or improves a real-data frontier. Synthetic-only validation is insufficient.

Counterfactual/synthetic annotations must be treated as potentially biased. Prefer incorporating them into a direct/reward-model component while retaining real propensity-weighted correction when off-policy evaluation is used.

## VIII. Semantics may retrieve evidence, not invent truth

Semantic routing is not banned. The failed pattern is `semantic cluster -> fixed model choice`.

Permitted semantic uses include:

- retrieving measured historical outcomes from similar work;
- capability/task decomposition;
- support/OOD estimation;
- partial-pooling strata;
- diversity-aware acquisition;
- model-pool shortlisting.

Any semantic memory MUST report effective neighborhood support and uncertainty. Low-support queries must back off toward a global/task prior or conservative route rather than extrapolate confidently.

## IX. Decision objective must match the deployment decision

Prefer targets aligned to the actual decision:

- marginal quality gain of one action over another;
- cost-adjusted utility;
- pairwise/listwise model ranking;
- treatment effect/uplift;
- value of information for acquiring another sample/tool/model call;
- stage-level mission utility for agentic routing.

Absolute difficulty/correctness estimates are allowed only when a spec justifies why they are sufficient for the downstream decision.

## X. Uncertainty and risk are first-class outputs

Every learned score used to accept cheap work or suppress escalation MUST be evaluated for selective risk, calibration, task-family heterogeneity, and distribution shift.

Where conformal or other finite-sample guarantees are claimed, the exact assumptions (exchangeability, calibration population, target risk definition) MUST be written in the spec. Guarantees do not transfer automatically under drift.

## XI. Stack gains only after individual falsification

Each innovation spec MUST contain an independent Stage-0 or Stage-1 falsification test that can kill the idea cheaply before full implementation.

For stackable ideas:

- qualify each component independently;
- measure error overlap and marginal contribution;
- run leave-one-out or pairwise ablations where signals overlap;
- do not sum standalone percentage gains;
- prefer the simpler composition when results are statistically/economically indistinguishable.

A later layer that duplicates an earlier one should be deleted, not celebrated.

## XII. Cost is total cost

Report separately:

- router/representation compute;
- cheap-model calls;
- repeated samples;
- tool/verifier calls;
- mid-tier/frontier calls;
- telemetry/outcome collection cost;
- labeling/judge cost;
- training/refresh cost;
- p50/p95 latency and model-switch overhead;
- retries/no-progress loops for agentic work.

Current model IDs and prices MUST be refreshed at execution time. Historical GPT-4/Mistral prices and model availability are historical evidence only.

Default paid research spend is `$0`. Paid calls MUST fail closed behind an explicit operator gate and per-spec cap. Existing project-wide constraints remain in force unless the operator changes them.

## XIII. Security and adversarial cost robustness

A router can itself be attacked to force expensive routes. Any method exposed to user-controlled text MUST include at least a lightweight perturbation/adversarial-cost stress test before promotion.

Candidate systems should test:

- harmless suffix/prefix perturbations;
- paraphrases preserving task semantics;
- length/format manipulation;
- repeated instruction/meta-language;
- OOD prompts;
- attempts to force an expensive route without increasing real task difficulty.

The goal is not perfect adversarial robustness at research stage; it is to avoid promoting a trivially manipulable cost controller.

## XIV. Agentic routing is a separate estimand

Single-turn RouterBench quality/cost and multi-turn Hermes mission economics are different questions.

Agentic-stage routing MUST be evaluated on trajectory-level outcomes, total mission cost, retries, model switches, progress/failure state, and accepted mission success. Do not claim RouterBench APGR proves mission-level value or vice versa.

Stage routing may coexist with a per-turn/single-turn router, but its qualification is separate.

## XV. Every spec must be executable and killable

Each feature spec MUST state:

- problem and why it is materially new;
- user/operator scenarios;
- functional requirements;
- exact data dependencies and prohibited data;
- success criteria in measurable terms;
- earliest falsification test;
- keep/kill gate;
- adverse/failure cases;
- stackability/exclusivity;
- expected benefit if successful;
- cost/spend boundary;
- required artifacts/provenance.

Each plan MUST include constitution checks, data contracts, algorithm details, baselines, statistics, and rollback/stop logic. Each tasks file MUST be ordered so the cheapest falsification work comes before expensive implementation.

## XVI. Promotion requires convergence, not optimism

Use the Spec Kit lifecycle pragmatically:

`spec -> clarify if needed -> plan -> tasks -> implement -> analyze/converge`

For this research program, the canonical roadmap is `specs/router-innovation-2026-09-08/roadmap.md`.

A spec is `SURVIVED-RESEARCH` only because its mechanism survived desk/adversarial review. It is **not** a successful router component until its implementation gates pass.

The final project recommendation must distinguish:

- literature-supported hypothesis;
- project-specific evidence;
- retrospective replay evidence;
- shadow evidence;
- live randomized evidence;
- production/shadow candidate.

No category may be silently upgraded to another.
