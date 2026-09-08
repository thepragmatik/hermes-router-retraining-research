# AGENTS.md — execution entrypoint

## Active mission

This repository is in the **stackable trust-and-escalation pivot** phase.

The previous router experiment family did not pass its gates. Do not rerun failed weak-correctness/FEV, symmetric-judge, semantic-cluster, or related approaches unchanged.

### Canonical source of truth

**Execute [`STACKABLE_ROUTING_MISSION.md`](STACKABLE_ROUTING_MISSION.md) to completion.**

That file defines the objective, data controls, experiment sequence, cost/quality gates, stackability rules, stop rules, deliverables, and final promotion decisions. If this file and another historical document disagree, the canonical mission wins unless the project operator explicitly changes it.

For a ready-to-paste launch instruction, see [`LAUNCH_AGENT_PROMPT.md`](LAUNCH_AGENT_PROMPT.md).

## Read order

1. [`STACKABLE_ROUTING_MISSION.md`](STACKABLE_ROUTING_MISSION.md)
2. [`memo/2026-09-06_pivot-stackable-gains.md`](memo/2026-09-06_pivot-stackable-gains.md)
3. [`evidence/pivot-source-ledger.md`](evidence/pivot-source-ledger.md)
4. [`DATASETS.md`](DATASETS.md)
5. historical memos/experiments only as needed to avoid repeating failed work

## Mission premise

Do **not** ask one prompt-only classifier to predict the whole routing decision before useful evidence exists.

Instead:

1. use the best economical cheap tier;
2. let it produce an answer;
3. gather cheap answer-aware evidence;
4. stack only evidence/interventions that add independent value;
5. use a mid-tier/specialist when it pays;
6. escalate to frontier only for unresolved cases;
7. convert recurring frontier rescues into cheap-tier capability where possible;
8. for Hermes agents, test whether strong intelligence is needed only at particular workflow stages.

The unit of progress is **marginal end-to-end quality/cost improvement**, not router classifier accuracy.

## Current frontier reference — Astra

This research conversation itself is running on **GPT-5.6 Sol**, not GPT-6 Astra.

As of **2026-09-08**, OpenAI's latest released frontier model is **GPT-6 Astra**. The execution agent must therefore treat Astra as the **current OpenAI frontier reference** when it is available through the connected provider/API and is compatible with the mission's privacy, spend, and access constraints.

Important distinctions:

- do **not** assume the historical `gpt-4-1106-preview` strong-model labels describe Astra; those remain historical exact-pair evidence only;
- for P0/P5 and cost-frontier work, verify the current Astra model ID, availability, provider, latency, and price at execution time before using it;
- Astra is primarily a **frontier comparator / escalation target**, not a cheap-tier candidate;
- if Astra access is unavailable or incompatible with ZDR/spend constraints, use the strongest currently available compliant frontier model and record the substitution explicitly;
- do not hard-code today's frontier forever: the mission must refresh the frontier reference at execution time because frontier models and prices change.

The strategic question is not “can we route to Astra cheaply?” It is “how rarely can we need frontier-class intelligence, while preserving end-to-end quality?”

## Research code is required

You are expected to implement and run research/experiment code: audits, generation/resampling, verifiers, hidden-state/logit probes, cascade simulations, cost models, targeted fine-tuning, agent-trace replay, tables, plots, and reproducibility checks.

Production integration into `thepragmatik/hermes-pi-agentic-stack` is **not** part of this research mission. A winning design may be recommended for controlled shadow evaluation.

## Non-negotiables

- RouterBench **test remains SEALED**. Never access it.
- Use train-only development / the pivot-holdout protocol for iterative experimentation; reserve historical validation for finalists as specified in the canonical mission.
- Default paid spend is **$0**. Paid work is fail-closed behind the explicit spend gate and remains under the mission cap unless the operator changes it.
- Preserve required ZDR/provider behavior with no silent fallback.
- Do not treat external datasets/model pairs as local exact-pair truth; follow `DATASETS.md`.
- Do not assume gains add. Measure composition and error overlap.
- Do not keep a layer because it is elegant or literature-supported; keep it only if it moves the measured frontier or retires a material risk.
- Prefer a simple paying stack over a complex redundant one.
- Record model IDs, provider, current prices, seeds, data hashes/revisions, commands, environment, spend, latency, and validation exposures.
- Do not stop at a new memo. The mission requires experiments, results, economics, repository artifacts, and a final decision.

## First actions

1. Create `MISSION_LOG.md` and the machine-readable cost/frontier/error-overlap ledgers required by the canonical mission.
2. Inventory mounted artifacts and freeze the development/qualification protocol.
3. Refresh current model/provider prices and constraints, including the current OpenAI frontier reference (GPT-6 Astra as of 2026-09-08 if accessible).
4. Reproduce available baselines.
5. Run **P0 — model-pool audit**.
6. Run **P1 — adaptive cheap inference** and **P2 — deterministic verification** before training another router/probe.
7. Proceed through the mission gates until a final economic decision is reached.

## Final decision

At completion choose exactly one primary outcome from the canonical mission:

- **STACK WORKS — PROMOTE TO HERMES SHADOW**
- **PARTIAL STACK — KEEP ONLY PAYING LAYERS**
- **MODEL-POOL PIVOT**
- **AGENTIC-ONLY PIVOT**
- **ROUTING NOT ECONOMIC**

A negative result is a successful mission if it is reproducible and shows that a simpler strategy is economically better.
