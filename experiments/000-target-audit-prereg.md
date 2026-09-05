# Experiment 000 preregistration: target sufficiency / rescue audit

**Spend:** $0  
**Purpose:** retire the biggest conceptual risk before training another router.

## Question

Is `weak correctness` a sufficient proxy for the actual routing target, or do we need to model the **marginal value of strong escalation**?

Weak correctness is insufficient when a meaningful fraction of weak failures are also strong failures, or when `P(strong succeeds | weak fails, x)` varies substantially across task/semantic strata.

## Data and leakage rules

- Use only the hash-defined **train split** for this audit.
- Existing strong/weak correctness columns may be read because this is a retrospective scientific audit, not a new label-acquisition method.
- Do not inspect or evaluate the sealed test split.
- Validation is not needed unless the audit leads to a model experiment.

## Frozen calculations

For each train row, assign one of four states:

1. weak correct / strong correct;
2. weak wrong / strong correct = **rescuable escalation**;
3. weak correct / strong wrong = **negative escalation**;
4. weak wrong / strong wrong = **non-rescuable weak failure**.

Report globally and by task family:

- `P(weak wrong)`;
- `P(strong correct | weak wrong)`;
- `P(strong wrong | weak correct)`;
- fraction of all strong calls that could create positive quality gain;
- rescue-rate variation across task families;
- if scores are continuous, expected `max(score_strong - score_weak, 0)` and signed difference.

## Decision rules

- If `P(strong correct | weak wrong) >= 0.95` **and** task-family rescue rates are tightly concentrated (max-min <= 0.10 after excluding tiny strata), weak correctness is an acceptable primary target for Experiment 001.
- Otherwise, elevate **Factorized Escalation Value (FEV)** to the primary target and run Experiment 003.
- If negative escalation (`weak correct / strong wrong`) is non-trivial (>2%), the production decision must optimize expected marginal gain rather than a one-sided “difficulty” score.

These thresholds are engineering heuristics, not literature-derived constants; they are frozen before observing the audit.

## Why this experiment is first

RouteLMT formalizes a closely related insight: hybrid routing should target the **large model's marginal gain over the small model**, not absolute difficulty or absolute quality. See [Luo et al., 2026](https://arxiv.org/abs/2604.22520).

This audit can therefore falsify the first memo's weak-correctness simplification with no retraining and no spend.
