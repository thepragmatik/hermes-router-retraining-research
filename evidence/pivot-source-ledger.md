# Pivot evidence ledger — stackable trust-and-escalation research

**Date:** 2026-09-06  
**Purpose:** evidence supporting the pivot from a single prompt-only router toward a response-aware cascade, adaptive cheap compute, model-pool curation, targeted weak-tier uplift, and workflow-stage routing.

This ledger distinguishes peer-reviewed evidence from newer preprints/product evidence. Published gains are **priors**, not promised transfer to the Hermes model pair or workloads.

| Source | Venue/year | Evidence used | Relevance / caveat |
|---|---|---|---|
| [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/) | Findings ACL 2026 | 400K+ instances, 21 datasets, 33 models; many routers similar; embedding backbone limited impact; careful model curation beats blindly growing ensembles; persistent model-recall gap | **Very high pivot relevance.** Supports moving effort from router architecture to pool/signals/system design |
| [A Unified Approach to Routing and Cascading for LLMs](https://proceedings.mlr.press/v267/dekoninck25a.html) | ICML 2025 | formal treatment of routing/cascading; unified cascade routing; quality estimator critical; combined strategy improves over isolated paradigms in experiments | **Very high.** Direct support for response-aware cascade architecture |
| [BEST-Route](https://proceedings.mlr.press/v267/ding25d.html) | ICML 2025 | jointly chooses model and number of test-time samples; up to 60% cost reduction with <1% drop in tested datasets | **Very high.** Supports cheap multi-sampling as an action, not only model choice |
| [AutoMix](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ecda225cb187b40ea8edc1f46b03ffda-Abstract-Conference.html) | NeurIPS 2024 | weak model generates then self-verifies; routes/escalates from response-aware signal; >50% compute cost reduction at comparable performance in tested settings | **High.** Direct response-aware cascade prior |
| [Select-then-Route](https://aclanthology.org/2025.emnlp-industry.28/) | EMNLP Industry 2025 | taxonomy reduces candidate set, then confidence cascade; reported 94.3% vs 91.7% best-single and 4× lower cost across six benchmarks | **High.** Strong evidence for stacking coarse task selection + cascade; multi-judge cost must be checked locally |
| [Confidence-Informed Self-Consistency](https://aclanthology.org/2025.findings-acl.1030/) | Findings ACL 2025 | confidence-weighted voting reduces reasoning paths >40% on average across 9 models/4 datasets | **High.** Supports adaptive second/third cheap sample |
| [Difficulty-Adaptive Self-Consistency](https://aclanthology.org/2025.findings-naacl.383/) | Findings NAACL 2025 | adapts sample allocation to question difficulty rather than fixed N | **High method prior.** Relevant to early-stopping cheap samples |
| [Learning to Route LLMs with Confidence Tokens / Self-REF](https://proceedings.mlr.press/v267/chuang25b.html) | ICML 2025 | lightweight confidence-token training improves routing/rejection vs verbalized confidence/token probability; evaluated with Mistral-7B-Instruct among local models | **Very high.** New signal source materially different from prompt embeddings |
| [BaseCal](https://aclanthology.org/2026.acl-long.234/) | ACL 2026 | hidden-state/base-model calibration; average 42.9% ECE reduction vs best unsupervised baselines across 5 datasets/3 families | **High.** Supports internal-state confidence calibration |
| [LatentGate](https://aclanthology.org/2026.acl-industry.153/) | ACL Industry 2026 | frozen SLM hidden states + PCA whitening + linear probe beat embedding baselines in 100-agent intent routing | **Medium/high representation prior.** Different target, but supports probing SLM internals instead of generic embeddings |
| [Conformal LLM Routing](https://aclanthology.org/2026.acl-srw.70/) | ACL SRW 2026 | calibrated cheap-routing violation bounds under assumptions; routability depends on model and task | **High policy prior.** Does not create signal; useful for abstention/safe coverage |
| [Scaling Test-Time Compute Without Verification or RL is Suboptimal](https://proceedings.mlr.press/v267/setlur25a.html) | ICML 2025 | theory + experiments argue verification is important for efficiently scaling test-time compute | **High.** Supports verifier ladder, cautions against blind resampling |
| [DA-KD](https://proceedings.mlr.press/v267/he25c.html) | ICML 2025 | difficulty-aware distillation focuses training budget on hard samples; reports +2% vs prior methods with half training cost in setting | **High for targeted weak uplift.** Not a guarantee for Mistral/RouterBench |
| [SmartAD](https://aclanthology.org/2026.findings-acl.1349/) | Findings ACL 2026 | student-compatible teacher trajectory selection + action/final-decision weighting improves 1.5B/3B agent distillation | **High strategic prior.** Especially relevant to future Hermes agentic traces |
| [MTRouter](https://aclanthology.org/2026.acl-long.2045/) | ACL 2026 | turn-level routing from history/model embeddings; reports >GPT-5 ScienceWorld with 58.7% lower cost and HLE competitive at 43.4% lower cost | **Very high strategic evidence.** Suggests route the trajectory/turn, not only initial prompt |
| [LLM-as-Scheduler](https://aclanthology.org/2026.acl-long.581/) | ACL 2026 | dynamically selects workflow; 43% token and >36% latency reduction with ≤1.4pp accuracy loss vs strong fixed workflow | **Very high for Hermes.** Supports routing workflows/interventions |
| [Faster Cascades via Speculative Decoding](https://research.google/pubs/faster-cascades-via-speculative-decoding/) | ICLR 2025 | combines cascade deferral with speculative decoding; matches regular-cascade quality at lower inference cost in tested T5/Gemma tasks | **Medium/high left-field systems option.** Requires serving-level compatibility |
| [RLM-Cascade](https://arxiv.org/abs/2606.22840) | preprint 2026 | response-level draft/accept/enhance; reports 45.8% API cost reduction on 125 Claude Code production requests | **Interesting but lower confidence.** Small preprint evidence; use only after ordinary cascade works |
| [DeepSeek V4 Flash 0731 pricing](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) | current service 2026 | example current cheap capable model listed at $0.05/M input, $0.16/M output | **Economic screening evidence only.** Price/provider availability changes; quality must be evaluated locally |
| [gpt-oss-120b pricing](https://openrouter.ai/openai/gpt-oss-120b/pricing) | current service 2026 | current provider listing as low as $0.03/M input, $0.17/M output | **Economic screening evidence only.** Do not infer local quality from price/model description |

## Evidence synthesis

### Strongest supported pivot

The highest-confidence shift is from **single-commit prompt routing** to a **cheap-answer-first cascade with multiple complementary trust signals**. This conclusion is supported by peer-reviewed routing/cascade work and by the local fact that the earlier prompt/label-driven experiment family did not pass.

### Stackable components with distinct information sources

1. response-aware cascading;
2. adaptive cheap resampling;
3. internal-state/confidence probing;
4. deterministic/task verifiers;
5. calibrated abstention;
6. curated mid-tier model;
7. targeted weak-tier uplift;
8. workflow-stage routing for agentic traffic.

The value of stacking depends on **error diversity**. If two layers make the same mistakes, apparent standalone gains may not compose. The pivot execution plan therefore requires incremental ablations and pairwise overlap analysis.

### What remains uncertain

- whether the historical Mistral model's internal states contain a useful correctness signal on the exact project tasks;
- whether extra local samples produce enough independent error diversity to justify latency;
- which current cheap model, if any, provides useful complementarity to the local tier;
- whether targeted LoRA/distillation can improve the specific recurring rescue clusters without regressions;
- how much of Hermes's real cost is addressable by turn/workflow-stage routing rather than single-turn routing.

These are empirical questions and are the next phase's highest-value tests.