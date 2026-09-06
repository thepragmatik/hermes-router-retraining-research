# Agent execution mission — stackable trust-and-escalation pivot

## Status

**Active mission as of 2026-09-06.**

The project operator reports that the previous experiment family (weak-correctness/FEV, one-sided judge, semantic-signal and bandit-oriented variants) **did not pass its gates**. Do not rerun those experiments unchanged. Their files remain in the repository as historical evidence.

Read first:

1. [`memo/2026-09-06_pivot-stackable-gains.md`](memo/2026-09-06_pivot-stackable-gains.md)
2. [`PIVOT_EXECUTION_PLAN.md`](PIVOT_EXECUTION_PLAN.md)
3. [`evidence/pivot-source-ledger.md`](evidence/pivot-source-ledger.md)
4. [`DATASETS.md`](DATASETS.md)
5. historical research only as needed to avoid repeating failed ideas.

## Mission objective

Your job is **not to find another single magical router classifier**.

Your job is to determine whether several small, independently useful interventions can be **stacked** into a system that reduces expensive/frontier-model use while preserving end-to-end quality.

The working architecture is:

```text
policy-safe request
      ↓
cheap model produces an answer
      ↓
trust bundle
  ├─ deterministic/test/tool checks
  ├─ internal hidden-state/logit confidence
  ├─ adaptive extra cheap sample + agreement
  ├─ task-specific verifier
  └─ OOD / calibrated abstention
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
record rescue/failure → improve cheap tier
```

For real Hermes missions, also investigate **turn/workflow-stage routing**: expensive intelligence may be valuable only at particular stages of an agent trajectory.

## Definition of done

The mission is complete only when it produces an evidence-backed economic decision about the **composed system**.

Required outcomes:

1. establish which individual layers move the quality/cost frontier;
2. quantify whether those gains actually compose or are redundant/correlated;
3. identify the simplest paying stack;
4. quantify total runtime cost, latency and frontier-call rate at matched quality;
5. quantify any refresh/fine-tuning cost;
6. test whether replacing/adding the cheap model dominates router-side improvements;
7. when Hermes mission traces exist, evaluate mission-level/stage-aware savings separately from RouterBench;
8. finish with one explicit decision:
   - **STACK WORKS — PROMOTE TO HERMES SHADOW**;
   - **PARTIAL STACK — KEEP ONLY PAYING LAYERS**;
   - **MODEL-POOL PIVOT**;
   - **AGENTIC-ONLY PIVOT**;
   - **ROUTING NOT ECONOMIC**.

A negative decision is a valid successful mission if it is supported by reproducible evidence.

## What you are expected to implement

**Research and experiment code is required.** Production integration is not.

You may and should write:

- data/audit scripts;
- model-screening harnesses;
- local generation/resampling experiments;
- hidden-state/logit extraction and tiny probes;
- verifier adapters and deterministic checks;
- cascade simulations;
- LoRA/fine-tuning experiments on train-safe failure clusters;
- cost/latency analysis and plots;
- replay/shadow analysis for Hermes trajectories;
- reproducibility tests and result tables.

Do not modify/ship production runtime code into the parent Hermes stack from this research mission.

## Hard guardrails

- **RouterBench test split remains SEALED.** Never access it.
- Use train and validation only according to the existing split discipline.
- Default paid research spend remains **$0**; any API spend requires explicit fail-closed authorization such as `SPEND_GO=1`, and total paid research spend remains **< $5** unless the project operator changes that rule.
- Remote judges/providers must preserve required ZDR behavior with no silent fallback.
- Do not rerun failed/falsified methods unchanged.
- Do not treat an external benchmark/model pair as local exact-pair truth.
- Do not promote a component because of classifier accuracy alone; measure the end-to-end cost/quality effect.
- Do not assume gains add. Measure composition and error overlap.
- Use multiple seeds where a trained probe/adapter can be seed-sensitive.
- Preserve model IDs, provider, prices, dataset revisions, hashes, commands and environment provenance.

## Core design principle — stack gains, not assumptions

Every candidate layer must pass a marginal-value test.

For each layer answer:

- What new information/action does it add that earlier layers do not?
- Which failure cases does it uniquely fix?
- Which new errors/latency/cost does it create?
- Does it move the Pareto frontier after all costs are counted?
- Does its value survive when composed with the other retained layers?

If it does not, remove it.

Prefer a simple 2–3-layer stack with real gains over a sophisticated 7-layer stack whose components overlap.

## Execution order

### P0 — model-pool audit first

Before making the router smarter, check whether the historical Mistral cheap tier is now the bottleneck.

Screen Mistral plus 2–3 current inexpensive candidates on a **train-derived/calibration sample**.

Measure:

- standalone task success;
- unique success/rescue relative to other cheap candidates;
- co-failure rate;
- token/API/local-compute cost;
- latency;
- structured output/tool compatibility where relevant.

Choose models by **complementarity per cost**, not leaderboard score or aggregate accuracy alone.

Current model prices must be looked up at execution time and recorded; do not reuse stale prices from the research memo.

### P1 — adaptive cheap resampling

On the local/cheapest viable tier, test 1/2/3/5 samples with early stopping.

Measure agreement vs correctness, incremental gain, and latency/compute. Use task-native verification where possible.

Agreement is evidence, not truth; calibrate it and inspect confident co-failures.

### P2 — internal-state answer confidence

Test whether the answering model's own hidden states/logits contain usable correctness/reliability information.

Start with lightweight frozen-state probes and compare against:

- prompt-only embedding baseline;
- log-prob/token statistics;
- hidden-state probe;
- prompt + hidden-state probe;
- task-conditioned variants.

Evaluate downstream cascade economics, not only AUROC.

### P3 — incremental trust-stack ablation

Starting from one cheap answer, add layers **one at a time**:

1. deterministic/schema/test/tool checks;
2. internal confidence probe;
3. adaptive extra cheap sample + agreement;
4. task verifier;
5. OOD/support + calibrated abstention.

For every addition record the marginal quality, frontier-call, latency and cost effect. Run pairwise ablations for overlapping layers.

### P4 — three-tier cascade

Compare:

- cheap → frontier;
- cheap → modern inexpensive mid-tier/specialist → frontier.

The middle tier survives only if the frontier spend it avoids justifies its own cost and latency.

### P5 — failure-focused cheap-tier uplift

Use recurring train-safe cases where a stronger model rescued the cheap tier as a curriculum.

Prefer stored teacher outputs/trajectories before buying new labels. Test LoRA/adapter fine-tuning with matched replay/easy examples to control regressions.

Do not attempt broad teacher imitation until targeted failure uplift has been tested.

### P6 — Hermes workflow-stage routing

When replayable/shadow Hermes traces are available, test where expensive capability actually changes accepted mission outcomes.

Candidate stage signals include:

- repeated tests/tool failures;
- no-progress/spinning behavior;
- unfamiliar/OOD tool operations;
- high-impact planning/final decisions;
- long-context synthesis;
- recovery after an error.

Compare whole-mission fixed-model strategies with stage-aware escalation. Include retries, switching/latency and total accepted-mission cost.

### P7 — draft/verify/repair, optional

Only after a useful cascade exists, test whether escalated models can reuse the cheap draft rather than regenerate from scratch.

This is optional systems research, not a prerequisite for the core pivot.

## Dataset discipline

Follow [`DATASETS.md`](DATASETS.md).

A few external datasets are useful only when used for a specific question. Do not pool data indiscriminately. Classify external data as exact-pair, transfer prior, stress test or unlabeled/OOD; deduplicate against local train/validation where applicable; preserve a local-only control.

For this pivot, external routing datasets are especially useful for **method-level robustness** of:

- model-pool complementarity;
- adaptive test-time sampling;
- performance/cost frontiers;
- cascade simulations.

They never override local or Hermes mission evidence.

## Cost accounting

For every serious candidate report separately:

- cheap-tier inference/local compute;
- additional cheap samples;
- verifier/tool calls;
- mid-tier calls;
- frontier calls;
- training/fine-tuning cost;
- latency;
- for agentic missions, retries and wasted loops where measurable.

The decision metric is **total end-to-end cost at a target quality/accepted-mission outcome**, not router accuracy.

## Required deliverables

Commit all experimental work and conclusions to this repository. At minimum:

- `results/P0_MODEL_POOL.md`
- `results/P1_CHEAP_SAMPLING.md`
- `results/P2_INTERNAL_CONFIDENCE.md`
- `results/P3_TRUST_STACK.md`
- `results/P4_THREE_TIER.md` if applicable
- `results/P5_WEAK_UPLIFT.md` if applicable
- `results/P6_AGENTIC_STAGE_ROUTING.md` when traces exist
- machine-readable per-component and composed cost/quality results;
- a decision/error-overlap log showing why layers were kept/removed;
- `PIVOT_FINAL_RECOMMENDATION.md`;
- updated README, manifest and Pages site with measured outcomes.

## What not to do

Do not center the next phase on:

- another prompt-embedding router;
- another KMeans/semantic cluster → model decision;
- a larger classifier trained on the same failed supervision;
- another generic symmetric LLM judge label set;
- blindly adding many models;
- optimizing RouterBench APGR as the sole definition of Hermes value.

Those approaches may remain baselines or tiny components only when a new hypothesis materially changes their role.

## First move

**Run P0 and P1 before training a new router.**

They answer two basic questions the previous phase did not settle:

1. is the old weak model itself now obsolete as the cheap tier?
2. can extra cheap inference provide enough new evidence/correctness to avoid some frontier calls?

Only then build P2/P3 around the best cheap tier and the actual response-aware signals it exposes.