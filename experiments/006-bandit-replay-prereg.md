# Experiment 006 preregistration: bandit replay for continual router learning

**Spend:** $0 retrospective  
**Horizon:** strategic architecture, after immediate v1-parity experiments.

## Why this matters

Offline supervised routers assume outcomes for every model on every query. Real deployment observes the outcome of the **chosen** model. That mismatch is precisely the retraining-cost problem.

Recent routing work treats model choice as contextual bandit learning:

- [PILOT, Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.1301/) learns from bandit feedback and avoids exhaustive inference across all LLMs.
- [BaRP, 2025 preprint](https://arxiv.org/abs/2510.07429) trains under the same partial-feedback restriction as deployment and allows the performance/cost preference to change at inference time without retraining.

## Retrospective simulation

Treat the train dataset as a hidden environment:

1. at each chronological/shuffled step, policy chooses weak or strong;
2. reveal only the chosen arm's stored outcome and cost;
3. update the policy using that bandit-consistent feedback;
4. maintain a small fixed exploration/sentinel probability;
5. freeze after train and evaluate the resulting policy on untouched validation using APGR.

Run 5 fixed shuffle seeds and report mean/range; selection may not depend on validation.

## Comparators

- v1 supervised baseline (recorded 0.6459 val APGR);
- random/best-single references;
- simple contextual LinUCB-style policy;
- only one policy-gradient/bandit method if implementation burden remains analysis-grade.

This is a research simulation, not production code.

## Success criteria

- val APGR >=0.60 while observing <=55% of the counterfactual outcome labels that full supervision would require;
- stretch: >=0.6459 while observing only chosen-arm feedback plus <=1% randomized dual-evaluation sentinels.

## Strategic interpretation

A pass would show a route away from periodic full-dataset retraining entirely: the router becomes an online learner fed by accepted operational outcomes and sparse unbiased exploration.
