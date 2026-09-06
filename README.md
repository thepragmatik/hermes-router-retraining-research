# Hermes Router Retraining Research

Research on **cost-effective, adaptive LLM/agent routing** for [`thepragmatik/hermes-pi-agentic-stack`](https://github.com/thepragmatik/hermes-pi-agentic-stack).

## Current status — 2026-09-06 pivot MISSION COMPLETE

**Outcome (2026-09-06): `ROUTING NOT ECONOMIC` — promotion decision E.** See **[PIVOT_FINAL_RECOMMENDATION.md](PIVOT_FINAL_RECOMMENDATION.md)** and **[MISSION_LOG.md](MISSION_LOG.md)**.

The stackable trust-and-escalation mission ran to completion across seven preregistered experiment families (P0–P6), at **$0.00 total spend** (stored responses only), with the RouterBench test split never loaded. Every deployable dynamic layer failed its frozen quality/cost gate on both the v1-anchored and the weak-first architecture. The only configuration that beats V1 — a three-tier cascade under a *perfect* correctness arbiter (+6.7pp accuracy at −39% cost, holdout-confirmed) — requires a signal this corpus cannot supply. The final operational artifact is **V1 @ threshold 0.30** (tag `router-v1-frozen`): holdout accuracy 0.6475 at $0.0025943/row.

Measured per-phase verdicts (single frozen-gate holdout passes, full detail in `results/`):

| phase | question | verdict |
|---|---|---|
| P0 | is the weak tier still the right foundation? | keep mistral-7b; Yi-34B best mid-tier (47% repair @ 4.05× cost) |
| P1 | do extra cheap samples avoid frontier calls? | disagree-escalate KILLED; oracle pair ceiling +6.7pp/−39% (not deployable) |
| P2 | can deterministic verifiers safely accept weak answers? | all 4 families FAIL precision gate (best 0.67 vs 0.90) |
| P3 | does an answer-aware confidence probe beat embedding-only routing? | all 3 arms FAIL; v1-weak rows are 95% both-models-fail |
| P4 | do killed layers pay as a stack on weak-first? | no layer survives retention; V1 ALONE IS THE STACK |
| P5 | does a mid tier justify a three-tier cascade? | oracle-only PASS (+6.7pp/−39%); no deployable arbiter exists |
| P6 | can weak-model failures be mined into uplift training? | 98.3% of v1-weak failures are both-fail; 94 minable rows; ceiling +0.38pp — FAIL |

**Revival conditions** (recorded in the final recommendation): a corpus with logprobs/hidden states, machine-checkable answer contracts, or a paid trained arbiter — under new preregs.

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
