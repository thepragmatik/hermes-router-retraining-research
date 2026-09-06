# Adversarial notes on the stackable-gains pivot

**Date:** 2026-09-06

The pivot should not become a new pile of attractive components that are assumed to work together. These are the strongest objections found in the final research pass.

## 1. The historical target may contain an intrinsic single-draw noise floor

A 2026 preprint, [How Much of the Routing Gap Is Real?](https://arxiv.org/abs/2607.03436), argues that per-query routing oracles built from one stochastic generation per model contain a component no single-commit router can reproduce. In three controlled open-model regenerations, it estimates **12–36% of the router-to-oracle gap** as single-draw label noise in the studied pools. The work is a preprint, so treat the exact percentage cautiously, but the structural point is important.

**Implication for Hermes research:** repeated failures to reach a historical single-draw routing target may partly reflect an ill-posed target, not only a weak classifier. Run a train-safe repeated-generation audit before spending another large effort on a single-commit router. Test-time resampling is one direct way to recover some stochastic headroom.

A related training-free preprint, [CARGO](https://arxiv.org/abs/2607.20481), uses prompt-varied local-model samples plus Bayesian early stopping and reports strong offloading performance without a trained router. This reinforces adaptive cheap sampling as a materially different experiment, but its claims need local reproduction.

## 2. Internal confidence is task-dependent

[Masked by Consensus, ACL 2026](https://aclanthology.org/2026.acl-long.483/) tests whether a model's own hidden states contain privileged correctness information. On standard evaluation, self-probes were comparable to peer-model probes. On model-disagreement subsets, self-representations did show extra signal for **factual knowledge**, but not for **math reasoning**.

**Implication:** P2 internal-state confidence must report performance by task family. A global hidden-state score should not be assumed to work across RouterBench. For math/reasoning, agreement, verification, or task-specific probes may be more useful.

## 3. Stacking can fail through correlated errors

Two components can each look useful alone but solve the same easy cases and fail on the same hard cases. The full system may therefore gain much less than the sum of its individual improvements.

**Required defense:** for each component report:

- errors fixed uniquely by this component;
- errors shared with existing components;
- new errors introduced;
- marginal frontier movement after composition.

Run pairwise ablations for overlapping confidence signals before building a large stack.

## 4. More models is not automatically better

[LLMRouterBench, Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1881/) finds diminishing returns from larger ensembles relative to careful model curation.

**Implication:** P0 should choose a mid-tier for **complementary rescues per cost**, not overall leaderboard quality. A model that is slightly better but fails on the same prompts does not justify another tier.

## 5. More cheap samples are not automatically better

Repeated sampling only helps when samples contain useful error diversity and when the system can identify/select good outcomes. [Scaling Test-Time Compute Without Verification or RL is Suboptimal, ICML 2025](https://proceedings.mlr.press/v267/setlur25a.html) argues verification is critical for efficient test-time scaling.

**Implication:** P1 must report the *marginal* gain of sample 2/3/5 and the verifier/selection mechanism. Stop when added samples no longer pay for latency/compute.

## 6. Distillation can exceed student capacity or create regressions

Difficulty-aware/capacity-aligned distillation is promising, but a small student cannot necessarily absorb every frontier capability.

**Implication:** P5 starts with narrow recurring failure clusters and a replay set, not broad imitation. Use multiple seeds and report regressions on previously solved strata.

## 7. RouterBench can become a local optimum for the wrong strategic goal

The parent Hermes objective is accepted agent mission quality at lower total cost. A single-turn benchmark cannot capture workflow-stage dynamics, retries, tool failures, cache/session continuity, or model-switch overhead.

Peer-reviewed 2026 work such as [MTRouter](https://aclanthology.org/2026.acl-long.2045/) and [LLM-as-Scheduler](https://aclanthology.org/2026.acl-long.581/) shows substantial cost-quality gains from history-aware turn routing and workflow scheduling in their settings.

**Implication:** keep RouterBench as a controlled historical diagnostic, but do not let inability to beat its v1 APGR prevent a separate Hermes workflow-stage experiment.

## Red-team conclusion

The pivot survives, with a constraint:

> **Do not build the full trust stack first. Build a measured ladder. Every rung must earn its place.**

The highest-value first checks remain:

1. model-pool complementarity;
2. repeated cheap-sample recoverability/noise audit;
3. task-conditioned internal confidence;
4. incremental composed ablation;
5. agentic stage routing as a separate strategic track.
