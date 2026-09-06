# Hermes Router Retraining Research

Research on **cost-effective, adaptive LLM/agent routing** for [`thepragmatik/hermes-pi-agentic-stack`](https://github.com/thepragmatik/hermes-pi-agentic-stack).

## Current status — 2026-09-06 pivot

The project operator reports that the first execution phase's proposed router experiments **did not pass their gates**. Exact result tables are not yet committed here, so this repository does not invent margins or rewrite those attempts as near-successes.

That result changes the research direction.

> **Current thesis: stop looking for one perfect prompt-only router. Build and measure a stack of small, response-aware interventions that can compound: cheap answer → trust signals → extra cheap compute/verifier → curated mid-tier → frontier, while using recurring frontier rescues to improve the cheap tier.**

### Active execution documents

- **[Canonical mission — Stackable Trust, Escalation, and Agentic Routing](STACKABLE_ROUTING_MISSION.md)** — source of truth for objective, experiment order, gates, economics, stop rules, and deliverables.
- **[Launch prompt](LAUNCH_AGENT_PROMPT.md)** — ready-to-paste instruction for an execution-capable agent.
- [Agent entrypoint](AGENTS.md) — concise repository-level instructions that point to the canonical mission.
- [Pivot memo — stackable gains after the first experiments failed](memo/2026-09-06_pivot-stackable-gains.md)
- [Pivot evidence/source ledger](evidence/pivot-source-ledger.md)
- [Dataset strategy](DATASETS.md)

The older `PIVOT_EXECUTION_PLAN.md` remains useful design provenance, but `STACKABLE_ROUTING_MISSION.md` is now the canonical active specification if the two differ.

The prior FEV/weak-correctness/judge/semantic/bandit research is preserved below as **historical provenance**, not the current recommended center of effort.

## Why the pivot

Recent unified evidence suggests router architecture itself often has limited leverage: many sophisticated routers perform similarly, embeddings are not the main bottleneck, and careful model-pool curation matters. At the same time, newer cascade research shows gains from using information that exists **after a cheap model answers**, from adaptive multiple cheap samples, from internal confidence signals, from verification, and from routing across workflow stages rather than only at the initial prompt.

The new design therefore treats routing as an **adaptive trust-and-escalation ladder**:

```text
policy-safe request
      ↓
cheap model answers
      ↓
trust bundle
  ├─ deterministic checks / tests / tools
  ├─ internal hidden-state/logit confidence
  ├─ adaptive extra cheap sample + agreement
  ├─ task verifier
  └─ OOD / abstention calibration
      ↓
accept? ─ yes → return
  │
  no
  ↓
curated mid-tier / specialist
      ↓
accept? ─ yes → return
  │
  no
  ↓
frontier
      ↓
store rescue → improve cheap tier
```

Every layer must independently move the measured cost/quality frontier or it is removed. The objective is **not to maximize stack complexity**.

## Highest-value pivot tests

1. **Model-pool audit:** determine whether the historical Mistral weak tier itself is now the bottleneck; screen a few current inexpensive models for complementary successes, not just aggregate score.
2. **Adaptive cheap sampling:** test whether a second/third local answer resolves enough uncertainty to avoid frontier calls.
3. **Deterministic verification:** use tests, schemas, tools and task-native checks to safely accept/reject a subset before learned trust models.
4. **Internal confidence probe:** use the answering model's hidden states/logits rather than only prompt embeddings or verbal confidence.
5. **Trust-stack ablation:** add answer-aware layers one at a time; retain only paying layers and measure error overlap.
6. **Three-tier cascade:** test `local → inexpensive modern mid-tier → frontier` instead of forcing a binary old-7B/frontier boundary.
7. **Failure-focused weak-model uplift:** LoRA/distill on recurring economically valuable failure/rescue clusters using stored strong evidence first.
8. **Hermes workflow-stage routing:** measure whether expensive intelligence is needed only at particular turns/stages of real agent missions.
9. **Optional draft/repair:** reuse cheap work when escalating rather than discarding it.

See [STACKABLE_ROUTING_MISSION.md](STACKABLE_ROUTING_MISSION.md) for the complete frozen execution discipline and deliverables.

## Public dataset strategy

Use [`DATASETS.md`](DATASETS.md) deliberately. External data is an evidence amplifier, not exact-pair truth.

- pinned RouterBench 0-shot remains the historical exact-pair qualification corpus;
- RoutingCompendium and LLMRouterBench are useful cross-pool stress tests;
- RouteLLM/EmbedLLM are transfer/method priors;
- Arena/LMSYS are useful for semantic/OOD coverage, not local correctness truth.

## Historical phase — retained for provenance

The earlier research explored:

- Factorized Escalation Value / sparse strong rescue labels;
- evaluator-first weak correctness;
- one-sided judge / positive-unlabeled learning;
- semantic performance memory/OOD signals;
- bandit feedback;
- selective hybrid labels.

Those documents remain useful as evidence and negative results. Do not rerun them unchanged after the reported failure of that experiment phase.

Historical starting points:

- [2026-09-05 ranked options memo](memo/2026-09-05_ranked-options-memo.md)
- [Adversarial review](evidence/adversarial-review.md)
- [Semantic routing review](evidence/semantic-routing-review.md)
- [Original learning flywheel](designs/router-learning-flywheel.md)

## Guardrails

- RouterBench test split remains sealed.
- Research/experiment code is expected; production runtime integration belongs in the parent Hermes stack after qualification.
- Previously falsified/failed approaches are not recycled unchanged.
- Public/external data must be provenance-tracked and must not contaminate local validation.
- Iterative pivot work should use train-only development / the canonical pivot-holdout protocol; historical validation is reserved for finalists.
- Cost, latency, retries and end-to-end accepted mission quality matter more than router-classifier accuracy alone.
- Prefer a simple stack of independently positive components over a complicated system with unproven interactions.

## License

Apache License 2.0. See [LICENSE](LICENSE).
