# Hermes Router Retraining Research

Adversarially reviewed research on **cheap, repeatable supervision and continual learning for LLM routing**, conducted as a workstream of [`thepragmatik/hermes-pi-agentic-stack`](https://github.com/thepragmatik/hermes-pi-agentic-stack).

**Status:** **ready for agent consumption and experimental execution; not production promotion.** See [Research sign-off](RESEARCH_SIGNOFF.md), [Agent execution mission](AGENTS.md), and the [final mission-design review](MISSION_DESIGN_REVIEW.md).

The deployed router already works. This repository asks the strategically harder question:

> How can routing remain economically useful when models, prices and workloads change—without fully evaluating every candidate model on tens of thousands of prompts every retrain?

## Revised headline finding

The strongest design after the second-pass red team is **Factorized Escalation Value (FEV)**:

```text
weak-failure probability
        ×
strong-rescue probability
        −
incremental model cost
        =
expected value of escalation
```

Broad weak-model correctness can often be regenerated cheaply from weak-only outputs and task-native/mission-native evaluators. Strong-model labels are then needed only to learn **where the strong model actually rescues the weak model**, making sparse strong evaluation plausible.

A second important finding: the failed evidence-mode judge is not uniformly bad. The mission's aggregate rates imply its `needs strong` predictions are ~96% precise, while its `weak sufficient` predictions are only ~58.5% reliable. The repository therefore proposes **one-sided / positive-unlabeled supervision** rather than treating all judge labels as symmetric ground truth.

## Semantic routing verdict

**Viable as a signal/control layer; not as a naive prompt-similarity final selector.**

Use semantic routing for task/domain, complexity, historical-performance retrieval, OOD/support detection, judge calibration and label-budget allocation. Do not rerun the falsified KMeans cluster-to-route approach.

See [Semantic routing review](evidence/semantic-routing-review.md).

## Public dataset strategy

The mission now includes a deliberate external-data plan in [`DATASETS.md`](DATASETS.md).

- the pinned RouterBench 0-shot artifact remains the **only exact-pair qualification dataset** for the historical Mistral-7B-chat / GPT-4-1106-preview pair;
- `Wikit/RoutingCompendium` is the preferred external method stress test because it harmonizes multiple routing benchmarks with per-query model outcomes, prompt embeddings and companion cost data;
- `LLMRouterBench` is the modern cross-model/task robustness test;
- RouteLLM and EmbedLLM data are transfer/method priors, not local exact-pair truth;
- Arena/LMSYS data is useful for real-world semantic/OOD coverage, not pairwise correctness labels.

External data must be provenance-tracked and deduplicated against local train/validation before it can affect training. External scores never override the local validation APGR gate.

## Read first

- [Research sign-off](RESEARCH_SIGNOFF.md)
- [Agent execution mission](AGENTS.md)
- [Dataset strategy](DATASETS.md)
- [Final mission-design review](MISSION_DESIGN_REVIEW.md)
- [Ranked options memo — adversarially reviewed v2](memo/2026-09-05_ranked-options-memo.md)
- [Adversarial review v2](evidence/adversarial-review.md)
- [Semantic routing review](evidence/semantic-routing-review.md)
- [Derived judge-noise analysis](evidence/judge-noise-derived-analysis.md)
- [Hermes Value Router Learning Flywheel](designs/router-learning-flywheel.md)
- [Source ledger](evidence/source-ledger.md)

## Experiment queue

1. [Experiment 000 — target sufficiency / rescue audit](experiments/000-target-audit-prereg.md) — **run first, $0**
2. [Experiment 003 — Factorized Escalation Value](experiments/003-factorized-escalation-value-prereg.md) — $0 retrospective sparse-label simulation
3. [Experiment 004 — one-sided judge / PU](experiments/004-one-sided-pu-prereg.md) — $0
4. [Experiment 005 — semantic-signal ablation](experiments/005-semantic-signal-ablation-prereg.md) — $0, explicitly not a cluster rerun
5. [Experiment 006 — bandit replay](experiments/006-bandit-replay-prereg.md) — $0 strategic continual-learning test

Earlier preregistrations remain preserved for provenance:

- [Experiment 001 — evaluator-first weak correctness](experiments/001-weak-correctness-prereg.md)
- [Experiment 002 — selective hybrid fallback](experiments/002-selective-hybrid-prereg.md)

## Guardrails

- RouterBench test split remains sealed.
- $0 default spend; paid work is fail-closed and mission total stays <$5.
- ZDR is mandatory for remote judge calls.
- Previously falsified approaches are not recycled without a materially different hypothesis.
- **Research/experiment code is expected in this repository; production runtime integration belongs in the parent Hermes stack after qualification.**
- APGR validation baseline for replacing v1 is **0.6459**; 0.55 is only a viability floor.

## License

Apache License 2.0. See [LICENSE](LICENSE).
