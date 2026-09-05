# Ranked options memo: cheap, repeatable router retraining — adversarially reviewed v2

**Date:** 2026-09-05  
**Parent program:** [thepragmatik/hermes-pi-agentic-stack](https://github.com/thepragmatik/hermes-pi-agentic-stack)  
**Decision:** how to preserve or exceed deployed router-v1 quality while making future retraining cheap enough to repeat whenever models, prices or tasks change.

## Direct executive answer

The research now supports a stronger conclusion than the first pass:

> **Do not make “which model won this historical row?” the long-term training target. Build a value router that estimates the marginal benefit of escalation, learns weak-model failure cheaply, learns strong-model rescue sparsely, and uses semantic routing as a conditioning/risk layer rather than the final oracle.**

The revised top option is **Factorized Escalation Value (FEV)**:

`expected escalation value ≈ P(weak fails | x) × E[strong rescue | weak fails, x] − incremental_cost × λ`.

Why it matters economically:

- weak-model correctness can often be regenerated with **weak-only inference + local/task-native evaluation**;
- strong-model evidence is needed only to learn **where strong actually rescues weak**, and can be sampled sparsely;
- when the weak model changes, refresh the first factor broadly and the second factor only on a small sample;
- when the strong model changes, weak labels remain useful and only rescue evidence needs refreshing;
- when prices change, the quality model can remain fixed while the decision cost multiplier changes.

This formulation is also better aligned with 2026 routing literature. RouteLMT explicitly identifies the large model's **marginal gain** over the small model as the correct signal for budgeted hybrid routing, while EquiRouter warns that objective/decision mismatch can cause routing collapse. ([RouteLMT](https://arxiv.org/abs/2604.22520), [EquiRouter](https://arxiv.org/abs/2602.03478))

A second major finding comes from the project's own failed judge experiment. The published aggregate rates algebraically imply that the evidence-mode judge's `needs strong` labels are approximately **96.0% precise**, while its `weak sufficient` labels have only about **58.5% negative predictive value**. This means the judge is not “83.82% noisy” in a symmetric sense: it is a potentially valuable **one-sided positive labeler**. Treating judge-weak rows as clean negatives was structurally harmful; a positive-unlabeled or three-state supervision scheme deserves a $0 test.

A third conclusion answers the semantic-routing question directly: **semantic routing is viable, but not as a naive prompt-similarity weak-vs-strong classifier.** Current vLLM Semantic Router work strongly supports multi-signal control planes (domain, complexity, embedding, context, feedback, OOD-style support), while its learned model-selection pipeline still requires measured historical model outcomes. The right role for semantics here is task conditioning, performance-memory retrieval, OOD guarding, judge calibration and label-budget allocation. The project's already-falsified KMeans/cluster route should not be repeated.

The immediate research program should therefore spend **$0 first**:

1. audit whether weak failures are actually rescued by strong (Experiment 000);
2. simulate FEV with only 0.5–5% strong labels (Experiment 003);
3. exploit one-sided judge positives (Experiment 004);
4. test semantic performance memory/OOD features without cluster routing (Experiment 005);
5. replay an online bandit learner that sees only the chosen model's outcome (Experiment 006).

Only after these should any paid judge call be authorized.

---

## Baseline and hard constraints

- Router v1: bge-small-en-v1.5 384-d embeddings feeding a ~49.5K-parameter matrix-factorization head.
- Training set: 29,193 RouterBench-0shot train rows under the fixed SHA256 split.
- Historical one-time **test APGR 0.6528**. Test is sealed and is not used again in this research.
- Same weights later measured **validation APGR 0.6459**; this is the v1 comparison baseline.
- Failed v2 trained on judge labels: agreement 0.8382, **val APGR 0.5304**, auto-reverted.
- Historical viability gate: **val APGR >=0.55**.
- A credible v1 replacement must reach **val APGR >=0.6459** under preregistered validation-only evaluation.
- Default spend $0; any paid call requires fail-closed `SPEND_GO=1`-style gating, ZDR, and total mission spend <$5.
- Falsified cluster router and BERT-family classifier are not to be rerun without a materially different hypothesis.

### Project metric definitions

**PGR:** fraction of prompts routed to weak, i.e. strong-model calls avoided.  
**APGR:** normalized area under the project routing-quality-vs-PGR curve as the routing threshold is swept. Random is ~0.50 in the project evaluator.

> External RouteLLM papers use “PGR” to mean performance gap recovered. This memo uses the project definition above.

---

# Ranked options after adversarial review

| Rank | Option | Why it ranks here | Expected future label cost | Expected lift / value | Biggest risk | <$0.50 falsification |
|---:|---|---|---:|---|---|---|
| **1** | **Factorized Escalation Value (FEV): weak failure + sparse strong rescue** | Optimizes the economic decision directly and localizes expensive labels to the strong-rescue factor | $0 retrospective; future strong labels potentially **0.5–5%** of corpus plus cheap weak-only grading | Highest probability of v1 parity at materially lower refresh cost; exact APGR unmeasured | Rescue events may be too idiosyncratic to forecast sparsely | Experiment 000 overlap audit, then mask all but 0.5/1/2/5% strong train labels and evaluate val APGR |
| **2** | **Evaluator-first weak correctness / reliability** | Cheapest broad supervision and reusable first factor of FEV; RouterBench has objective families with task-native scoring | $0 retrospective; future weak-only inference + local grading | Strong chance to recover much of v1; can equal v1 only if weak failure closely tracks strong rescue | Over-escalates both-wrong rows and ignores negative escalation | Experiment 000; if rescue conditional is nearly constant/high, run existing Experiment 001 |
| **3** | **One-sided judge supervision: high-precision strong positives + unlabeled weak predictions** | Converts the failed judge into a useful asymmetric label source instead of throwing it away | $0 from stored labels | Potentially large recovery vs v2 because it stops encoding judge false negatives as truth | PU selection assumptions fail; positives are instance-dependent and ~4% contaminated | Experiment 004: simple one-sided, nnPU, task-conditioned and verifier-negative variants |
| **4** | **Semantic performance memory + OOD/risk guard** | Uses semantics where evidence is strongest: locate comparable historical outcomes, estimate support, stratify tasks and detect drift | $0 using existing embeddings/outcomes | Could improve sparse-label efficiency and rescue recall; ContextualRouter reports strong results with 1% history | Semantic neighborhoods may not align with model complementarity; raw embeddings can collapse | Experiment 005: task, kNN outcome memory, OOD distance ablation; no clusters |
| **5** | **Selective hybrid label factory: verifier → one-sided judge → adaptive jury → sparse exact truth** | General solution for open-ended/agentic traffic; spends exact truth only where cheaper evidence abstains | $0 simulation; paid residual should remain well under $5 | Best label-engineering fallback if #1–#4 fall short | Selection bias and correlated judge error | Retrospective oracle-budget simulation + 20% random sentinel; no API calls first |
| **6** | **Bandit-feedback continual router + tiny unbiased sentinel stream** | Strategically removes the assumption that every training query needs outcomes for every model; learns under deployment-like partial feedback | $0 replay; future feedback comes from chosen arm, plus tiny audit/exploration budget | Highest long-run leverage for Hermes if offline replay holds up | Exploration/counterfactual blindness; operational safety | Experiment 006 replay on train, revealing only chosen-arm outcomes; evaluate frozen policy on val |
| **7** | **Conformal/selective judge abstention + adaptive jury** | Literature supports risk-controlled abstention and per-item judge selection rather than static majority vote | $0 calibration first; <$0.50 second-judge pilot | Useful in the residual open-ended band, not a universal labeler | Guarantees may not transfer; second judges may share bias | Measure conditional error correlation only on primary-judge risk set before scaling |
| **8** | **Task-conditioned soft noise correction / clean-set reweighting** | $0 rescue of current labels; can model known partial-credit bias | $0 CPU | Likely modest alone, but useful component | Tiny strata, post-hoc overfitting, cannot recover missing signal | Frozen coarse task strata + hierarchical shrinkage, then val APGR |
| **9** | **Training-free reliability/cascade signals (CARGO/C3PO)** | Potential escape hatch from supervised retraining; uses weak answer behavior/unlabeled outputs | Label cost ≈ $0; runtime cost/latency from extra weak samples | Could outperform supervised routers in some task families | Multiple samples may erase savings/latency advantage; not available from single stored response | Tiny <$0.50 repeated-weak sample or stored multi-response subset; test failure-ranking signal |
| **10** | **Public/synthetic router priors (RouteLLM, EmbedLLM, LLMRouterBench, CASCAL/RGD)** | Strong technique priors and free augmentation, but no exact historical pair truth | $0 downloads/training | Useful regularizer/pretraining; low confidence as standalone replacement | Model-pair/task mismatch | Fixed external prior or checkpoint score added without tuning; val APGR once |
| **11** | **Bigger/fancier router architecture / raw semantic classifier** | Lowest EV until target/labels improve; unified 2026 work says embeddings/architectures often matter less than outcome recall | $0–$5 compute | Low expected incremental lift | Learns the wrong target more efficiently; repeats falsified family | **Do not run now** |

---

# 1. Factorized Escalation Value (FEV) — recommended primary research path

## What it is

Estimate the **incremental value** of strong rather than generic prompt difficulty or absolute weak quality.

For continuous mission quality:

`EV(x) = E[Q_strong - Q_weak | x] - λ (C_strong - C_weak)`.

For the current binary-correctness setting, a useful factorization is:

`P(rescue | x) = P(weak fails | x) × P(strong succeeds | weak fails, x)`.

The decision threshold becomes cost-aware and can move as prices/preferences change.

## Prior art

RouteLMT (ACL Industry-era 2026 work on hybrid machine translation) argues that **marginal gain** is the optimal routing signal for budgeted decisions and that absolute quality/difficulty is inferior in its setting. [Paper](https://arxiv.org/abs/2604.22520).

EquiRouter identifies objective-decision mismatch as a cause of routing collapse and learns model rankings instead of relying only on scalar quality estimates; it reports ~17% cost reduction at GPT-4-level performance on RouterBench relative to its strongest prior router. [Paper](https://arxiv.org/abs/2602.03478).

## Why it may solve retraining economics

The expensive part is not learning `P(weak fails)`: for many objective tasks that can be regenerated from weak inference and local grading. The expensive counterfactual is whether strong would have rescued the weak failure. FEV isolates that signal so it can be acquired sparsely.

## Expected cost

- retrospective simulation: **$0**;
- future: weak-only generation broadly + strong evaluation on a small selected subset;
- Experiment 003 tests 0.5%, 1%, 2%, 5% strong-label budgets before any new spend.

## Expected lift

Highest expected value among new options because it corrects target misspecification **and** reduces label cost. No numeric APGR claim is made before the retrospective simulation.

## Biggest risk

Strong rescue might be prompt-idiosyncratic and sparse, so a model trained on 1–2% labels may miss exactly the rare examples that matter.

## Cheap first test

Run [Experiment 000](../experiments/000-target-audit-prereg.md). If rescue probability varies meaningfully, run [Experiment 003](../experiments/003-factorized-escalation-value-prereg.md).

---

# 2. Evaluator-first weak correctness / expected reliability

## What it is

Predict `P(weak correct | prompt)` using weak-answer labels produced by deterministic/task-native evaluators wherever possible.

RouterBench reports exact-match evaluation for MMLU, HellaSwag, GSM8K, ARC-Challenge and WinoGrande, while MBPP, MT-Bench and RAG use GPT-4-based evaluation in its published setup. [RouterBench](https://openreview.net/pdf?id=IVXmV8Uxwh).

The pinned local 0-shot corpus must be inventoried before claiming exact task coverage; published dataset mix is a prior, not a substitute for the local audit.

## Prior art

Routing methods that predict per-model correctness or capability support this decomposition conceptually. More importantly, FEV shows weak correctness is a useful **factor** even when it is not the final decision target.

## Expected cost

$0 on stored responses. Future cost is weak-model inference plus local scoring for objective tasks.

## Expected lift

Potentially large relative to failed v2 because labels are not judge-generated. V1 parity is plausible only if strong usually rescues weak failures or rescue variation is learnable by a small additional factor.

## Biggest risk

Both-wrong rows and negative escalation make weak failure an economically wrong proxy.

## Cheap first test

Experiment 000; proceed to Experiment 001 only if its frozen sufficiency condition is met.

---

# 3. One-sided judge supervision / PU-style learning

## What it is

Use the existing judge's reliable polarity without forcing its unreliable polarity into the training target.

From the mission's own aggregate numbers:

- truth strong-needed prevalence = 78.3%;
- judge strong-needed prevalence = 67.5%;
- agreement = 83.82%.

These identify an approximate confusion matrix with:

- `judge says strong` precision ≈ **96.0%**;
- `judge says weak` NPV ≈ **58.5%**.

Full derivation: [`../evidence/judge-noise-derived-analysis.md`](../evidence/judge-noise-derived-analysis.md).

## Design

Adopt three evidence states:

```text
ESCALATE_CONFIRMED  high-precision judge positive or exact rescue evidence
WEAK_CONFIRMED      deterministic weak-correctness evidence
UNKNOWN             judge weak / disagreement / unsupported region
```

Train with one-sided/semi-supervised or positive-unlabeled objectives rather than hard binary labels.

## Prior art

Non-negative PU learning allows classification from positive and unlabeled examples while reducing overfitting of unbiased PU risk estimators. [Kiryo et al., NeurIPS 2017](https://papers.nips.cc/paper/2017/hash/7cce53cf90577442771720a370c3c723-Abstract.html).

## Expected cost

$0 using stored judge labels and embeddings.

## Expected lift

Medium-to-high upside versus v2 because the method directly removes its dominant false-negative mechanism. No v1-parity claim until validation.

## Biggest risk

The judge-positive set is not selected at random; standard PU assumptions are violated and positives have ~4% contamination.

## Cheap first test

[Experiment 004](../experiments/004-one-sided-pu-prereg.md) compares simple one-sided supervision, nnPU, task-conditioned variants and deterministic weak negatives.

---

# 4. Semantic performance memory + OOD/risk guard

## What it is

Use semantic routing to **locate comparable evidence**, not to claim that semantic similarity itself determines weak/strong choice.

Potential features:

- task/domain;
- complexity and prompt structure;
- nearest-neighbor weak success rate;
- nearest-neighbor strong rescue rate;
- distance/density/support of historical clean labels;
- semantic/task-specific judge error rate.

## Prior art

### vLLM Semantic Router

Current vLLM Semantic Router implements a multi-signal control plane: signals such as domain, complexity, embeddings, context, structure, preference and user feedback are coordinated through projections and decisions. This architecture is valuable for Hermes because it separates readable policy/signal extraction from model-selection algorithms. [Introduction](https://github.com/vllm-project/semantic-router/blob/main/website/docs/intro.md).

But its learned KNN/KMeans/SVM/MLP model selectors require historical measured query/model outcomes; the training pipeline benchmarks candidate models on each query and explicitly does not manufacture trustworthy labels from model names. [Training README](https://github.com/vllm-project/semantic-router/blob/main/src/training/model_selection/ml_model_selection/README.md).

### ContextualRouter

ContextualRouter (EACL 2026) retrieves similar historical queries and estimates model performance; simple kNN averaging performs comparably or better than more complex variants in several settings and remains robust with as little as 1% historical data. [Paper](https://aclanthology.org/2026.eacl-srw.22/).

### Cautions

LLMRouterBench finds embedding backbone has limited impact and many methods converge to similar performance. [Paper](https://aclanthology.org/2026.findings-acl.1881/).

LatentGate shows vanilla embedding-based agent routers can collapse semantically similar but functionally different intents due to anisotropy; it improves them with SLM hidden-state probing and whitening. [Paper](https://aclanthology.org/2026.acl-industry.153/).

## Why it is not a rerun of the falsified cluster router

Failed approach: `prompt -> cluster -> fixed route`.

Proposed approach: `prompt -> nearby clean outcomes / support estimate -> value model + risk guard`.

The semantic representation does not create the label; measured outcomes do.

## Expected cost

$0 using existing embeddings/outcomes.

## Expected lift

Moderate as an auxiliary signal and potentially high for sparse-label efficiency; low confidence as a standalone route.

## Biggest risk

Semantic neighborhoods may be smooth in topic but not in model complementarity.

## Cheap first test

[Experiment 005](../experiments/005-semantic-signal-ablation-prereg.md). KMeans and BERT reruns are explicitly prohibited.

---

# 5. Selective hybrid label factory

## What it is

Apply label sources in descending order of trust/cost:

1. deterministic task/mission verifier;
2. weak-answer correctness where objectively gradeable;
3. high-precision one-sided judge evidence;
4. learned risk/abstention gate;
5. diverse second judge only when conditional error evidence justifies it;
6. exact counterfactual strong evaluation for the remaining high-value unknowns;
7. random sentinel truth to detect blind spots.

## Prior art

RouteLLM demonstrated that adding judge-augmented data can dramatically change router quality and that relatively small in-domain gold can matter. [RouteLLM](https://arxiv.org/abs/2406.18665).

SCOPE (2026) demonstrates the value of **selective abstention** for LLM judging with finite-sample risk control in its pairwise setting. It should inspire the design, but its guarantee does not transfer automatically to this binary evidence-mode judge. [SCOPE](https://arxiv.org/abs/2602.13110).

CaMVo (NeurIPS 2025) and Jury-on-Demand support per-instance annotator selection instead of static full juries. [CaMVo](https://proceedings.neurips.cc/paper_files/paper/2025/hash/054e9f9a286671ababa3213d6e59c1c2-Abstract-Conference.html), [Jury-on-Demand](https://arxiv.org/abs/2512.01786).

## Expected cost

$0 retrospective simulation; paid residual depends on how much remains after deterministic and one-sided evidence.

## Expected lift

High fallback potential because it directly attacks systematic error rather than averaging labels.

## Biggest risk

Active selection hides the router's blind spots; judge errors are correlated.

## Cheap first test

Simulate sparse exact labels from existing train ground truth with **80% targeted + 20% random sentinel** and compare to uniform sampling.

---

# 6. Bandit-feedback continual routing

## What it is

Train from the feedback available in real deployment: only the chosen model's outcome, plus a small exploration/sentinel stream.

This attacks the deepest economic mismatch in supervised routing: full-information training assumes every candidate model is evaluated for every query, while production observes only the selected arm.

## Prior art

PILOT (Findings EMNLP 2025) formulates LLM routing as a contextual bandit, refining query/model affinity from online bandit feedback and handling user budgets. [Paper](https://aclanthology.org/2025.findings-emnlp.1301/).

BaRP (2025 preprint) similarly trains under partial feedback and allows operators to vary the performance/cost preference at inference without retraining; it reports gains over offline routers in its experiments including RouterBench. [Paper](https://arxiv.org/abs/2510.07429).

## Expected cost

$0 retrospective replay. In production, normal chosen-arm outcomes provide feedback; sparse counterfactual audits remain necessary.

## Expected lift

Strategically very high if it reaches v1-adjacent validation quality, because it may remove periodic full-label retrains entirely.

## Biggest risk

Counterfactual blindness and unsafe exploration.

## Cheap first test

[Experiment 006](../experiments/006-bandit-replay-prereg.md), with policy gates and random sentinel exploration simulated offline.

---

# 7. Selective judge abstention + adaptive jury

## What it is

Predict whether the cheap judge is safe to trust; abstain otherwise. If a second judge is needed, select it per row instead of always querying a static ensemble.

## Prior art

- [SCOPE, 2026](https://arxiv.org/abs/2602.13110): selective conformal pairwise judging with target risk and abstention.
- [CaMVo, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/054e9f9a286671ababa3213d6e59c1c2-Abstract-Conference.html): context-aware subset selection of LLM annotators.
- [Jury-on-Demand, 2025](https://arxiv.org/abs/2512.01786): dynamic judge selection using per-item reliability prediction.

## Expected cost

$0 to build/train risk selectors from existing evidence. A second-judge calibration can remain <$0.50 if tightly scoped.

## Expected lift

Useful in the open-ended residual band; unlikely to beat deterministic labels where deterministic evaluation exists.

## Biggest risk

Confidence/error predictors fail under task shift; judges share correlated blind spots.

## Cheap first test

Measure error *conditional on primary-judge mistakes* for a disjoint-family second judge before any ensemble scaling.

---

# 8. Task-conditioned noise correction / clean-set reweighting

## What it is

Estimate coarse task-dependent error rates and train with soft posteriors or instance weights instead of hard judge labels.

This is especially relevant because the failed v2 diagnosis localized error in partial-credit families such as HellaSwag, grade-school math and professional law.

## Expected cost

$0 CPU.

## Expected lift

Likely modest alone; useful as a component of #3/#5.

## Biggest risk

Overfitting tiny strata and using validation to invent categories.

## Cheap first test

Freeze coarse task families using train metadata, estimate confusion with hierarchical shrinkage, train the same MF head and compare val APGR once.

---

# 9. Training-free / self-supervised reliability signals

## What it is

Avoid conventional router labels by using answer-time weak-model behavior or unlabeled model outputs.

CARGO uses agreement among weak-model responses with Bayesian early stopping and reports that it can outperform supervised routers in some reasoning/QA settings. [CARGO](https://arxiv.org/abs/2607.20481).

C3PO builds cascades from unlabeled model outputs and uses conformal prediction for cost control. [C3PO](https://arxiv.org/abs/2511.07396).

## Expected cost

No label acquisition, but potentially multiple weak calls at inference.

## Expected lift

Unknown on this exact pair. Best treated as a strategic fallback or auxiliary reliability signal.

## Biggest risk

Runtime token/latency overhead may exceed the savings created by avoiding strong calls.

## Cheap first test

Use any already-stored multiple weak responses; if none exist, a tiny <$0.50 sample under a spend gate can test whether weak-answer agreement ranks failures.

---

# 10. Public / synthetic routing priors

RouteLLM, EmbedLLM, LLMRouterBench and newer generated-data methods are valuable technique priors but do not provide exact counterfactual labels for this historical pair.

LLMRouterBench is especially valuable as an adversarial reality check: over 400K instances, 21 datasets and 33 models, it finds many leading routers similar, embedding choice limited in impact, and a persistent oracle gap driven by model recall. [Paper](https://aclanthology.org/2026.findings-acl.1881/).

Use public data for representation priors, architecture sanity checks, retrieval priors and augmentation—not as a claim that local pairwise truth has been replaced.

---

# 11. Bigger router architecture — defer

The project already falsified a BERT-family classifier and cluster routing. The 2026 evidence makes architecture-chasing even less attractive before supervision is repaired.

Do not spend GPU credits on a larger tower until a better target/label source lets the existing MF head approach or beat v1.

---

# Direct answers to the original mission questions

## 1. Confidence-weighted training

**Raw judge confidence weighting is not the best test.** The failed labels are label-asymmetric and task-dependent. Use confidence only as one risk/selection feature. More promising is one-sided supervision plus task-conditioned calibration.

## 2. Judge ensembles / disagreement filtering

**Yes, but static majority voting is not recommended.** First measure conditional error independence. Use a second judge only on primary-risk rows. Prefer abstention and selective jury designs.

## 3. Public judge-augmented datasets

Useful for priors and technique transfer, **not exact-pair replacement labels**. Exact local calibration still matters.

## 4. Hybrid labels

**Yes.** After adversarial review, hybrid evidence remains the robust operational answer, but it should be structured around *value of information* and include a random sentinel stream.

## 5. Alternative targets

The hierarchy is now:

1. **expected marginal value of escalation** — preferred final target;
2. weak correctness/reliability — cheapest broad factor/proxy;
3. direct cost prediction — insufficient alone because price does not tell whether escalation improves quality.

## 6. 2025–2026 innovations that materially change the plan

1. **RouteLMT:** marginal gain is the right routing signal for a budgeted weak/strong system.
2. **EquiRouter:** objective-decision mismatch can cause routing collapse; ranking/decision-aware training matters.
3. **ContextualRouter:** sparse performance retrieval can remain strong with ~1% historical data.
4. **PILOT/BaRP:** train from bandit feedback instead of exhaustive per-model labels.
5. **vLLM Semantic Router:** semantic routing is becoming a multi-signal control plane, not merely nearest-intent matching.
6. **LLMRouterBench:** model recall/training signal matters more than many architectural differences; embedding swaps have limited effect.
7. **LatentGate:** raw embedding geometry can collapse; semantic features need calibration/whitening/learned use when used as classifiers.
8. **SCOPE/CaMVo/Jury-on-Demand:** abstain and select judges dynamically rather than trusting raw self-confidence or always using a jury.
9. **CARGO/C3PO:** label-free or training-free cascade signals are plausible strategic fallbacks.

---

# Recommended experiment sequence

## Experiment 000 — target sufficiency / rescue audit

**Run first. $0.**

Compute the train-only 2×2 weak/strong correctness overlap and task-level strong-rescue rates. This determines whether weak correctness is sufficient or FEV is mandatory.

Preregistration: [`../experiments/000-target-audit-prereg.md`](../experiments/000-target-audit-prereg.md).

## Experiment 003 — FEV sparse strong-label simulation

**Run if Experiment 000 shows heterogeneous/non-universal strong rescue. $0.**

Mask strong outcomes except 0.5%, 1%, 2%, 5% train budgets; compare uniform vs targeted+random-sentinel acquisition; train weak failure + rescue/value models and score untouched validation.

Preregistration: [`../experiments/003-factorized-escalation-value-prereg.md`](../experiments/003-factorized-escalation-value-prereg.md).

## Experiment 004 — one-sided judge / PU

**$0.** Turn the current judge's high-precision strong labels into positives and stop treating judge-weak rows as clean negatives.

Preregistration: [`../experiments/004-one-sided-pu-prereg.md`](../experiments/004-one-sided-pu-prereg.md).

## Experiment 005 — semantic signal ablation

**$0.** Add task/domain, historical-performance kNN and OOD support to the strongest target. Do not rerun cluster routing.

Preregistration: [`../experiments/005-semantic-signal-ablation-prereg.md`](../experiments/005-semantic-signal-ablation-prereg.md).

## Experiment 006 — bandit replay

**$0.** Simulate a router that observes only the chosen model's outcome and a tiny exploration stream.

Preregistration: [`../experiments/006-bandit-replay-prereg.md`](../experiments/006-bandit-replay-prereg.md).

### Gates shared by model experiments

- viability: val APGR >= **0.55**;
- meaningful rescue: >= **0.60**;
- replacement: >= **0.6459**;
- test stays sealed;
- all hyperparameters/acquisition rules frozen before validation;
- report quality/PGR near deployed operating region in addition to APGR.

---

# Strategic design for Hermes

The strategic target is a **self-renewing economic control plane**, not a static classifier.

```text
mission/request
    ↓
deterministic privacy/capability policy
    ↓
semantic coordinate system
(task · domain · complexity · support · OOD)
    ↓
expected escalation value
    ↓
risk / abstention guard
    ↓
weak ───────────── or ───────────── strong
    ↓                                  ↓
verifier / acceptance / retry / operational outcome
    └─────────────────┬────────────────┘
                      ↓
       performance memory + bandit feedback
          + tiny unbiased sentinel truth
```

This architecture has four crucial second-order properties:

1. **model-refresh locality:** changing one model need not invalidate every historical label;
2. **price independence:** cost trade-offs can move without relearning quality from scratch;
3. **drift visibility:** semantic support/OOD and sentinel evidence show where the router no longer knows;
4. **counterfactual discipline:** a small unbiased sample prevents self-confirming routing policies.

Detailed design: [`../designs/router-learning-flywheel.md`](../designs/router-learning-flywheel.md).

---

# What the adversarial review changed

The review did not merely validate the first memo. It changed it:

- **demoted weak correctness from final target to broad cheap factor**;
- **promoted FEV / marginal gain to rank #1**;
- **rescued the failed judge as a one-sided labeler** based on derived confusion structure;
- **reframed semantic routing** as performance-memory/OOD/task conditioning rather than direct cluster routing;
- **promoted bandit feedback** as the long-term mechanism that aligns training with deployment;
- added **random sentinel truth** as a mandatory defense against active-label and online-learning blind spots;
- explicitly separated RouterBench qualification from eventual Hermes accepted-mission quality.

This is a stronger, more innovative and more falsifiable plan than the first-pass recommendation.

---

# Evidence map

- semantic routing review: [`../evidence/semantic-routing-review.md`](../evidence/semantic-routing-review.md)
- derived judge-noise analysis: [`../evidence/judge-noise-derived-analysis.md`](../evidence/judge-noise-derived-analysis.md)
- adversarial review: [`../evidence/adversarial-review.md`](../evidence/adversarial-review.md)
- source ledger: [`../evidence/source-ledger.md`](../evidence/source-ledger.md)
- evidence gaps: [`../evidence/gap-matrix.md`](../evidence/gap-matrix.md)
