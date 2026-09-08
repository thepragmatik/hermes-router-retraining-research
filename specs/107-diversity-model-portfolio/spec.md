# Feature Specification: Diversity-Optimized Model Portfolio

**Feature Branch:** `107-diversity-model-portfolio`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation

## Problem

Routing quality depends on the candidate model pool. A globally stronger model may add little if its successes duplicate a cheaper model's successes. Conversely, a modest specialist may be valuable because it uniquely repairs cases the cheap tier misses.

This feature optimizes a **small complementary model portfolio before routing**, using measured per-query outcomes and cost. The goal is not to add models; it is to select the smallest pool whose complementary coverage creates a better attainable quality/cost frontier.

This is materially different from the failed three-tier experiment because it does not assume Yi or any historical mid-tier is the right complement. It first solves the portfolio-selection problem on current/public outcome matrices, then requires downstream routing to be recalibrated on the selected pool.

## Core Objective

For model subset `S` under size/cost constraints, measure functions such as:

`F(S) = Σ_i max_{m∈S} Q_{im}`

or a budgeted utility:

`F_λ(S) = Σ_i max_{m∈S}(Q_{im} - λ C_{im})`

with penalties/constraints for latency, provider/privacy incompatibility and maintenance complexity.

The `max` oracle is a **portfolio headroom diagnostic**, not a deployable router. Selection must also report whether a simple realizable routing signal exists or whether the portfolio merely creates unreachable oracle diversity.

## User Stories

### Story 1 — Find complementary models

As a researcher, identify models that uniquely solve meaningful request mass per unit cost rather than selecting by aggregate leaderboard score.

### Story 2 — Keep the pool small

As an operator, constrain the pool to a practical size (normally 2–3 models) and quantify the marginal value of every added model.

### Story 3 — Reject unreachable diversity

As a researcher, distinguish “oracle complementarity” from complementarity a practical router can identify using available signals.

### Story 4 — Refresh as models/prices change

As an operator, rerun portfolio selection cheaply from new outcome matrices/price snapshots without redesigning the router architecture.

## Requirements

- **FR-001:** Use per-query measured outcome matrices and current price/provider metadata where possible.
- **FR-002:** Minimum controls: cheapest eligible single model, best quality single model, historical pair/pool where comparable, unconstrained/full-pool oracle diagnostic.
- **FR-003:** Compute pairwise co-failure, unique-success/rescue mass, conditional rescue, cost and latency/provider constraints.
- **FR-004:** Implement greedy cost-aware subset selection for a frozen objective and brute-force verification when candidate count is small enough.
- **FR-005:** Default max promoted pool size is 3 unless a fourth model has a program-material marginal contribution.
- **FR-006:** Model/provider eligibility filters (privacy, tool support, context, availability) apply before optimization.
- **FR-007:** Report marginal objective gain for every added model and remove redundant models.
- **FR-008:** A portfolio is not qualified solely by oracle `max` performance. It must pass a simple realizability test using V1/semantic memory/simple pairwise router or another predeclared low-complexity signal.
- **FR-009:** If 107 changes the action set, downstream 102/103/105/106 must be recalibrated; historical router thresholds cannot be reused blindly.
- **FR-010:** External/public matrices are robustness/selection evidence; exact Hermes deployment claims require compatible real outcomes.
- **FR-011:** Prices/model ids must be refreshed at execution time.
- **FR-012:** RouterBench test remains sealed.

## Selection Algorithm

### Phase A — Candidate filtering

Filter on:

- current availability;
- provider/privacy constraints;
- context/tool/structured-output requirements;
- price/latency ceilings;
- sufficient measured outcome coverage.

### Phase B — Complementarity matrix

For each pair calculate:

- success rates;
- `P(B succeeds | A fails)`;
- `P(A succeeds | B fails)`;
- co-failure;
- unique-success fraction;
- disagreement in quality, not just output string;
- incremental cost per unique rescue.

### Phase C — subset optimization

Run greedy marginal-gain selection under size or expected-cost budget. If `n<=15`, brute-force all subsets up to size 3 to verify greedy choice. For larger pools, use lazy greedy and a limited beam/control sample.

## Stage 0 — Cheapest Falsification

Use public/stored routing matrices with current-ish model pools (RoutingCompendium/LLMRouterBench where compatible) and train-only local stored matrix for historical reference.

The idea survives if a <=3 model portfolio:

- improves oracle attainable quality by >= **2pp** over the best eligible single model at <= **2x** its expected all-called cost, **or** reduces oracle cost by >= **15%** at matched quality versus a larger/reference pool;
- each added model contributes >= **0.5pp unique success/rescue** or >=5% relative cost improvement after preceding models, unless it serves a distinct required capability;
- a simple realizability test captures >= **35% of the portfolio oracle gain** without erasing its cost advantage;
- result is stable across at least two compatible datasets/task mixes or is clearly labeled domain-specific.

If oracle complementarity exists but every simple routing signal captures <35%, label `ORACLE_ONLY_PORTFOLIO` and do not expand runtime complexity.

## Expected Benefit

- may solve the problem upstream by replacing an obsolete weak/frontier pair;
- reduces routing action-space complexity;
- makes 102/103/106 easier by increasing model complementarity;
- creates a repeatable portfolio refresh process as model prices/capabilities change.

## Stackability / Exclusivity

- Upstream of 102/103/106; they must retrain/recalibrate after pool change.
- Can coexist with 109 if different models are used by stage.
- The promoted portfolio is exclusive with the historical pool for a given evaluation; compare them as alternatives, not mixed baselines.
- Greedy and brute-force are validation methods, not separate runtime components.
- Do not stack multiple redundant mid-tiers merely because each has high standalone quality.