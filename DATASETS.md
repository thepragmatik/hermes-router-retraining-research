# Dataset strategy for the Hermes routing mission

## Purpose

This mission may use public routing datasets to reduce experimental cost, stress-test methods, and improve generalization. They must **not** be treated as substitutes for exact-pair evidence unless the model pair and task semantics actually match.

The mission's qualification truth remains the pinned local RouterBench-0shot train/validation data for `mistralai/mistral-7b-chat` vs `gpt-4-1106-preview`. The sealed RouterBench test split remains untouched.

## Core dataset principle — useful only when used with discipline

> **A few datasets are genuinely useful, but only if the mission is disciplined about how they are used.**

More data is not automatically better for this routing problem. Routing labels are unusually context-specific: they depend on the exact model pair, evaluator, prompt distribution, task semantics, sampling behavior, and sometimes the price assumptions used to define a preferred route. A large external dataset can therefore make an experiment look statistically stronger while making it **less relevant to the actual Hermes routing decision**.

The agent must treat each dataset as evidence for a specific purpose, not as generic training material. Before using an external dataset, answer four questions:

1. **What question is this dataset allowed to answer?** Exact-pair qualification, transfer/warm start, method stress test, or unlabeled/OOD coverage?
2. **What can it not answer?** For example, a Mixtral-vs-GPT-4 preference label is not ground truth for Mistral-7B-vs-GPT-4 marginal rescue.
3. **Could it contaminate local validation?** Benchmark reuse and near-duplicate prompts are common across routing datasets.
4. **Does it change the decision enough to justify its complexity/cost?** If not, do not download, embed, or train on it.

This principle has three practical consequences:

- **local exact-pair evidence always outranks external evidence** for the immediate router-refresh decision;
- **external datasets are used selectively as evidence amplifiers**, not pooled indiscriminately into one training set;
- **every external-data experiment keeps a local-data-only control at the same local strong-label budget**, so any claimed benefit is attributable and economically meaningful.

The mission should prefer a smaller, clearly relevant dataset over a larger but mismatched one. The goal is not maximum data volume; the goal is the **cheapest trustworthy evidence needed to make the routing decision**.

## Dataset tiers

### Tier A — primary exact-pair qualification data

#### [`withmartian/routerbench`](https://huggingface.co/datasets/withmartian/routerbench) — pinned `routerbench_0shot.pkl`

**Role:** mandatory primary dataset.

Why it matters:

- contains prompt-level outputs/performance for the historical model pool;
- includes the exact weak/strong pair used by router v1;
- supports train-only counterfactual audits, sparse-label masking, FEV, semantic performance-memory, and bandit replay;
- has task-native correctness/evaluation structure for many objective families.

**Allowed use:** train and validation only according to the project's frozen hash split and experiment preregistrations.

**Forbidden use:** do not inspect/re-evaluate the sealed test split; do not replace the pinned 0-shot artifact with 5-shot/raw data while claiming comparability.

---

### Tier B — high-value external routing stress tests

These datasets can answer whether a method is robust beyond the exact historical pair. They cannot set the final Hermes promotion gate.

#### [`Wikit/RoutingCompendium-perf`](https://huggingface.co/datasets/Wikit/RoutingCompendium-perf) + [`Wikit/RoutingCompendium-cost`](https://huggingface.co/datasets/Wikit/RoutingCompendium-cost)

**Recommended external dataset #1.**

The compendium harmonizes five public routing benchmarks into one row-per-query schema, with per-query candidate performance, prompt embeddings, and companion model-cost data. Current splits include RouterBench, Sprout, EmbedLLM, FusionBench, and R2Bench (~133k total performance rows across pools of roughly 10–112 candidate models).

**Use for:**

- sparse-label acquisition simulations;
- kNN/performance-memory routing;
- FEV/value-routing generalization;
- bandit replay;
- robustness of cost-quality Pareto-frontier code;
- testing whether conclusions depend on one model pair or one benchmark.

**Do not use for:**

- choosing the final local validation threshold;
- claiming exact Mistral-7B/GPT-4 lift;
- importing its RouterBench split into local training without deduplication/provenance checks.

Each split inherits the source benchmark's license; record the exact split, revision and license used.

#### [`ynulihao/LLMRouterBench`](https://github.com/ynulihao/LLMRouterBench) pre-collected benchmark results

**Recommended external dataset #2.**

LLMRouterBench provides standardized per-instance outputs/scores/costs across 21+ datasets and 33 models, including a performance-cost setting with modern flagship models and tasks such as LiveCodeBench, SWE-Bench, MMLU-Pro, SimpleQA, ArenaHard and tool-use benchmarks.

**Use for:**

- cross-model-pool stress testing of FEV/marginal-gain ideas;
- checking whether semantic/task conditioning generalizes;
- testing model-recall failure and sparse-sentinel policies;
- verifying cost-quality frontier logic on modern costed model pools;
- testing bandit replay beyond the RouterBench historical pair.

**Default:** external validation/stress test only after the local RouterBench train/validation experiment is implemented correctly.

---

### Tier C — transfer priors / warm-start data

These may improve representation learning or provide transfer baselines, but the model pair differs from the mission's exact weak model.

#### [RouteLLM public datasets](https://huggingface.co/routellm/datasets)

Useful assets include:

- [`routellm/gpt4_judge_battles`](https://huggingface.co/datasets/routellm/gpt4_judge_battles) — ~109k Apache-2.0 pairwise battles, using `gpt-4-1106-preview` vs `mixtral-8x7b-instruct-v0.1`;
- [`routellm/gpt4_dataset`](https://huggingface.co/datasets/routellm/gpt4_dataset) — corresponding prompts/responses/scores;
- `routellm/arena_battles_embeddings` and `routellm/gpt4_judge_battles_embeddings` — precomputed embedding variants;
- `routellm/mmlu_battles` / embeddings — ~1.5k MMLU augmentation rows.

**Use for:**

- optional MF/router warm start;
- transfer-learning ablations;
- semantic-performance retrieval priors;
- testing whether external preference data lowers the amount of local exact-pair truth needed.

**Critical limitation:** the weak model is Mixtral-8x7B, not this mission's Mistral-7B-chat. Therefore these labels are **transfer priors, never local ground truth**.

Any use must include a local-data-only baseline and report whether external data helps at the same local strong-label budget.

#### [`RZ412/EmbedLLM`](https://huggingface.co/datasets/RZ412/EmbedLLM)

EmbedLLM releases an Apache-2.0 correctness matrix plus train/val/test data, model/question order files, and trained model embeddings. It covers a large multi-model pool and the full public artifact is large (roughly tens of GB).

**Use for:**

- correctness-forecasting stress tests;
- sparse-label scaling experiments;
- validating whether FEV/performance-memory ideas work on a many-model correctness matrix;
- optional representation pretraining research.

**Default:** do not download the full dataset unless a specific experiment needs it; `RoutingCompendium` already exposes a lighter harmonized EmbedLLM split with prompt embeddings.

---

### Tier D — real-world prompt/preference distribution, not pairwise correctness truth

#### [`lmarena-ai/arena-human-preference-55k`](https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k)

~55k real-world Arena battles across 70+ models, Apache-2.0.

**Use for:**

- semantic/domain coverage analysis;
- OOD/support stress tests;
- optional prompt-distribution pretraining;
- testing whether the router's semantic signal plane covers real user traffic better than benchmark-only prompts.

**Do not use human preference labels as correctness truth for the Hermes weak/strong pair.** Preference, correctness and marginal rescue are different targets.

#### [`lmsys/lmsys-chat-1m`](https://huggingface.co/datasets/lmsys/lmsys-chat-1m) (optional)

One million real-world conversations. Useful only if the mission later needs a large unlabeled prompt distribution for semantic/OOD coverage. It is not required for the core experiments and should not be downloaded by default. Verify current access terms/license before use.

---

## Mandatory external-data protocol

Before any external dataset affects a trained candidate:

1. **Record provenance:** dataset name, source URL, revision/commit, license, files/splits used and content hashes where practical.
2. **Classify its role:** `exact_pair`, `transfer_prior`, `stress_test`, or `unlabeled_ood`. Never blur these categories in result claims.
3. **Deduplicate:** normalize prompts and remove exact duplicates against local RouterBench train **and validation** before using external rows for fitting. For benchmark-derived datasets, also run a lightweight near-duplicate check because many sources reuse MMLU/GSM8K/MBPP-style prompts.
4. **Protect validation:** no external row that duplicates or near-duplicates a local validation prompt may be used for training, warm start, retrieval memory, or threshold selection.
5. **Protect the sealed test:** never inspect local test prompts to deduplicate. Test remains sealed; external-data hygiene is performed against train/validation only.
6. **Preserve local baselines:** every external-data experiment must compare against the same method trained only on local data at the same local strong-label budget.
7. **No promotion by external score alone:** the mission's primary promotion gate remains local validation APGR >= 0.6459 plus refresh economics.
8. **Cost the dataset:** report download/storage/embedding/training overhead when it is materially non-zero; a giant public dataset is not 'free' if it makes refresh operationally expensive.

## Recommended order of use

Do **not** start by downloading everything.

1. Run Experiment 000 on the pinned local RouterBench train data.
2. Run the local sparse-label/FEV experiments first.
3. If a local candidate is viable, use `RoutingCompendium` as the first external stress test because it is harmonized and already includes embeddings/cost information.
4. Use LLMRouterBench when a modern-model / modern-task generalization check would change the decision.
5. Use RouteLLM data only for a preregistered transfer/warm-start experiment.
6. Use full EmbedLLM or large Arena/LMSYS prompt corpora only when a specific observed failure justifies their size.

## Success interpretation

External datasets can strengthen confidence that the **method family** generalizes. Only the pinned local pair can establish that the method solves the immediate router-refresh problem.
