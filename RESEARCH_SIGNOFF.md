# Research sign-off

**Date:** 2026-09-05  
**Status:** **READY FOR AGENT CONSUMPTION AND EXPERIMENTAL EXECUTION**  
**Not status:** production router approval

## Sign-off statement

The research package has completed two passes: a clean-room literature/industry review and a separate adversarial review that materially changed the recommendation. The evidence, counterarguments, remaining gaps, preregistered experiments, semantic-routing treatment, and strategic design are all preserved in this repository.

I sign off this repository as a sound basis for the **next research/experiment agent**.

I do **not** sign off Factorized Escalation Value (FEV), semantic augmentation, one-sided judge training, or bandit learning as empirically proven on this exact RouterBench split yet. Those are deliberately converted into preregistered $0 experiments so the next agent can falsify them without moving the goalposts.

## Execution mandate

`AGENTS.md` is the authoritative execution mission for the next agent.

The next agent is **expected to implement and run research/experimental code** needed to solve the routing-refresh problem: analysis scripts, training/evaluation code, ablations, cost models, and reproducibility utilities are explicitly in scope. What remains out of scope is **production integration into the parent Hermes runtime** before the experimental gates are satisfied.

The mission outcome is not another research memo. It is a measured answer to:

> **What routing refresh method preserves or exceeds v1 quality at the lowest repeatable supervision cost, and what savings does it produce?**

If no cheap method recovers v1, the agent must determine the cheapest viable ground-truth frontier and recommend whether router economics remain justified.

## What is established with high confidence

1. **The router idea has legs.** The deployed v1 already demonstrates useful routing: the open problem is cheap refresh supervision, not whether routing can ever work.
2. **The main bottleneck is supervision/feedback economics, not obviously router size.** Recent unified router evaluations and the project's own failed variants argue against spending first on a larger classifier or embedding tower.
3. **Naive prompt-cluster semantic routing should remain retired.** It is too close to the already-falsified cluster router.
4. **Semantic routing remains useful as a signal/control layer** for task/domain conditioning, measured-performance retrieval, OOD/support, calibration, and label-budget coverage.
5. **Weak correctness alone may be the wrong final objective.** Routing should care about whether strong is likely to add value, not merely whether weak fails.
6. **The failed judge contains asymmetric signal.** The reported aggregate rates algebraically imply judge `needs strong` is approximately high precision, while judge `weak sufficient` is much less reliable. Recompute from row-level labels before operational use.
7. **The sealed RouterBench test split must stay sealed.** All next decisions remain train/validation only until a preregistered gate passes.

## What remains unproven and must be tested

- how often GPT-4-1106-preview actually rescues Mistral-7B failures, globally and by task;
- whether sparse strong labels (0.5–5%) are sufficient to recover v1-level APGR;
- whether one-sided judge supervision produces useful router lift;
- whether semantic performance-memory/OOD features add measurable APGR or rescue recall;
- whether a bandit-feedback learner can approach v1 while observing only chosen-arm outcomes;
- how RouterBench qualification transfers to accepted Hermes mission quality.

These are **bounded unknowns**, not hidden assumptions. Each has a preregistered falsification path.

## Next-agent execution order

The next agent should read `AGENTS.md` and then execute in this order:

1. **Experiment 000** — train-only weak/strong outcome overlap and rescue audit. No training, $0.
2. If rescue is heterogeneous/non-universal: **Experiment 003** — sparse-label Factorized Escalation Value simulation.
3. In parallel after 000: **Experiment 004** — one-sided judge/PU ablation.
4. After the best target/label method is known: **Experiment 005** — semantic performance-memory/OOD ablation.
5. Strategic follow-up: **Experiment 006** — deployment-like bandit replay.
6. If <=5% strong labels cannot recover v1, simulate the larger strong-label cost frontier before proposing any paid labeling.

Do not spend on new judge calls or touch the sealed test split before the corresponding preregistered evidence warrants it.

## Minimum evidence package the next agent should have mounted

- pinned RouterBench-0shot data/pickle;
- hash-defined train and validation frames;
- row-level weak and strong correctness columns for retrospective train-only audits;
- stored weak responses;
- judge labels plus confidence and task identifiers;
- existing prompt embeddings or the ability to reproduce the frozen v1 embeddings;
- v1 weights/eval harness for validation APGR comparison.

If some artifacts are unavailable, execute only the experiments whose prerequisites are present and record the gap instead of substituting the sealed test split.

## Promotion rule

A research option is not promoted merely because it is elegant or well-supported in literature. It must pass the project's validation gates. The meaningful replacement baseline remains **v1 validation APGR 0.6459**; **0.55** is only viability.

## Strategic destination

The desired end state is a self-renewing routing control plane:

`policy-safe request -> semantic support -> expected escalation value -> route -> accepted outcome -> performance memory / sparse audit -> refresh`

The durable asset is the feedback-and-evidence loop, not a particular router checkpoint or model pair.
