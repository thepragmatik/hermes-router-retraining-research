# Semantic routing: viability review for Hermes router retraining

**Date:** 2026-09-05  
**Question:** Is “semantic routing” a viable replacement or complement for the current weak-vs-strong router?

## Verdict

**Yes as a signal/control layer; no as a direct drop-in solution to the label-economics problem.**

The important distinction is between:

1. **semantic intent/domain routing** — infer what kind of request this is, then apply a policy; and
2. **semantic model sufficiency routing** — infer whether *this exact weak model* will be good enough relative to *this exact strong model*.

The first is well supported and increasingly productionized. The second still needs trustworthy model-outcome evidence. The project has already falsified two close relatives of the naive version: a cluster router (`val 0.4155`) and a BERT-family classifier (`macro-F1 0.5612` against its preregistered gate). Re-running “prompt embedding similarity directly decides weak vs strong” would therefore be a poor use of effort unless the signal is used in a materially different way.

The recommended use is **Semantic Routing 2.0: semantic signals condition and protect the value router; they do not substitute for the value signal.**

## What current semantic-routing systems actually show

### vLLM Semantic Router: useful architecture, not a free-label oracle

The current vLLM Semantic Router explicitly implements a `signals -> projections -> decisions -> model selection` control plane. Its maintained signals include domain, complexity, embeddings, context, structure, preference, user feedback, safety and other request/runtime facts. This is architecturally very close to what the Hermes uplift needs: policy and privacy remain deterministic, while learned semantic signals become reusable facts rather than opaque final decisions.

Source: [vLLM Semantic Router introduction](https://github.com/vllm-project/semantic-router/blob/main/website/docs/intro.md).

However, its learned model-selection pipeline is **not a solution to cheap retraining labels**. The official training README says the selector should be trained from records where candidate models have actually been benchmarked on queries; the benchmarker sends each unique query to every configured model, and the docs warn that it “does not create trustworthy labels from model names alone.” It supports KNN, KMeans, SVM and MLP selectors over historical performance.

Sources: [ML model-selection training](https://github.com/vllm-project/semantic-router/blob/main/src/training/model_selection/ml_model_selection/README.md), [ML model selection docs](https://vllm-sr.ai/docs/training/ml-model-selection/).

**Implication:** vLLM SR is attractive as a replaceable runtime signal plane and shadow harness, but its vanilla learned selector preserves the exact supervision cost this mission is trying to remove.

### “When to Reason”: proof that semantic classification can save cost, but on an easier target

The 2025 *When to Reason: Semantic Router for vLLM* paper classifies whether a query needs reasoning mode and reports +10.2 percentage points accuracy on MMLU-Pro while reducing response latency 47.1% and token consumption 48.5% versus direct inference in its setting.

Source: [Wang et al., 2025](https://arxiv.org/abs/2510.08731).

This is real evidence that semantic classification can be economically valuable. It is **not** evidence that prompt-only semantics recovers the pairwise outcome `gpt-4-1106-preview` vs `mistral-7b-chat`. “Does this look reasoning-heavy?” is a substantially more semantic/intensional label than “will model A actually rescue model B on this sampled instance?” The latter depends on model capability, answer stochasticity, evaluation quirks and task-specific partial credit.

### Aurelio Semantic Router: fast intent routing, limited evidence for model-quality selection

Aurelio's Semantic Router uses vector-space semantic matching as a zero-LLM-call decision layer. This is compelling for intent/tool/policy routing because latency is tiny and the output can abstain below a similarity threshold.

Source: [Aurelio Semantic Router](https://www.aurelio.ai/semantic-router).

But that is again an **intent matching** problem. It does not establish that cosine similarity can estimate marginal model quality. The project's failed cluster router is direct local evidence that coarse semantic geometry alone was insufficient for the current target.

### 2026 evidence cautions against betting on embeddings alone

*LLMRouterBench* re-evaluated 10 representative routers across 400K+ instances, 21 datasets and 33 models. It found leading routing methods often surprisingly similar under unified evaluation, found that embedding-backbone choice had limited impact, and attributed much of the remaining oracle gap to model-recall failures rather than representation choice.

Source: [Li et al., Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.1881/).

*LatentGate* offers a separate warning from agent routing: vanilla embedding routers can collapse semantically similar but functionally different intents because of representation anisotropy. It uses frozen SLM hidden states, PCA whitening and a linear probe, reporting 98.8% in-domain and 80.0% OOD accuracy across 100 agents, 13–22 points above embedding baselines in that task.

Source: [Ratnakar et al., ACL Industry 2026](https://aclanthology.org/2026.acl-industry.153/).

**Implication:** changing `bge-small` to a fancier embedding tower is low-EV. If semantic features are used, test the *information they add* rather than assuming a better embedding fixes supervision.

## The version of semantic routing worth testing

### Semantic signals as conditioning features

Use frozen, cheap semantic facts to condition a value model:

- task/domain family;
- coarse complexity/reasoning demand;
- prompt structure (multiple choice, code, free form, long context);
- distance/density relative to clean historical examples;
- nearest-neighbor historical weak-success and strong-rescue rates;
- judge-error propensity by semantic/task stratum.

These features answer **where we are in task space**, while outcome labels answer **what the weak/strong pair tends to do there**.

### Semantic performance memory, not semantic clustering

The failed cluster router assigned a route based on semantic clusters. A different method has now gained stronger evidence: **retrieve nearby queries and aggregate their measured model performance**. ContextualRouter (EACL SRW 2026) reports that simple k-nearest-neighbor averaging is often competitive with more complex generalizable routers and remains useful with as little as 1% historical data.

Source: [Varangot-Reille et al., EACL 2026](https://aclanthology.org/2026.eacl-srw.22/).

This is materially different from the falsified cluster attempt:

- cluster routing: `prompt -> cluster -> fixed route`;
- performance memory: `prompt -> neighbors -> empirical model outcome distribution -> cost-aware decision`.

The latter preserves local outcome information rather than assuming semantic membership implies a fixed model choice.

### Semantic OOD guard

Embedding distance may be more valuable as a **risk detector** than a selector. If a query lies far outside the support of clean historical observations, route conservatively or place it in a shadow/audit queue. This is cheap and prevents the router from extrapolating with false confidence.

### Semantic stratification of label acquisition

When buying sparse exact truth, semantic space should determine *coverage*, not the target itself. Sample from:

- high predicted escalation-value uncertainty;
- regions where judge and deterministic signals disagree;
- underrepresented semantic/task strata;
- a small random sentinel sample to detect blind spots.

This prevents active-learning collapse where the system only labels examples its current model already knows are interesting.

## Proposed Hermes architecture

```text
Tier 0  deterministic policy/privacy/capability eligibility
   ↓
Tier 1  semantic signal plane
        domain · complexity · structure · OOD distance · performance-neighbor support
   ↓
Tier 2  escalation-value estimator
        P(weak fails | x) × E[strong gain | weak fails, x]
   ↓
Tier 3  risk / abstention guard
        low support · high disagreement · drift · policy sentinel
   ↓
Tier 4  weak/strong dispatch and provider routing
   ↓
        accepted-outcome telemetry → performance memory / bandit feedback
```

This mirrors the parent Hermes principle that deterministic eligibility precedes learned routing and keeps routing implementations replaceable.

## Cheap experiment that does not redo the falsified cluster router

See [`../experiments/005-semantic-signal-ablation-prereg.md`](../experiments/005-semantic-signal-ablation-prereg.md).

The experiment adds semantic information only as auxiliary risk/performance features and compares:

1. no semantic augmentation;
2. task/domain only;
3. kNN performance memory only;
4. OOD guard only;
5. combined.

It explicitly forbids KMeans/cluster-to-route reimplementation.

## Bottom line

**Semantic routing is viable and strategically useful, but the innovation is to separate “semantic understanding” from “economic model selection.”** The semantic layer should describe and bound the request. The value layer should estimate the marginal benefit of escalation using trustworthy outcome evidence. That separation makes the system more explainable, safer under drift, and much cheaper to refresh than a monolithic semantic classifier.
