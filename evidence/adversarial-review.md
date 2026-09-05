# Adversarial review v2: router retraining research

**Date:** 2026-09-05  
**Purpose:** attack the research recommendations before committing money, test-set access, or production authority.

## Review posture

This review assumes the memo is wrong until an option survives the strongest plausible objections. It distinguishes:

- **retired risk** — evidence or a $0 analysis materially resolves the concern;
- **bounded risk** — unresolved, but a preregistered cheap experiment can answer it;
- **fatal if true** — do not progress without resolving it.

The historical test split remains sealed throughout.

## Executive red-team result

The first-pass memo survives in its broad conclusion—**fix the supervision/economic loop before making the router bigger**—but two recommendations changed materially:

1. `predict weak correctness` is **too coarse as the final target** because it pays for strong even when strong would not improve the answer. It remains valuable as the first factor of a better target.
2. The existing judge labels are **far more asymmetric than aggregate 0.8382 agreement suggests**. Algebra from the reported rates implies judge `needs strong` precision ≈96%, while judge `weak sufficient` NPV ≈58.5%. The right use is one-sided/selective supervision, not ordinary hard labels.

A third conclusion strengthened: **semantic routing is viable as a signal/control layer but not as a direct replacement for trustworthy outcome supervision.**

The revised top design is **Factorized Escalation Value (FEV)** plus semantic support/OOD signals and sparse unbiased outcome sampling.

---

## Attack 1 — “Weak correctness is the wrong target”

### Challenge

A weak answer being wrong does not imply that paying for strong creates value. If both models fail, a weak-correctness router over-escalates. If weak succeeds while strong fails, a generic “difficulty” model can actively regress quality.

### Evidence

RouteLMT (2026) argues directly that the large model's **marginal gain over the small model** is the optimal signal for budgeted routing, and reports better quality-budget frontiers than absolute quality/difficulty baselines in machine translation.

Source: [Luo et al., 2026](https://arxiv.org/abs/2604.22520).

EquiRouter identifies a related objective-decision mismatch: scalar performance prediction can cause “routing collapse,” and learning model rankings reduces cost at GPT-4-level performance on RouterBench.

Source: [Lai & Ye, 2026](https://arxiv.org/abs/2602.03478).

### Verdict

**Attack succeeds. First-pass rank #1 must be refined.**

### Resolution

Run Experiment 000 to measure the weak/strong overlap matrix and rescue-rate heterogeneity. If weak failures are not almost always rescued by strong, use FEV:

`P(weak fails | x) × P(strong succeeds | weak fails, x)`

or the continuous expected score difference when available.

Risk state: **bounded by $0 audit**.

---

## Attack 2 — “Evaluator-first labels exploit RouterBench but will not generalize to Hermes”

### Challenge

RouterBench contains many objective benchmark tasks. Hermes agentic work includes coding, research, tool use, long-horizon workflows and subjective acceptance. An evaluator-first strategy could be benchmark overfitting disguised as a retraining architecture.

### Evidence

RouterBench's own paper reports exact-match scoring for MMLU, HellaSwag, GSM8K, ARC-Challenge and WinoGrande, with GPT-4 evaluation used for MBPP, MT-Bench and RAG. This does make objective weak grading unusually cheap in the present corpus, but it is not representative of all future Hermes outcomes.

Source: [RouterBench paper](https://openreview.net/pdf?id=IVXmV8Uxwh).

The parent Hermes program's actual optimization target is accepted mission quality and cost, including retries/latency/human intervention, not benchmark classifier accuracy.

### Verdict

**Attack partly succeeds.** Evaluator-first remains the cheapest immediate label source but cannot be the whole strategic design.

### Resolution

Treat deterministic evaluators as the **first tier of a general evidence hierarchy**, not the definition of success. The long-run flywheel must consume tool/test outcomes, user acceptance, retries, judge abstention and sparse audits. See [`../designs/router-learning-flywheel.md`](../designs/router-learning-flywheel.md).

Risk state: **bounded architecturally; requires later Hermes shadow evaluation**.

---

## Attack 3 — “Semantic routing already failed; why touch it again?”

### Challenge

The project already falsified cluster routing (`val 0.4155`) and a BERT-family classifier. Any semantic-routing proposal could be disguised repetition.

### Evidence against naive rerun

LLMRouterBench (Findings ACL 2026) finds embedding-backbone changes have limited impact and many routing methods are similar under unified evaluation. LatentGate (ACL Industry 2026) shows ordinary embedding routing can collapse semantically similar but functionally distinct intents.

Sources: [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/), [LatentGate](https://aclanthology.org/2026.acl-industry.153/).

### Evidence for a different semantic use

vLLM Semantic Router separates reusable signals, projections and decisions, including domain, complexity, embeddings, context and user feedback. ContextualRouter shows that **retrieving historical performance of nearby queries** can work with sparse history—even when simple kNN is used.

Sources: [vLLM Semantic Router](https://github.com/vllm-project/semantic-router/blob/main/website/docs/intro.md), [ContextualRouter](https://aclanthology.org/2026.eacl-srw.22/).

### Verdict

**Naive semantic model selection remains rejected. Auxiliary semantic routing survives.**

### Resolution

Semantic signals may be tested only for task conditioning, local outcome retrieval, OOD support and active-sampling coverage. Experiment 005 explicitly forbids KMeans fixed-route and BERT reruns.

Risk state: **bounded by $0 ablation**.

---

## Attack 4 — “The existing judge is unusable because v2 failed”

### Challenge

Systematic judge noise destroyed APGR, so further work on the same judge may be sunk-cost bias.

### New algebraic evidence

Using only the mission-reported prevalence and agreement numbers, the judge confusion matrix is approximately identified. It implies:

- precision of `judge needs strong` ≈ **96.0%**;
- NPV of `judge weak sufficient` ≈ **58.5%**.

See [`judge-noise-derived-analysis.md`](judge-noise-derived-analysis.md).

### Verdict

**Attack fails in its absolute form.** The judge is not a good symmetric labeler, but one polarity carries high-value signal.

### Resolution

Treat judge-positive examples as high-precision positives and judge-negative examples as unlabeled unless independently verified. Test PU/semi-supervised learning and task-conditioned posteriors. Do not pay for a broader judge ensemble until conditional error correlation is measured.

Risk state: **partially retired analytically; model utility bounded by Experiment 004**.

---

## Attack 5 — “PU learning assumptions do not hold”

### Challenge

Classic positive-unlabeled methods often rely on assumptions about how positives become labeled. The judge chooses positive examples based on instance difficulty/task, so its positive set is not random. It also has ~4% false-positive contamination.

### Verdict

**Attack succeeds against naive nnPU.**

### Resolution

PU is an option family, not a drop-in recipe. Compare:

- simple one-sided weighted supervision;
- nnPU;
- task/semantic propensity-adjusted variants;
- deterministic trusted negatives;
- hierarchical task shrinkage.

If the simplest one-sided method matches the complex methods, choose it.

Risk state: **bounded by Experiment 004**.

---

## Attack 6 — “Sparse strong labels may miss rare rescues”

### Challenge

The exact rows where strong uniquely succeeds could be rare and semantically atypical. Active selection based on the current model can create a self-confirming blind spot.

### Evidence

LLMRouterBench says much of the remaining gap to oracle is driven by **model-recall failures**—queries where only a small subset of models answer correctly and routers fail to recall them.

Source: [Li et al., 2026](https://aclanthology.org/2026.findings-acl.1881/).

### Verdict

**Serious risk.** This is one of the strongest objections to sparse labeling.

### Resolution

Every sparse-label experiment must reserve a random sentinel fraction. Proposed default for simulation: 80% targeted + 20% uniform random. Long-run deployment should preserve a tiny unbiased exploration/dual-evaluation stream. The exact fraction is learned offline, not asserted.

Risk state: **bounded by Experiments 003/006/011-style replay**.

---

## Attack 7 — “Task-stratified correction will overfit tiny strata”

### Challenge

The judge is known to fail on partial-credit families. Splitting by task can fix systematic bias, but estimating separate confusion matrices on small groups creates high variance and leakage-like tuning.

### Verdict

**Valid risk.**

### Resolution

Use coarse preregistered families and hierarchical shrinkage toward the global confusion matrix. No post-hoc creation of strata after observing validation APGR. Report effective sample size per stratum.

Risk state: **bounded by train-only calibration experiment**.

---

## Attack 8 — “A second judge just reproduces the same bias”

### Challenge

Judge ensembles help only if errors are not strongly correlated. Two frontier models trained on similar data and prompted identically may agree confidently on the same wrong partial-credit cases.

### Evidence

Jury-on-Demand and CaMVo support adaptive per-item judge choice, while SCOPE supports abstention under calibrated risk. None implies that majority vote automatically fixes correlated bias.

Sources: [SCOPE](https://arxiv.org/abs/2602.13110), [CaMVo, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/054e9f9a286671ababa3213d6e59c1c2-Abstract-Conference.html), [Jury-on-Demand](https://arxiv.org/abs/2512.01786).

### Verdict

**Attack succeeds against static ensemble-by-default.**

### Resolution

Before spending, label only a small clean calibration sample with a genuinely different judge family and compute **conditional error correlation on primary-judge mistakes**. A second judge advances only if it corrects enough primary errors per dollar.

Risk state: **bounded by <$0.50 calibration**.

---

## Attack 9 — “Conformal judge guarantees do not transfer here”

### Challenge

SCOPE provides finite-sample selective guarantees for pairwise judging under exchangeability and a particular bidirectional uncertainty signal. Our judge emits binary weak correctness + self-reported confidence, not pairwise preference probabilities.

### Verdict

**Attack succeeds against copying SCOPE's guarantee.**

### Resolution

Use SCOPE as design precedent for **selective abstention**, not as a borrowed guarantee. Any project-specific risk bound requires its own exchangeability assumptions and calibration score. With only 90 calibration rows, strong guarantees may have poor coverage; report that honestly.

Risk state: **unresolved until larger clean calibration evidence exists**.

---

## Attack 10 — “Public routing datasets solve the problem already”

### Challenge

RouteLLM, EmbedLLM, LLMRouterBench and synthetic routing datasets are large. Why not train on them and skip exact-pair labels?

### Verdict

**Rejected as direct replacement.** Their model pools, task mixes and scoring do not provide exact counterfactual truth for the historical `mistral-7b-chat` / `gpt-4-1106-preview` pair.

### Resolution

Use public data only for representation priors, retrieval priors, model-agnostic techniques, and sanity checks. Exact-pair decision calibration still needs local outcome evidence.

Risk state: **retired conceptually**.

---

## Attack 11 — “Bandit learning sacrifices safety while exploring”

### Challenge

Online partial-feedback routing is strategically attractive, but exploration can deliberately send hard queries to weak models or waste strong calls. In an agentic harness, unsafe exploration is unacceptable.

### Evidence

PILOT and BaRP show routing can learn from bandit feedback rather than exhaustive full-information labels.

Sources: [PILOT, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.1301/), [BaRP, 2025](https://arxiv.org/abs/2510.07429).

### Verdict

**Valid operational risk, not a reason to dismiss bandits.**

### Resolution

Exploration sits *after* deterministic privacy/capability gates and is allowed only on policy-eligible, low-consequence traffic. Offline replay must quantify the exploration rate first. For high-risk traffic, use shadow dual-evaluation rather than action exploration.

Risk state: **bounded by Experiment 006; production approval remains separate**.

---

## Attack 12 — “APGR can reward ranking changes that do not matter at the deployed threshold”

### Challenge

A method can improve the area under the quality-vs-PGR curve while being worse near the actual operating point. Conversely, an intercept/prior correction changes a fixed decision threshold but cannot improve rank-based APGR if score order is unchanged.

### Verdict

**Valid metric risk.**

### Resolution

Every experiment reports:

- APGR as primary preregistered metric for comparability;
- quality/PGR near the deployed operating region;
- rescue recall at economically relevant strong-call budgets;
- cost at current prices.

Do not claim an APGR rescue from pure post-hoc intercept/class-prior correction unless it changes ranking; threshold calibration is a separate operating-point optimization.

Risk state: **retired procedurally**.

---

## Attack 13 — “One-shot outcomes may be statistically unlearnable”

### Challenge

If model correctness varies materially across stochastic draws, a single RouterBench outcome can label identical latent difficulty differently. Training harder on those labels may chase noise.

### Verdict

**Valid and strategically important.**

### Resolution

Prefer expected reliability/marginal-gain targets; if future labels are regenerated, use deterministic decoding where appropriate or repeated weak sampling only in a tiny audit to estimate outcome variance. Training-free CARGO is relevant because it explicitly uses weak-model response agreement as a reliability signal.

Source: [CARGO, 2026](https://arxiv.org/abs/2607.20481).

Risk state: **partially bounded; requires future variance audit**.

---

## Attack 14 — “A fancy value model can collapse like other routers”

### Challenge

Factorizing the target does not guarantee ranking quality. Multiplying two miscalibrated probabilities can amplify errors, especially in rare rescue regions.

### Verdict

**Valid modeling risk.**

### Resolution

FEV must beat two simple baselines:

1. weak-failure probability alone;
2. direct rescue classifier using the same sparse strong labels.

If direct rescue ranking is better, use it. Factorization is an economic/data decomposition, not dogma.

Risk state: **bounded by Experiment 003**.

---

## Attack 15 — “The research is optimizing an obsolete model pair”

### Challenge

`gpt-4-1106-preview` and Mistral-7B are historical. A solution overfit to their peculiarities has little strategic value.

### Verdict

**Correct strategically.**

### Resolution

Judge each design by **refresh locality**:

- weak changes → can we refresh weak-success cheaply without relabeling strong everywhere?
- strong changes → can we refresh only sparse rescue evidence?
- prices change → can thresholds/cost multiplier change without retraining?
- task mix changes → can OOD/performance-memory identify unsupported regions?

FEV + semantic signals + bandit/sentinel outcomes scores best on this criterion.

Risk state: **incorporated into ranking**.

---

# Innovations that survived the red team

## 1. Factorized Escalation Value (new rank #1)

Learn weak-failure broadly and strong-rescue sparsely. Make the final decision on expected incremental quality per incremental dollar, not generic difficulty.

## 2. One-sided judge supervision

Use the judge where its observed polarity is strong: high-precision escalation positives. Treat its weak predictions as unknown unless corroborated.

## 3. Semantic performance memory + OOD guard

Use semantic geometry to retrieve measured outcomes and quantify support, not to assign fixed routes by cluster.

## 4. Unbiased sentinel labeling

Reserve a small random share of any active-label budget. This is insurance against the router's own blind spots and makes future drift estimates credible.

## 5. Bandit-feedback end state

Move from periodic “fully labeled retrain datasets” toward a router that learns from chosen-arm operational outcomes, with policy-gated exploration and tiny counterfactual sentinel samples.

## 6. Three-state supervision

`ESCALATE_CONFIRMED / WEAK_CONFIRMED / UNKNOWN` is a more faithful representation of evidence quality than forcing every cheap label into a binary target.

---

# Recommended execution order after adversarial review

1. **Experiment 000:** audit weak/strong rescue structure. $0, no model training.
2. **Experiment 003:** FEV sparse-strong simulation if Experiment 000 shows meaningful non-rescuable weak failures or heterogeneous rescue.
3. **Experiment 004:** exploit one-sided judge positives via PU/semi-supervised training. $0.
4. **Experiment 005:** semantic performance-memory/OOD ablation on the best target. $0.
5. **Experiment 006:** bandit replay simulation as the strategic continual-learning test. $0.
6. Only then authorize any <$0.50 second-judge calibration, if evidence says the residual open-ended region needs it.

This sequence deliberately spends **zero dollars** until the biggest modeling risks have been retired retrospectively.
