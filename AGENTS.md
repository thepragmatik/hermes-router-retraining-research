# Agent execution mission — solve cheap, repeatable Hermes routing

## Mission objective

Your job is **not to produce another research memo**. Your job is to use the research in this repository to experimentally determine the best practical way to keep the Hermes weak/strong router effective **while making future refreshes dramatically cheaper**.

The north-star outcome is:

> **A reproducible routing-training/refresh recipe that preserves or exceeds router-v1 validation quality while minimizing the amount and cost of strong-model supervision required each time models, prices, or workloads change.**

The deployed v1 proves that routing itself can work. The unsolved problem is **cheap, repeatable supervision and refresh**.

If the proposed cheap methods cannot recover v1 quality, do not hide that result. Determine the **cheapest viable ground-truth path**, quantify its cost, and recommend whether continuing the router remains economically worthwhile.

## Definition of done

This mission is complete only when the agent produces an evidence-backed decision, not merely more analysis.

A successful outcome should achieve all of the following on the existing **validation split only**:

1. **Quality:** validation APGR >= **0.6459** (router-v1 replacement baseline). `0.55` is only a viability floor, not success.
2. **Cheap refresh:** recover that quality with the smallest possible strong-label budget. The primary research target is <= **5%** of train rows requiring strong counterfactual labels; <=2% is preferred.
3. **Economic result:** quantify future refresh cost and the routing quality/cost frontier. Show how the recommended method compares with:
   - always strong;
   - always weak;
   - deployed v1;
   - full dual-model retraining;
   - the best cheap-label candidate found in this mission.
4. **Reproducibility:** all experiment code, configs, seeds, commands, result tables, and assumptions required to reproduce the decision are committed to this repository.
5. **Decision:** explicitly recommend one of:
   - **PROMOTE TO HERMES SHADOW EVALUATION** — candidate meets the research quality/economic gates;
   - **KEEP V1 / USE CHEAPEST REFRESH FRONTIER** — no new method beats v1, but a viable refresh strategy is identified;
   - **ROUTER ECONOMICS NOT YET JUSTIFIED** — evidence says maintenance/label cost overwhelms the achievable savings or quality.

Passing this research mission does **not** itself authorize production deployment. Production promotion belongs in the parent Hermes stack after shadow evaluation on real Hermes missions.

## What you are explicitly authorized and expected to do

**You SHOULD write code for research and experiments.** The previous wording about “production code” must not be interpreted as “do not implement experiments.”

You may and should:

- write analysis scripts, training scripts, evaluation scripts, data loaders, ablations, plotting/reporting utilities, and reproducibility tests in this research repository;
- train experimental router variants locally;
- reproduce the frozen v1 validation result before comparing candidates;
- inspect and use the hash-defined **train** split and **validation** split according to each preregistration;
- use stored train labels for retrospective masking/sparse-label simulations;
- use existing weak responses, judge labels/confidence, task metadata, and embeddings;
- create new preregistered experiments when an observed result exposes a genuinely new uncertainty;
- use local CPU/MPS first and Vast GPU only when the experiment scale clearly warrants it;
- update the README, manifest, evidence, results, and Pages site as findings change.

You must **not**:

- modify or ship runtime/production routing code into `hermes-pi-agentic-stack` from this research mission;
- inspect, score, tune against, or re-evaluate the sealed RouterBench test split;
- rerun a FALSIFIED approach unchanged just to see whether it gets lucky;
- silently spend money or silently fall back to a non-ZDR judge/provider.

Research code is required. Production integration is out of scope.

## Hard guardrails

- **RouterBench test split is SEALED.** Never access it during this mission.
- **Default spend is $0.** Paid work requires an explicit fail-closed environment gate such as `SPEND_GO=1` and total research spend must remain **< $5**.
- All remote judge requests must enforce ZDR with no silent fallback.
- Normalize local paths to `~/`; publish no personal absolute home paths or credentials.
- Preserve seeds, split logic, model identifiers, and provenance for every result.
- Validation APGR **0.6459** is the meaningful replacement baseline; **0.55** is only viability.
- Do not move gates after seeing validation results. If a new experiment is needed, preregister its hypothesis, variants, metric, and decision rule first.

## Required starting inventory

Before training anything, confirm which of these are available and record paths/hashes in a mission log:

- pinned RouterBench-0shot data/pickle;
- reproducible hash-defined train/validation frames;
- row-level weak and strong correctness/outcome columns for retrospective train-only analysis;
- stored weak responses;
- judge labels and confidence;
- task/dataset identifiers;
- frozen v1 embeddings or ability to reproduce them;
- v1 router weights and evaluation harness;
- current model/provider prices if any cost projection will use live pricing.

If something is missing, continue with experiments whose prerequisites are present. Do **not** substitute the sealed test split.

## Execution plan

### Phase 0 — establish the baseline and mission ledger

1. Read `RESEARCH_SIGNOFF.md` and the ranked memo.
2. Inventory all local artifacts and record availability.
3. Reproduce **v1 validation APGR = 0.6459** using the existing validation harness. If this cannot be reproduced, stop model comparison and diagnose the evaluation pipeline first.
4. Create/update a mission ledger containing:
   - git commit;
   - data hashes/split counts;
   - environment/package versions;
   - baseline metrics;
   - spend-to-date = $0 unless explicitly authorized.

### Phase 1 — answer the most important target question at $0

Run **Experiment 000** exactly as preregistered.

Measure the train-only 2x2 weak/strong outcome table:

- both correct;
- weak wrong / strong correct = valuable rescue;
- weak correct / strong wrong = negative escalation;
- both wrong = wasted escalation.

This determines whether `weak correctness` is a sufficient target or whether the router must model the **marginal value of escalation**.

### Phase 2 — find the cheapest supervision strategy

Use the Phase-1 result to choose the branch.

**If strong almost always rescues weak failures and rescue rates are homogeneous:**

- test evaluator-first weak correctness (Experiment 001);
- compare selective hybrid fallback (Experiment 002).

**Otherwise (expected default):**

- run **Experiment 003 — Factorized Escalation Value (FEV)**;
- simulate strong-label budgets of 0.5%, 1%, 2%, and 5%;
- compare uniform sampling with targeted acquisition + random sentinel;
- report APGR versus strong-label percentage and estimated refresh cost.

In parallel after Experiment 000, run **Experiment 004** to test whether the existing judge is useful as a **one-sided high-precision signal** rather than symmetric ground truth.

### Phase 3 — test semantic routing only where it can add information

After the best target/supervision method is known, run **Experiment 005**.

Semantic routing is **not** authorized as `prompt -> cluster -> fixed weak/strong route`; that is falsified-adjacent.

Test semantics as:

- task/domain conditioning;
- kNN retrieval of **measured historical model outcomes**;
- OOD/support distance;
- calibration/risk features;
- label-acquisition coverage.

Keep semantic features only if they improve the preregistered APGR/rescue-risk gates.

### Phase 4 — test the long-term refresh architecture

Run **Experiment 006 — bandit replay** after the immediate supervised candidates are understood.

The strategic question is whether the router can learn from the outcome of the **chosen model** plus a tiny unbiased sentinel stream, instead of periodically purchasing a full counterfactual label matrix.

This is the path to a self-renewing router rather than repeated batch retraining.

### Phase 5 — if <=5% strong labels cannot recover v1

Do not declare failure prematurely and do not spend money yet.

Using the already stored retrospective train truth, preregister and simulate a **strong-label cost frontier** at larger budgets (for example 10%, 20%, 40%, 100%) to answer:

> What is the minimum amount of strong truth actually required to recover v1 quality?

Then translate that minimum label fraction into an execution-time dollar estimate using current prices.

This produces the required fallback answer: the **cheapest viable ground-truth path**.

Only after the retrospective frontier is known may a real paid label run be proposed, and it must still satisfy the mission spend cap.

## Cost accounting — mandatory

For every serious candidate, report two separate economics:

### A. Refresh / training-supervision cost

Estimate or measure:

- weak-model generation cost;
- percentage/count of strong counterfactual generations;
- judge/jury cost, if any;
- GPU cost, if any;
- total estimated cost for refreshing a 29k-row-scale training set;
- reduction versus full dual-model labeling.

### B. Runtime routing economics

On validation only, produce a cost-quality/PGR curve showing:

- fraction routed weak vs strong;
- APGR/quality proxy;
- projected inference cost relative to always strong and always weak;
- comparison with the deployed v1 operating point when comparable.

Do not optimize to a single pretty number. Preserve the Pareto frontier so Hermes can later choose its quality/cost operating point.

## Required deliverables

Commit all work to this repository. At minimum, the completed mission must contain:

- `results/EXPERIMENT_000.md` and equivalent result reports for every experiment actually run;
- machine-readable result table(s) with seeds, metrics, label budgets, and costs;
- reproducible research/experiment code and commands;
- `COST_MODEL.md` with refresh-cost and runtime-cost comparisons;
- `FINAL_RECOMMENDATION.md` containing:
  - the winning approach;
  - measured validation metrics;
  - required strong-label fraction;
  - estimated refresh cost;
  - runtime economics;
  - risks/limitations;
  - explicit promotion decision;
- updated `research-manifest.json`;
- updated README and GitHub Pages site summarizing the experimentally validated outcome;
- a decision log explaining why candidates were promoted, rejected, or deferred.

If the winning experiment produces a small research checkpoint, record its path/hash and reproduction command. Do not silently make that checkpoint a production artifact.

## Research discipline

Use the existing literature and adversarial review as **priors**, not as substitutes for local evidence.

Do additional web research only when an experiment exposes a specific uncertainty that could change the next decision. The project is now in an **evidence-generation phase**, not another broad literature phase.

Prefer the simplest method that passes the gates. A sophisticated model that matches a simpler method loses on maintenance cost unless it creates a clear quality or label-efficiency advantage.

## Read order

0. [`RESEARCH_SIGNOFF.md`](RESEARCH_SIGNOFF.md)
1. [`memo/2026-09-05_ranked-options-memo.md`](memo/2026-09-05_ranked-options-memo.md)
2. [`evidence/adversarial-review.md`](evidence/adversarial-review.md)
3. [`designs/router-learning-flywheel.md`](designs/router-learning-flywheel.md)
4. [`evidence/semantic-routing-review.md`](evidence/semantic-routing-review.md)
5. experiment preregistrations `000`, `001`, `002`, `003`, `004`, `005`, `006`
6. [`evidence/source-ledger.md`](evidence/source-ledger.md)

## Current recommended first move

**Run Experiment 000 now.**

It costs $0, requires no model training, and tells us whether the next router should predict weak failure or the more economically correct quantity: **strong model rescue / marginal escalation value**.

Then execute the branch above until the mission produces a validated quality/cost answer.
