# Canonical execution mission — Stackable Trust, Escalation, and Agentic Routing

**Status:** ACTIVE  
**Date:** 2026-09-06  
**Repository:** `thepragmatik/hermes-router-retraining-research`  
**Parent:** `thepragmatik/hermes-pi-agentic-stack`

## 1. Mission in one sentence

Build and experimentally qualify the **simplest stack of independently useful interventions** that reduces expensive/frontier-model use and total end-to-end cost while preserving useful answer/mission quality — without relying on another single prompt-only router classifier.

The mission is successful when it produces a reproducible economic decision, including a negative one.

---

## 2. Why this mission exists

The previous router-retraining phase explored weak-correctness/FEV labels, judge-derived supervision, semantic signals, and bandit-style approaches. The project operator reports that those experiments did not pass their gates.

Treat that as evidence, not as a temporary inconvenience.

The pivot is based on a different premise:

> **Do not require one model to predict the entire routing decision before useful evidence exists. Let cheap computation create evidence, then escalate only as needed.**

The new unit of progress is not “router accuracy.” It is **marginal movement of the end-to-end quality/cost frontier**.

A 3–5% improvement can be valuable if it is cheap, robust, and complementary to other improvements. Several such gains may compose into a useful system. They may also overlap and fail to compose; that must be measured rather than assumed.

---

## 3. Strategic architecture under test

```text
policy-safe request
      │
      ▼
cheap / local model produces an answer
      │
      ▼
answer-aware trust bundle
      ├── deterministic schema / test / tool checks
      ├── calibrated logit / hidden-state confidence
      ├── adaptive second/third cheap sample
      ├── agreement / disagreement evidence
      ├── task-specific verifier or external tool
      └── OOD / support / abstention signal
      │
      ▼
trust sufficient?
   ┌──┴──┐
 yes     no
  │       │
return    ▼
       cheap-capable mid-tier / specialist
              │
              ▼
         trust sufficient?
           ┌──┴──┐
          yes     no
           │       │
        return     ▼
                frontier
                   │
                   ▼
       record rescue / miss / cost / latency
                   │
                   ▼
        failure-focused cheap-tier uplift
```

For Hermes agent missions, add a second routing dimension:

```text
mission state / workflow stage
      │
      ├── routine read / transform / tool call → cheap
      ├── uncertain planning / synthesis          → conditional
      ├── repeated failure / no progress          → escalate
      └── high-impact final decision              → strong when justified
```

The ultimate design may be a cascade, a curated model pool, stage-aware escalation, targeted fine-tuning, or a small combination of these. Do not force the final system to look like the diagram if evidence points elsewhere.

---

## 4. North-star objective

Optimize **total accepted-work cost**, not classifier metrics.

For RouterBench-style experiments, preserve the historical v1 reference:

- v1 validation APGR: **0.6459**
- 0.55 remains only a viability floor for historical comparison
- RouterBench test split remains **SEALED**

For Hermes mission traces, the primary outcome is **accepted mission quality/success at total mission cost**, including retries and wasted loops.

### Primary decision metrics

Every serious candidate or stack must report:

1. answer/mission quality;
2. total runtime model cost;
3. frontier-call rate;
4. mid-tier-call rate;
5. extra cheap-sample count/cost;
6. verifier/tool cost;
7. p50/p95 latency where measurable;
8. retry/no-progress cost for agentic traces where measurable;
9. refresh/training/fine-tuning cost;
10. high-value/catastrophic miss rate where the task supports such a classification.

### Materiality defaults

These are **mission-design thresholds**, not claims from literature. They exist to prevent endless pursuit of tiny noisy improvements.

A layer is considered economically meaningful when, after uncertainty/noise checks, it achieves at least one of:

- **>=5% relative total runtime-cost reduction** at matched quality;
- **>=5 percentage-point absolute frontier-call reduction** at matched quality with no meaningful latency regression;
- **>=1 percentage-point absolute quality improvement** at approximately matched cost;
- a material reduction in high-value/catastrophic misses that justifies its added cost.

A composed stack is a serious **Hermes shadow candidate** when it shows a robust Pareto improvement and preferably achieves one of:

- **>=10% relative total runtime-cost reduction** versus the strongest comparable existing baseline at matched quality; or
- materially higher quality at no higher total cost; or
- a clearly better accepted-mission cost frontier on Hermes traces.

If the evidence shows a smaller but strategically useful gain, classify it as **PARTIAL STACK** rather than stretching the promotion gate.

---

## 5. Non-goals

Do **not** center this mission on:

- another prompt-embedding-only router;
- another semantic/KMeans cluster → fixed model mapping;
- a larger classifier trained on essentially the same failed supervision;
- another generic symmetric LLM judge label set;
- adding many models without measuring complementarity;
- maximizing RouterBench APGR while ignoring runtime economics;
- broad teacher distillation before targeted failure uplift is tested;
- production integration into the parent Hermes runtime.

Historical failed methods remain useful as baselines and negative evidence. Do not rerun them unchanged.

---

## 6. Authorization and implementation scope

**Research/experiment code is expected and required.**

The agent may write and commit:

- data inventory and audit scripts;
- model-screening harnesses;
- generation/resampling harnesses;
- hidden-state/logit extraction;
- tiny probes/calibrators;
- deterministic verifier adapters;
- cascade simulators;
- cost/latency models;
- LoRA/QLoRA or equivalent targeted fine-tuning experiments;
- agent-trace replay analysis;
- plots/tables/site updates;
- reproducibility tests.

Do not ship production runtime routing code into `hermes-pi-agentic-stack` from this mission. A winning research design may be recommended for **shadow evaluation**, not silently deployed.

---

## 7. Hard guardrails

### Data / evaluation

- RouterBench **test is sealed**. Never inspect it, deduplicate against it, score it, or use it indirectly.
- Preserve the existing train/validation split and provenance.
- Because the historical validation set has already been consulted by multiple prior experiments, create a **pivot-development protocol**:
  - use train-only cross-validation or a deterministic train-derived pivot holdout for iterative experiments;
  - reserve the existing validation set for finalists and milestone qualification, not constant tuning;
  - record every validation exposure in the mission ledger.
- Do not move thresholds after seeing qualification results. New hypotheses require preregistration before another qualification exposure.

### Spend

- Default paid spend: **$0**.
- Any paid API experiment must fail closed unless an explicit spend gate such as `SPEND_GO=1` is present.
- Existing mission cap remains **< $5 total paid research spend** unless the operator explicitly changes it.
- Prefer stored outputs, local inference, existing labels, and public pre-collected datasets before buying inference.
- Record actual or estimated per-experiment spend.

### Privacy/provider behavior

- Remote judge/provider calls must preserve required ZDR behavior with no silent fallback.
- Never publish credentials, personal absolute paths, or private identifiers.

### Experimental integrity

- Preserve model IDs, model revisions where available, providers, prices, parameters, seeds, dataset revisions, hashes, commands, and environment versions.
- Use multiple seeds for trained probes/adapters when seed sensitivity is plausible.
- Do not select a component solely on classifier AUROC/F1. It must improve downstream cost/quality or retire a material safety/reliability risk.
- Do not assume individual gains add. Measure composition and error overlap explicitly.

---

## 8. Data and dataset policy

Read `DATASETS.md` before using public data.

Core principle:

> **A few datasets are genuinely useful, but only if the mission is disciplined about how they are used.**

Classify each external dataset as one of:

- `exact_pair`
- `transfer_prior`
- `stress_test`
- `unlabeled_ood`

External data is an **evidence amplifier**, not a substitute for exact-pair or Hermes mission evidence.

For this pivot, public datasets are most useful for:

- model-pool complementarity stress tests;
- adaptive-sampling experiments;
- many-model cost/quality frontiers;
- cascade simulations;
- OOD and distribution-coverage checks.

Preserve a local-only control whenever external data influences training or thresholds.

---

## 9. Mission ledger — create this first

Create `MISSION_LOG.md` before running experiments.

It must track:

- current git SHA;
- mission start date/time;
- operator-reported historical failures;
- mounted local artifacts and hashes;
- train/pivot-holdout/validation counts;
- every validation exposure;
- model/provider/version inventory;
- current price snapshot source/date;
- environment/package versions;
- spend-to-date;
- active hypotheses;
- decisions and stop reasons.

Also create machine-readable ledgers:

- `results/frontier.csv` — one row per evaluated policy/stack operating point;
- `results/component_effects.csv` — marginal effect of each layer;
- `results/error_overlap.csv` — overlap/correlation between component failure sets;
- `costs/model_prices.json` — execution-time model prices and source timestamps.

---

# 10. Experimental program

## P0 — baseline and model-pool audit

### Question

Is the historical weak tier still the right foundation, or is model choice now a larger lever than routing sophistication?

### Required baselines

On train-derived development data, establish:

- always weak;
- always strong/frontier where stored labels permit simulation;
- historical router v1 where reproducible;
- one-answer cheap model;
- simple cheap→frontier cascade with no learned trust layer.

### Candidate screening

Screen the historical cheap model plus **2–3 current inexpensive candidates**. Prefer models that can be tested from stored/public results or at negligible cost before paid calls.

Measure:

- aggregate quality;
- per-task quality;
- unique successes;
- pairwise co-failure;
- rescue of historical weak failures;
- structured-output/tool reliability when relevant;
- latency;
- cost;
- privacy/provider suitability.

### Selection rule

Choose models by **complementarity per unit cost**, not leaderboard score alone.

A more accurate model that duplicates every success/failure of a cheaper model may add little routing value.

### Deliverable

`results/P0_MODEL_POOL.md`

### Decision

- If a new cheap model dominates the historical weak model, make it the primary cheap tier for later phases while preserving the old model as a comparison.
- If two cheap models are complementary and jointly economical, carry both into P1/P4.
- If no cheap candidate improves the frontier, keep the current cheap tier and proceed.

---

## P1 — adaptive cheap inference / resampling

### Question

Can extra cheap inference replace some frontier calls?

### Variants

Test 1, 2, 3, and 5 cheap samples where compute permits.

Compare:

- fixed-N self-consistency;
- early stopping on agreement;
- early stopping on deterministic verifier success;
- disagreement-triggered escalation;
- optional heterogeneous pair: two different cheap models instead of two samples from one model.

### Measure

- quality vs N;
- probability that an additional sample repairs the first answer;
- probability of confident co-failure;
- agreement→correctness calibration;
- incremental tokens/compute/latency;
- task-family heterogeneity;
- frontier calls avoided in a simulated cascade.

### Rule

Agreement is evidence, **not truth**. Inspect cases where cheap samples confidently agree and are wrong.

### Deliverable

`results/P1_CHEAP_SAMPLING.md`

### Keep gate

Retain only sampling policies that move the end-to-end frontier after their own latency/compute cost is counted.

---

## P2 — deterministic and tool-grounded verification

### Question

Which weak answers can be accepted or rejected using near-free objective evidence?

### Candidate verifier families

Use only where task semantics make them valid:

- exact/reference match;
- schema/JSON validation;
- unit tests;
- Python/calculator recomputation;
- compiler/type/lint checks;
- tool execution success/failure;
- retrieval/source consistency checks;
- constraint satisfaction;
- task-specific deterministic graders.

### Measure

For each verifier:

- coverage;
- precision of “safe to accept” decisions;
- false-accept rate;
- false-reject rate;
- incremental latency/cost;
- frontier calls avoided.

### Rule

A verifier may abstain. Prefer **high-precision partial coverage** over a broad but unreliable pseudo-judge.

### Deliverable

`results/P2_VERIFIERS.md`

---

## P3 — answer-aware internal confidence

### Question

Does the cheap model contain useful reliability information after answering that the prompt-only router could not see?

### Features

Start lightweight:

- token log-probability summaries where available;
- entropy/margin statistics;
- answer length/termination features;
- frozen hidden states from a small number of layers/tokens;
- prompt embedding + hidden-state combination;
- task-conditioned calibrators.

### Baselines

Compare against:

- prompt-only BGE baseline;
- simple log-prob threshold;
- hidden-state-only probe;
- prompt+hidden-state probe;
- task-conditioned variants.

### Metrics

Report AUROC/AUPRC/risk-coverage for diagnosis, but select by:

- cascade quality/cost;
- selective-risk curve;
- frontier-call reduction;
- false-accept behavior;
- task-specific stability.

### Important adversarial rule

Do not assume internal confidence generalizes equally across factual, mathematical, coding, and open-ended tasks. Keep task-conditioned analyses and drop the signal where it is not useful.

### Deliverable

`results/P3_INTERNAL_CONFIDENCE.md`

---

## P4 — stack construction by incremental ablation

### Question

Which combination of answer-aware signals actually pays when composed?

### Frozen build order

Start from the best P0 cheap tier and add, one at a time:

1. deterministic verifier(s);
2. adaptive extra cheap sample/disagreement;
3. internal confidence signal;
4. OOD/support/abstention;
5. task-specific verifier or specialist check not already covered.

If evidence from P1–P3 supports a different order, preregister the revised order before qualification.

### For every layer report

- marginal quality delta;
- marginal total-cost delta;
- marginal frontier-call delta;
- latency delta;
- cases uniquely fixed;
- cases newly broken;
- failure overlap with already-retained layers;
- engineering/maintenance complexity.

### Composition tests

- full stack;
- leave-one-out ablation;
- pairwise ablation for overlapping signals;
- simplified stack with the weakest/most complex layer removed.

### Complexity rule

Prefer **2–3 paying dynamic layers** over a 6–7-layer system whose incremental gains are tiny.

A fourth or later dynamic layer should normally provide a clearly material gain or retire a high-value risk; otherwise remove it.

### Deliverable

`results/P4_TRUST_STACK.md`

---

## P5 — three-tier / specialist cascade

### Question

Is the gap between “cheap” and “frontier” unnecessarily large?

Compare:

- cheap → frontier;
- cheap → inexpensive mid-tier → frontier;
- cheap → task specialist → frontier, where a specialist is justified.

### Mid-tier selection

Use P0 complementarity logic. Do not pick a mid-tier solely because it is globally stronger.

### Measure

- mid-tier resolution rate;
- frontier calls avoided;
- incremental mid-tier spend;
- total cost at matched quality;
- latency/switching cost;
- task-specific value.

### Keep gate

The middle tier survives only if its own spend/latency is more than justified by avoided frontier cost or improved quality.

### Deliverable

`results/P5_THREE_TIER.md`

---

## P6 — failure-focused cheap-tier uplift

### Question

Can repeated expensive rescues be converted into permanent cheap-model capability?

### Curriculum construction

Mine **train-safe** recurring cases where:

- cheap fails;
- stronger model or verifier resolves the case;
- the failure pattern repeats enough to matter economically.

Use semantics for **failure clustering/analysis**, not direct routing.

### Training

Prefer:

- stored strong outputs/trajectories;
- targeted LoRA/QLoRA/adapters;
- replay mixture of previously easy/solved examples;
- multiple seeds;
- small controlled data volumes.

### Measure

- standalone cheap-tier quality change;
- reduction in escalations under the **unchanged** trust stack;
- regression on easy/previously solved tasks;
- training cost;
- refresh complexity;
- whether the uplift makes any trust layer unnecessary.

### Rule

Do not broad-distill the frontier model until targeted failure uplift has shown whether narrow repair is sufficient.

### Deliverable

`results/P6_WEAK_UPLIFT.md`

---

## P7 — Hermes workflow-stage routing

### Question

For an agent, is expensive intelligence valuable only at particular points in a mission?

This track is strategically important even if single-turn RouterBench routing remains mediocre.

### Prerequisite

Replayable or shadow Hermes mission traces with enough state/outcome data to compare decisions.

### Candidate escalation signals

- initial high-level planning;
- repeated tool/test failure;
- no-progress/spinning state;
- unfamiliar/OOD tool use;
- long-context synthesis;
- security/high-impact decision point;
- recovery after an error;
- final answer/commit review where consequences are high.

### Baselines

Compare:

- all-frontier mission;
- all-cheap mission;
- fixed model chosen at mission start;
- stage-aware escalation;
- simple heuristic stage rules before learned stage routing.

### Measure

- accepted mission success/quality;
- total model spend;
- total tokens;
- wall-clock latency;
- retries;
- wasted tool loops;
- strong calls by stage;
- rescue contribution of each strong call.

### Key rule

Optimize **accepted mission cost**, not RouterBench APGR.

### Deliverable

`results/P7_AGENTIC_STAGE_ROUTING.md`

If traces are unavailable, document the prerequisite gap and do not fabricate proxy results.

---

## P8 — draft / verify / repair reuse (optional)

### Question

When escalation is necessary, can the strong model repair the cheap draft rather than regenerate from scratch?

Compare:

- strong from scratch;
- strong with cheap draft as context;
- strong instructed to verify/repair only identified weak points;
- task-specific patching where feasible.

Measure tokens, latency, quality, and whether weak-draft anchoring introduces errors.

Only run after P4/P5 identifies a useful cascade. This is optional systems optimization, not a prerequisite for the core mission.

### Deliverable

`results/P8_DRAFT_REPAIR.md`

---

# 11. Innovation sandbox

The agent is encouraged to pursue **at most two** genuinely new side bets during the mission when evidence exposes a promising gap.

Examples:

- heterogeneous cheap-model disagreement instead of repeated sampling;
- specialist tool/model selection;
- retrieval/tool intervention before model escalation;
- “escalate the method, not the model” policies;
- cached performance memory for recurring task patterns;
- selective strong review of only critical answer spans/decisions.

Before running an innovation experiment, create a short preregistration containing:

- hypothesis;
- why it is materially different from failed work;
- expected cost;
- metric;
- keep/kill gate;
- maximum effort/spend.

Do not let the sandbox derail P0–P5.

---

# 12. Experimental statistics and uncertainty

For every finalist:

- report sample counts and task strata;
- use bootstrap confidence intervals or another appropriate uncertainty estimate for key cost/quality deltas;
- report multiple seeds for learned components;
- record threshold-selection procedure;
- report both aggregate and task-family results;
- inspect error-overlap, not only averages;
- flag results that are likely within noise.

Do not describe a small numerical improvement as real if uncertainty makes the direction unclear.

---

# 13. Cost accounting rules

Keep **refresh/training cost** separate from **runtime cost**.

Runtime accounting should include:

- cheap inference;
- extra cheap samples;
- verifier/tool calls;
- mid-tier calls;
- frontier calls;
- switching/serialization overhead where measurable;
- for agents, retries/no-progress loops.

Refresh accounting should include:

- new labels/model calls;
- training/fine-tuning compute;
- embedding/index refresh;
- dataset preprocessing when material;
- judge or evaluator calls.

Never call a public dataset or local model “free” if its compute/storage/refresh overhead materially affects the practical design.

---

# 14. Stop / kill rules

Kill a layer when:

- two clean ablations show no meaningful frontier movement;
- its gain disappears after composing with a cheaper/simpler layer;
- its false-accept risk is unacceptable;
- it adds more latency/cost than the frontier spend it avoids;
- it is highly unstable across seeds/tasks without a reliable gating condition.

Kill a model candidate when:

- its successes are overwhelmingly duplicated by a cheaper model;
- it is expensive/slow enough that direct frontier use dominates;
- provider/privacy constraints make it operationally unsuitable.

Stop the broader routing effort and recommend simplification when:

- no stack, model-pool change, or agentic-stage policy produces a material Pareto improvement;
- the maintenance/refresh burden consumes the savings;
- a single modern inexpensive model produces a better operational tradeoff than routing.

A negative conclusion is a valid mission success.

---

# 15. Promotion decisions

At mission completion choose exactly one primary outcome:

### A. `STACK WORKS — PROMOTE TO HERMES SHADOW`

A composed stack shows robust, material cost/quality improvement and is ready for controlled shadow integration in the parent stack.

### B. `PARTIAL STACK — KEEP ONLY PAYING LAYERS`

One or more components independently help, but the full cascade does not justify its complexity.

### C. `MODEL-POOL PIVOT`

Replacing/adding the cheap or mid-tier model dominates router-side innovation.

### D. `AGENTIC-ONLY PIVOT`

Single-turn routing remains unattractive, but stage-aware mission routing shows useful mission-level savings.

### E. `ROUTING NOT ECONOMIC`

No routing/cascade architecture produces enough value. Recommend the simplest fixed-model/workflow strategy supported by evidence.

Do not create a sixth ambiguous “needs more research” outcome unless a specific unavailable prerequisite blocks a decisive experiment; if so, state the exact missing prerequisite and the smallest experiment that would resolve it.

---

# 16. Required repository deliverables

The mission is not complete until the repository contains, as applicable:

- `MISSION_LOG.md`
- `results/frontier.csv`
- `results/component_effects.csv`
- `results/error_overlap.csv`
- `costs/model_prices.json`
- `results/P0_MODEL_POOL.md`
- `results/P1_CHEAP_SAMPLING.md`
- `results/P2_VERIFIERS.md`
- `results/P3_INTERNAL_CONFIDENCE.md`
- `results/P4_TRUST_STACK.md`
- `results/P5_THREE_TIER.md`
- `results/P6_WEAK_UPLIFT.md`
- `results/P7_AGENTIC_STAGE_ROUTING.md` when traces exist
- `results/P8_DRAFT_REPAIR.md` if run
- preregistrations for any innovation-sandbox experiments
- reproducible research code/configs/commands
- `PIVOT_FINAL_RECOMMENDATION.md`
- updated `research-manifest.json`
- updated README
- updated GitHub Pages summary of **measured** outcomes

`PIVOT_FINAL_RECOMMENDATION.md` must include:

1. direct decision;
2. winning stack/model pool;
3. exact retained layers;
4. quality metrics;
5. total runtime economics;
6. frontier-call reduction;
7. latency impact;
8. refresh/training economics;
9. component marginal contributions;
10. important failure modes;
11. external robustness evidence if used;
12. Hermes-stage evidence if available;
13. what was killed and why;
14. explicit next action for the parent Hermes stack.

---

# 17. Execution order and parallelism

Mandatory order:

1. **Mission ledger / data controls**
2. **P0 model-pool audit**
3. **P1 adaptive cheap inference** and **P2 deterministic verifiers** — may run in parallel after P0
4. **P3 internal confidence** — after the primary cheap tier is selected
5. **P4 trust-stack composition** — only after P1–P3 evidence exists
6. **P5 three-tier cascade**
7. **P6 failure-focused uplift** if recurring expensive rescues justify it
8. **P7 Hermes stage routing** when traces are available; this may run in parallel with P4–P6 because it answers a different strategic question
9. **P8 draft/repair** only if a useful cascade already exists

Do not start by training a new router.

---

# 18. First concrete actions

The next agent should begin by:

1. reading this file, `AGENTS.md`, the pivot memo, and `DATASETS.md`;
2. creating `MISSION_LOG.md` and the machine-readable result ledgers;
3. inventorying local data/artifacts and confirming the sealed-test boundary;
4. freezing the pivot development/qualification protocol;
5. refreshing current candidate-model prices/provider constraints;
6. reproducing available baseline metrics;
7. running **P0**;
8. running **P1 and P2** before fitting any new router/probe.

The key early questions are deliberately simple:

- Is the historical cheap model now obsolete?
- Does one extra cheap attempt solve enough problems to matter?
- Can objective verification safely accept a useful subset of weak answers?

Only after those are answered should the mission spend engineering effort on learned trust models.

---

## Final principle

> **Do not ask one cheap classifier to predict the future. Spend a little cheap computation to create evidence, stack only the evidence sources that pay, and reserve expensive intelligence for the cases that remain unresolved.**
