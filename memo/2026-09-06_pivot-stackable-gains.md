# Pivot memo — stackable gains after the first router experiments failed

**Date:** 2026-09-06  
**Status:** research pivot, based on the project operator's report that the previously preregistered experiments did not pass. Exact failed-result tables are not yet present in this repository, so this memo does not invent failure margins.

## Executive answer

The router idea is **not dead**, but the evidence says we should stop betting on a single prompt-only classifier that tries to predict which model will win before either model answers.

The more promising direction is a **stack of small interventions**:

1. let the cheap model answer;
2. inspect signals that only exist *after* it answers;
3. if uncertain, spend a little more cheap compute (another sample, a verifier, a tool check, or a mid-tier model);
4. escalate to the frontier only when the cheap evidence still cannot establish trust;
5. continuously improve the cheap tier on the recurring failures that caused escalation.

Think of this as a **triage ladder**, not a single gate.

```text
request
  ↓
policy / deterministic fast-path
  ↓
cheap model answers
  ↓
answer-aware trust signals
  ├─ internal confidence / hidden-state probe
  ├─ schema / test / tool verifier
  └─ agreement with another cheap sample
  ↓
confident? ── yes → return
  │
  no
  ↓
mid-tier cheap-capable model / specialist
  ↓
resolved? ── yes → return
  │
  no
  ↓
frontier model
  ↓
store failure / outcome → improve weak tier and thresholds
```

The important design rule is **stackability**: every layer must independently improve the quality/cost frontier and must be removable if it does not.

---

# Why this pivot is materially different

The failed research phase mostly tried to learn the routing decision from the **prompt and historical labels**. That is an information-poor decision point. Recent work increasingly combines routing with **cascading**, where the cheap model is allowed to answer first and the system can use response-level evidence.

Dekoninck, Baader & Vechev (ICML 2025) formally unify routing and cascading and report that their combined cascade-routing approach consistently improves over either paradigm alone; they identify the quality estimator as a critical component. [A Unified Approach to Routing and Cascading for LLMs](https://proceedings.mlr.press/v267/dekoninck25a.html).

BEST-Route (ICML 2025) makes a related observation: a single cheap-model response may be insufficient, but **multiple cheap responses can still cost less than one expensive response**. It jointly chooses a model and a test-time sample count, reporting up to 60% cost reduction with less than 1% performance drop in its tested datasets. [BEST-Route](https://proceedings.mlr.press/v267/ding25d.html).

LLMRouterBench (ACL 2026) gives an important negative result for the previous direction: under unified evaluation, many sophisticated routers perform similarly, several fail to beat a simple baseline, embedding backbone choice has limited impact, and careful model-pool curation often matters more than simply enlarging the ensemble. [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/).

**Interpretation:** the highest-EV improvement may now be in the *system around the router*, not a fancier router classifier.

---

# Ranked stackable improvements

## 1. Cheap-answer-first cascade — make the answer part of the routing evidence

### Idea

Run the cheap model first. Decide whether to accept or escalate using the generated answer, not only the prompt.

This creates new evidence that prompt-only routing never sees: whether the answer is internally consistent, whether it satisfies a schema, whether a tool/test can verify it, how confident the model's internal state looks after generation, and whether a second cheap attempt agrees.

### Why it has legs

- **AutoMix** routes after weak-model generation using self-verification and reports >50% compute-cost reduction at comparable performance across its tested settings. [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ecda225cb187b40ea8edc1f46b03ffda-Abstract-Conference.html).
- **A Unified Approach to Routing and Cascading** finds unified cascade-routing better than routing or cascading alone in its experiments. [ICML 2025](https://proceedings.mlr.press/v267/dekoninck25a.html).
- **Select-then-Route** first narrows the model pool by task and then runs a cheap-to-expensive confidence cascade; it reports 94.3% versus 91.7% best-single accuracy with 4× lower inference cost across six benchmarks. [EMNLP Industry 2025](https://aclanthology.org/2025.emnlp-industry.28/).

### Stackability

This is the base architecture. Every later idea plugs into its trust decision.

### Cheap first test

On train/validation-safe data with stored weak answers, compare:

- prompt-only router score;
- answer-aware features;
- prompt + answer-aware features.

Do not build a huge model. Start with simple, auditable signals.

---

## 2. Adaptive cheap resampling — ask the cheap model twice before paying for frontier

### Idea

For uncertain cases only, generate another cheap answer. Agreement is evidence; disagreement is a reason to escalate. Stop early when confidence becomes decisive.

This changes the action space from `weak OR strong` to something like:

`weak×1 → weak×2/3 if uncertain → mid-tier/frontier if still unresolved`.

### Evidence

- **BEST-Route** explicitly exploits multiple cheap responses as an alternative to a single expensive response. [ICML 2025](https://proceedings.mlr.press/v267/ding25d.html).
- **Confidence-Informed Self-Consistency (CISC)** uses confidence-weighted voting and reduces the required reasoning paths by >40% on average across nine models/four datasets. [Findings ACL 2025](https://aclanthology.org/2025.findings-acl.1030/).
- **Difficulty-Adaptive Self-Consistency** dynamically allocates samples rather than using a fixed number for every problem. [Findings NAACL 2025](https://aclanthology.org/2025.findings-naacl.383/).

### Why it is especially interesting here

The local weak model has effectively zero API cost. Extra weak samples cost latency/local compute, but may still be economically preferable to frontier calls.

### Risk

Agreement can be confidently wrong. Therefore use agreement as **one signal**, not the sole oracle, and calibrate by task family.

---

## 3. Internal confidence probe — ask the weak model's internals, not its prose

### Idea

The failed judge and prompt embeddings were external guesses. A local model exposes logits and hidden states that may contain more direct evidence about whether *its own answer* is reliable.

Train a tiny linear/MLP probe on frozen internal states, ideally conditioned on task family. This is cheap and can piggyback on the weak generation forward pass.

### Evidence

- **Self-REF / Learning to Route LLMs with Confidence Tokens** uses lightweight fine-tuning to teach explicit confidence tokens and outperforms verbalized confidence/token-probability baselines on routing/rejection across four datasets and two local models, including Mistral-7B-Instruct. [ICML 2025](https://proceedings.mlr.press/v267/chuang25b.html).
- **BaseCal** maps post-trained hidden states toward the base model's better-calibrated space and reduces ECE by 42.9% on average versus its best unsupervised baselines across five datasets/three families. [ACL 2026](https://aclanthology.org/2026.acl-long.234/).
- **LatentGate** shows frozen SLM hidden states + whitening + a linear probe can substantially beat ordinary embedding routing in a different agent-routing problem. [ACL Industry 2026](https://aclanthology.org/2026.acl-industry.153/).

### Important caveat

Internal self-knowledge can be task-dependent; do not expect one global score to work equally well for math, factual QA, code, and open-ended tasks.

### Cheap first test

Extract a few frozen layers from the current local Mistral run and train tiny correctness probes. Compare AUROC/risk-coverage and downstream routing utility against the current BGE prompt representation.

This is **not** a rerun of the failed BERT classifier: the signal source is the answering model's internal computation, ideally after it has produced an answer.

---

## 4. Add a mid-tier — the two-model gap may be the real problem

### Idea

The historical pool jumps from an old 7B chat model to a frontier GPT-4-era model. That is a very large capability gap. Instead of learning an impossibly sharp binary boundary, use a three-tier ladder:

`local ultra-cheap → modern cheap-capable → frontier`.

A mid-tier can absorb medium-difficulty cases that are too hard for the local model but do not justify frontier cost.

### Evidence

LLMRouterBench finds strong model complementarity but also diminishing returns from blindly adding models; **careful curation** matters. [ACL 2026](https://aclanthology.org/2026.findings-acl.1881/).

The market has also changed dramatically since the historical model pair was chosen. For example, OpenRouter currently lists:

- DeepSeek V4 Flash 0731 at **$0.05/M input, $0.16/M output**; [OpenRouter](https://openrouter.ai/deepseek/deepseek-v4-flash-0731)
- gpt-oss-120b from providers as low as **$0.03/M input, $0.17/M output** on the current pricing page. [OpenRouter](https://openrouter.ai/openai/gpt-oss-120b/pricing)

Prices change; these are examples for screening, not permanent assumptions.

### Left-field implication

A better *cheap* model may create more savings than a better router. If the first-tier model becomes good enough, the classification problem itself becomes easier.

### Cheap first test

On a small train-derived screen (not sealed test), compare 2–3 modern cheap candidates on:

- absolute success;
- unique rescues over Mistral;
- co-failure rate;
- cost per successful rescue;
- latency/tool-use compatibility.

Only add a model if it creates useful complementarity.

---

## 5. Verifier ladder — sometimes verification is cheaper than regeneration

### Idea

Before escalating, use the cheapest reliable check available:

- exact answer / unit / schema check;
- code tests;
- tool execution;
- retrieval/evidence consistency;
- lightweight task-specific verifier;
- only then an LLM critic/judge.

### Evidence

Research on test-time compute finds that verification is crucial for efficient scaling; blindly sampling more without a useful verifier is suboptimal. [Setlur et al., ICML 2025](https://proceedings.mlr.press/v267/setlur25a.html).

### Why this is strategically important for Hermes

Agentic tasks often create their own verification signals: tests pass, a tool call succeeds, a file exists, a schema validates, a search result supports the claim. Those signals can be more trustworthy and cheaper than a generic judge.

### Stackability

Verifier outputs become another feature for the accept/escalate decision and another supervision source for future learning.

---

## 6. Improve the weak model on the exact failures — reduce the need for routing

### Idea

Every recurring escalation is a curriculum. Instead of only teaching a router to recognize hard cases, teach the cheap model to solve the failure clusters it sees repeatedly.

Use LoRA/adapter fine-tuning on **strong-rescue examples** plus matched easy examples to avoid catastrophic specialization. Use stored strong answers/trajectories where possible, so the first experiment can be nearly free.

### Evidence

- **DA-KD** focuses distillation on harder samples and reports better performance with half the training cost than prior KD baselines in its setting. [ICML 2025](https://proceedings.mlr.press/v267/he25c.html).
- **SmartAD** finds that small students learn better when teacher trajectories are selected to fit student capacity and the loss emphasizes actions/final decisions rather than every reasoning token. [Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1349/).

### Why this is different from ordinary distillation

Do not teach the cheap model everything the frontier knows. Teach it the **frequent, economically valuable gaps** that generate frontier spend.

### Risk

Small models can fail to learn reasoning that is far beyond their capacity. Use targeted slices, multiple seeds, and hold out validation.

---

## 7. Conformal / abstention wrapper — make "I don't know" a product feature

### Idea

Instead of demanding that a router rank every prompt perfectly, create a conservative region where cheap answers are accepted and abstain/escalate on everything else.

### Evidence

**Conformal LLM Routing** calibrates a gate to bound the cheap-routed violation rate under its assumptions and shows routability is jointly model- and task-dependent on GSM8K/MMLU with Mixtral/GPT-4. [ACL SRW 2026](https://aclanthology.org/2026.acl-srw.70/).

### Role in the stack

This is not meant to create more raw signal. It turns whatever combined trust score we have into a safer operating policy and makes task-specific thresholds principled.

---

## 8. Route the workflow, not just the model — likely the most important Hermes pivot

### Idea

RouterBench treats a request as one isolated decision. Hermes is agentic. During a long mission, the right question may be:

> Which **workflow step / intervention** deserves expensive intelligence right now?

Examples:

- use cheap model for file browsing and routine transformations;
- use stronger model when tests repeatedly fail or the agent is spinning;
- use search/tool execution instead of a stronger model when missing information is the bottleneck;
- lock a capable model during fragile tool loops, then drop down after the difficult stage passes.

### Evidence

- **MTRouter** explicitly routes model choice at each turn using interaction history; on its tested ScienceWorld setting it surpasses GPT-5 while reducing cost 58.7%, and on HLE it reports 43.4% lower cost with competitive accuracy. [ACL 2026](https://aclanthology.org/2026.acl-long.2045/).
- **LLM-as-Scheduler** dynamically chooses agent workflows and reports 43% token reduction and >36% latency reduction with at most 1.4pp accuracy loss relative to a strong fixed workflow. [ACL 2026](https://aclanthology.org/2026.acl-long.581/).

### Strategic implication

Even if single-turn RouterBench APGR is stubborn, Hermes can still achieve substantial real-world savings by routing **stages and interventions** rather than trying to perfectly predict difficulty from the initial prompt.

This may ultimately matter more than squeezing another few points from the historical benchmark.

---

## 9. Draft → verify/repair instead of throw-away escalation

### Idea

A conventional cascade wastes the cheap answer when it escalates: the strong model starts again. A different design lets the cheap model draft and asks the strong model to **accept, repair, or extend** it.

### Evidence

- Google's **Speculative Cascades** combines cascade deferral with speculative decoding and reports better cost-quality trade-offs than the component techniques on tested reasoning, summarization, coding, translation and QA tasks. [Google Research / ICLR 2025](https://research.google/pubs/faster-cascades-via-speculative-decoding/).
- **RLM-Cascade** (2026 preprint) applies the idea at response level for API models; on 125 reported Claude Code production requests it reports 45.8% API cost reduction and lower median latency versus its Opus baseline. [arXiv](https://arxiv.org/abs/2606.22840). Treat this as promising but less established than the peer-reviewed evidence above.

### Why it is left-field

It changes escalation from "discard cheap work and pay again" to "reuse cheap work and buy only the missing capability."

---

# The proposed stack

The research now favors this sequence:

### Layer A — deterministic eligibility and cheap task routing

Keep privacy/security/capability rules deterministic. Identify task family only where it changes the applicable model/tool/verifier—not to predict difficulty directly.

### Layer B — cheap model produces the first answer

The local/cheap model is no longer just a feature generator; it does useful work.

### Layer C — trust bundle

Combine **different kinds of evidence** whose failure modes are not identical:

- internal hidden-state/logit confidence;
- answer format/schema/test results;
- one additional cheap sample when needed;
- agreement / disagreement;
- task-specific verifier;
- OOD/support signal.

Do not expect any single feature to clear the old APGR bar by itself.

### Layer D — mid-tier rescue

Use a carefully selected modern inexpensive model for medium cases.

### Layer E — frontier

Reserve frontier spend for cases that remain unresolved after the cheap evidence ladder.

### Layer F — feedback improvement

Store frontier-rescued failure clusters. Periodically fine-tune the cheap tier on repeated, learnable gaps. The objective is to make the escalation distribution shrink over time.

---

# How to test stackability without creating another giant experiment

The next research phase should behave like controlled engineering rather than another monolithic model search.

## P0 — model-pool audit

Question: is the historical Mistral weak tier itself now the bottleneck?

Screen Mistral plus 2–3 current inexpensive models on a train-only/calibration sample. Measure success, unique rescue, co-failure, latency and token cost. Reject models that merely duplicate another model's successes.

## P1 — cheap resampling audit

For the local weak model, generate 1/2/3/5 samples on train-only examples. Measure:

- majority/best-of-N gain;
- agreement vs correctness;
- how often a second sample resolves uncertainty;
- local compute/latency.

This directly tests whether extra cheap compute can replace strong calls.

## P2 — internal-state confidence probe

Train a tiny frozen-state correctness/reliability probe from the answering model's hidden states/logits. Evaluate globally and by task family. Compare against prompt embedding and verbal confidence.

## P3 — incremental trust-stack ablation

Start from cheap answer only, then add **one layer at a time**:

1. + deterministic checks;
2. + internal probe;
3. + adaptive second sample/agreement;
4. + verifier;
5. + OOD/abstention calibration.

For every added layer, report its marginal quality gain, strong-call reduction, latency and complexity. A layer that does not move the Pareto frontier is removed.

## P4 — three-tier cascade

Compare:

- local → frontier;
- local → modern cheap/mid-tier → frontier.

Use the same trust stack. The question is whether a middle capability tier cheaply absorbs ambiguous cases.

## P5 — failure-focused weak-model uplift

Fine-tune/LoRA the local model on recurring `weak failed / stronger succeeded` training examples plus a matched replay set. Run multiple seeds. Measure whether the same trust stack now escalates fewer prompts at equal quality.

## P6 — Hermes agentic shadow track

Separate from the historical RouterBench qualification question, replay/observe Hermes missions and identify stages where expensive models actually create marginal mission value. Test stage-aware escalation signals such as repeated tool errors, failed tests, lack of progress, long reasoning loops, or retrieval uncertainty.

This protects the program from optimizing the wrong benchmark forever.

## P7 — optional draft/repair

Only after a strong/mid-tier cascade is useful, test whether escalation can reuse the cheap draft instead of regenerating from scratch.

---

# What I would *not* spend more time on now

1. Another large prompt-embedding classifier.
2. KMeans / generic semantic cluster → model routing.
3. A larger neural router trained on the same failed labels.
4. Another broad LLM judge used as symmetric ground truth.
5. Blindly adding many models to the pool.
6. Optimizing RouterBench APGR as the only strategic objective for an agentic system.

These may still appear as components or baselines, but they should not be the center of the next phase.

---

# Friendly non-technical version

The first version of the project was like putting a receptionist at the door and asking:

> "From the question alone, can you tell whether this person needs the junior employee or the expensive expert?"

We tried several ways of making the receptionist smarter. They did not pass the bar.

The new approach is more like a real triage system:

1. let the junior employee try;
2. automatically check the work;
3. if it looks doubtful, ask for a second cheap opinion;
4. if it is still doubtful, send it to a competent but inexpensive specialist;
5. only then call the expensive expert;
6. every time the expert fixes something, teach the junior how to handle that type of problem next time.

No single step has to be magical. A 3–5% improvement from several independent steps can compound into a meaningful system improvement—provided every step is measured against total cost and quality.

---

# Overall research verdict

**Pivot from "learn one perfect router" to "engineer an adaptive trust-and-escalation stack."**

The literature increasingly supports this direction: combined routing+cascading, adaptive test-time sampling, output-aware confidence, careful model-pool curation, selective verification, and multi-turn workflow routing all attack different sources of waste. The attractive feature for Hermes is that they can be tested and deployed incrementally.

The biggest left-field bets are:

1. **replace/augment the historical weak model** before trying to make the router smarter;
2. **route the intervention/workflow stage**, not only the model;
3. **reuse cheap drafts on escalation**;
4. **use frontier failures as a curriculum** to continuously improve the cheap tier.

These are more likely to create durable economic value than another round of classifier tuning on the same signal.