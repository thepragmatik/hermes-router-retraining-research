# Pivot execution plan — stackable trust-and-escalation gains

**Date:** 2026-09-06  
**Status:** proposed next experimental mission after the project operator reported that the earlier router experiments did not pass.

## Objective

Stop looking for a single classifier that independently clears the routing bar. Determine whether a **sequence of small, complementary interventions** can preserve useful quality while reducing frontier-model calls and total mission cost.

The unit of progress is **marginal frontier movement**: each added layer must improve quality at matched cost, reduce cost at matched quality, or retire a material reliability risk.

## Design rule

> **Stack gains, not assumptions.**

Every layer is tested separately before it is allowed into the stack. If a layer does not improve the measured cost/quality frontier, remove it even if it is elegant or literature-supported.

Do not claim that improvements are additive before measuring the composed system: correlated errors can erase apparent individual gains.

## Proposed architecture

```text
policy-safe request
      ↓
task / verifier eligibility
      ↓
cheap model produces answer
      ↓
trust bundle
  ├─ deterministic checks
  ├─ internal confidence probe
  ├─ adaptive extra cheap sample
  ├─ answer agreement
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
record rescue → failure curriculum / weak-tier uplift
```

For Hermes agentic traffic, add a parallel track where routing decisions occur at **workflow stages/turns** rather than only at mission entry.

## Experimental order

### P0 — curated model-pool audit

**Question:** Is the historical weak model now the largest bottleneck?

Use a small train-only/calibration sample. Evaluate current Mistral plus 2–3 inexpensive candidate models. Do not touch the sealed test.

Report per candidate:

- task-family success;
- unique successes over each other candidate;
- co-failure rate;
- cost/token usage;
- latency;
- structured output/tool compatibility where relevant.

**Decision:** keep only candidates with meaningful complementarity per unit cost. Do not add models merely because they score higher in aggregate.

### P1 — adaptive cheap-sampling audit

**Question:** Can additional cheap attempts replace some frontier calls?

On local weak-model examples, obtain up to 5 fixed-seed/temperature samples (or reuse available samples). Simulate early stopping at 1/2/3/5 attempts.

Report:

- majority-vote/best-of-N quality where a verifier permits selection;
- agreement vs correctness calibration;
- fraction resolved at the second/third sample;
- latency/compute cost;
- task-specific differences.

**Decision:** retain only sampling policies that improve cost/quality after accounting for latency.

### P2 — answer-aware internal confidence

**Question:** Does the answering model know more about its own reliability than the prompt-only router can see?

Extract frozen hidden-state/logit summaries from a small set of layers. Fit only lightweight probes initially. Compare:

- prompt BGE baseline;
- token/log-probability summaries;
- frozen hidden-state probe;
- prompt + hidden-state probe;
- task-conditioned variants.

Primary outputs:

- AUROC/AUPRC for weak correctness/rescue-risk diagnosis;
- risk-coverage curve;
- downstream cost/quality when used as an abstention feature.

Do not choose a probe solely on classification metric; it must improve end-to-end routing/cascade economics.

### P3 — incremental trust-stack ablation

Start with the best cheap model producing one answer. Add one feature family at a time in frozen order:

1. deterministic/schema/task-native checks;
2. internal confidence probe;
3. adaptive additional cheap sample + agreement;
4. task-specific verifier;
5. OOD/support + calibrated abstention.

For every transition report:

- quality change;
- frontier-call change;
- total token/compute/latency change;
- marginal engineering complexity;
- failure cases uniquely fixed and newly introduced.

**Gate:** a layer survives only if it moves the Pareto frontier or materially reduces catastrophic/high-value misses without an unacceptable economic penalty.

### P4 — three-tier cascade

Compare the best two-tier stack against:

`local/ultra-cheap → modern inexpensive mid-tier → frontier`.

Use the same trust rules where possible. The mid-tier must demonstrate net economic value: the frontier calls it avoids must justify its own calls and latency.

### P5 — failure-focused cheap-model uplift

Use only train-safe recurring failure/rescue examples. Fine-tune/LoRA the weak tier on the economically important failure clusters plus a replay mix of ordinary/easy examples.

Prefer stored strong outputs/trajectories before buying any new teacher data.

Run multiple seeds. Measure:

- weak-model standalone validation gain;
- reduction in escalations under the unchanged trust stack;
- regression on previously solved/easy strata;
- training cost and refresh complexity.

Do not perform broad teacher imitation if targeted failures are enough.

### P6 — Hermes workflow-stage routing track

This is deliberately separate from historical RouterBench qualification.

Using replayable/shadow Hermes mission traces when available, measure whether expensive-model value is concentrated in particular workflow states such as:

- initial planning;
- repeated test/tool failure;
- no-progress/spinning states;
- high-impact final decisions;
- unfamiliar/OOD tool operations;
- long-context synthesis.

Compare whole-mission model selection with stage-aware escalation. Optimize accepted mission quality, retries, latency and total cost—not APGR alone.

### P7 — draft/verify/repair (optional)

Only after P4 shows a useful cascade, test whether an escalated model can consume/reuse the cheap draft rather than generating from scratch.

Measure full regeneration vs repair/enhancement on quality, tokens and latency. Treat speculative/API-level techniques as optional systems research rather than a dependency of the pivot.

## Composition discipline

A stack that contains individually positive layers can still fail because their errors are correlated. Therefore:

1. keep a frozen baseline for every stage;
2. record the marginal effect of each layer;
3. run pairwise ablations for layers with overlapping signals;
4. report the full stack and at least one simplified stack;
5. prefer the simpler stack when performance is statistically/economically indistinguishable;
6. use multiple seeds for trained probes/adapters where seed sensitivity can matter.

## Cost accounting

Separate:

- cheap-model inference/compute;
- extra sample cost;
- verifier/tool cost;
- mid-tier cost;
- frontier cost;
- training/fine-tuning refresh cost;
- latency and switching overhead.

The relevant measure is **total end-to-end cost at a target quality**, not classifier accuracy.

For agentic experiments include retries and wasted tool loops when measurable.

## Stop rules

- Do not return to prompt-only router architecture search unless a new signal/source gives a materially different hypothesis.
- Do not add a layer after two clean ablations show no frontier movement.
- Do not add a model whose successes are almost entirely duplicated by a cheaper model.
- Do not use majority agreement as correctness without calibration.
- Do not distill broad teacher behavior before testing failure-focused distillation.
- Do not let RouterBench optimization block testing of workflow-stage savings on Hermes missions.

## Required deliverables for the pivot

- `results/P0_MODEL_POOL.md`
- `results/P1_CHEAP_SAMPLING.md`
- `results/P2_INTERNAL_CONFIDENCE.md`
- `results/P3_TRUST_STACK.md`
- `results/P4_THREE_TIER.md` when applicable
- `results/P5_WEAK_UPLIFT.md` when applicable
- `results/P6_AGENTIC_STAGE_ROUTING.md` when traces exist
- machine-readable cost/quality frontier with component costs
- `PIVOT_FINAL_RECOMMENDATION.md`
- updated README/Pages with measured—not hypothesized—stack contributions

## Promotion decision

At completion choose one:

- **STACK WORKS — PROMOTE TO HERMES SHADOW:** composed system demonstrates a materially better quality/cost frontier and robustness.
- **PARTIAL STACK — KEEP ONLY PAYING LAYERS:** some interventions work but full cascade does not justify complexity; promote only independently positive components.
- **MODEL-POOL PIVOT:** replacing/adding the cheap tier dominates router-side improvements.
- **AGENTIC-ONLY PIVOT:** single-turn routing remains unattractive, but workflow-stage routing shows mission-level savings.
- **ROUTING NOT ECONOMIC:** neither routing nor cascade improvements create enough value; prefer a simpler default model/workflow strategy.

The mission succeeds by producing the correct economic decision, including a negative one.