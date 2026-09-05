# Design proposal: Hermes Value Router Learning Flywheel

**Status:** research design; not production code.  
**Goal:** make model routing self-renewing as models, prices and workloads change.

## Core idea

The router should not be trained to answer “which model won this one historical draw?” It should answer:

> **What is the expected incremental mission value of paying for the strong model on this request, after policy and privacy constraints?**

That gives a stable economic abstraction even when model identities and prices change.

## Architecture

```text
                    ┌─────────────────────────────┐
request ───────────▶│ Tier 0 deterministic policy │
                    │ privacy · authz · capability│
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │ Tier 1 semantic signal plane│
                    │ domain · complexity · OOD   │
                    │ structure · local neighbors │
                    └──────────────┬──────────────┘
                                   ▼
             ┌─────────────────────────────────────────┐
             │ Tier 2 Factorized Escalation Value     │
             │ p_fail_weak × expected_strong_rescue   │
             │      − incremental_cost × λ            │
             └───────────────────┬─────────────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │ Tier 3 risk / abstain guard │
                    │ low support · drift · jury  │
                    └──────────────┬──────────────┘
                          weak ◀───┴───▶ strong
                            │               │
                            └───────┬───────┘
                                    ▼
                    ┌─────────────────────────────┐
                    │ outcome / acceptance signals│
                    │ tests · verifier · retry    │
                    │ user acceptance · audits    │
                    └──────────────┬──────────────┘
                                   ▼
                    performance memory + bandit update
                         + sparse randomized sentinel
```

## Label hierarchy

Prefer the cheapest trustworthy signal available:

1. **deterministic mission/task verifier** — tests, exact answer, schema constraints, tool execution result;
2. **weak-answer correctness** where an evaluator exists;
3. **high-precision judge positive** (`ESCALATE_CONFIRMED`), never blindly treating judge-negative as clean;
4. **selective diverse jury / conformal abstention** for ambiguous open-ended cases;
5. **sparse exact counterfactual truth** where uncertainty or expected information value is high;
6. **random sentinel dual evaluations** to detect selection bias/drift.

## Why factorization is strategically useful

When the weak model changes, the weak-failure factor changes and can be refreshed cheaply by regenerating only the weak arm. Strong rescue needs refresh on only a sparse weak-failure sample.

When the strong model changes, weak labels remain useful; refresh only the rescue factor.

When model prices change, the learned quality terms remain useful; change the cost multiplier/decision threshold rather than retraining the whole model.

When workload mix changes, semantic/OOD and random-sentinel telemetry reveal where the historical support is thin.

## Guard against counterfactual blindness

A pure bandit system can become self-confirming: if it rarely sends a region to strong, it never learns that strong would have helped there. Therefore preserve a very small **unbiased exploration budget**:

- e.g. 0.5–1% dual-evaluation or randomized routing in policy-eligible traffic;
- stratified so every major semantic/task family receives minimum support;
- stored as high-value calibration evidence rather than routine labels.

The exact production percentage should be chosen from an offline replay, not assumed.

## Relationship to semantic routing

Semantic routing is not discarded. It becomes the **observable coordinate system** for the value learner:

- identifies task/domain and applicable evaluator;
- supplies local performance neighbors;
- detects OOD regions;
- allocates exploration and audit budget;
- conditions judge calibration;
- provides readable routing explanations.

This is closer to vLLM Semantic Router's multi-signal control-plane architecture than to a single embedding nearest-centroid router.

## Research precedents

- Marginal-gain target: [RouteLMT, 2026](https://arxiv.org/abs/2604.22520).
- Sparse performance memory: [ContextualRouter, EACL 2026](https://aclanthology.org/2026.eacl-srw.22/).
- Partial-feedback continual routing: [PILOT, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.1301/); [BaRP, 2025](https://arxiv.org/abs/2510.07429).
- Training-free reliability signals: [CARGO, 2026](https://arxiv.org/abs/2607.20481); [C3PO, 2025](https://arxiv.org/abs/2511.07396).
- Multi-signal routing control plane: [vLLM Semantic Router](https://github.com/vllm-project/semantic-router/blob/main/website/docs/intro.md).

## Strategic success condition

The long-term success metric is not merely APGR on RouterBench. It is:

> **accepted mission quality at materially lower total cost, with refresh cost low enough that routing can be recalibrated whenever models, prices or task distributions change.**

The RouterBench validation gate is a disciplined qualification proxy for the current workstream, not the final definition of value for Hermes.
