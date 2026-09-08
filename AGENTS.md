# AGENTS.md — Router Innovation Program entrypoint

## Active mission on this branch

This branch is the **2026-09-08 Router Innovation Program**. The previous stackable-uplift mission is historical evidence: its uplift experiments mostly failed, V1 remains the useful frozen control, and later operational/shadow/generator work exposed additional data-quality gaps.

Do **not** execute the old `STACKABLE_ROUTING_MISSION.md` as the active mission on this branch.

## Canonical entrypoints

For an orchestrator over the whole research program, execute:

**[`ideas/META_PROMPT.md`](ideas/META_PROMPT.md)**

For a human-readable idea/dependency index, read:

**[`ideas/README.md`](ideas/README.md)**

For program status during execution, maintain:

**[`ideas/STATUS.md`](ideas/STATUS.md)**

The Spec Kit roadmap is:

**[`specs/router-innovation-2026-09-08/roadmap.md`](specs/router-innovation-2026-09-08/roadmap.md)**

The governing constitution is:

**[`.specify/memory/constitution.md`](.specify/memory/constitution.md)**

## Individual idea execution

Each idea has its own independent GitHub Spec Kit package under `specs/<idea>/` containing:

- `spec.md`
- `plan.md`
- `tasks.md`
- `PROMPT.md`

Use the idea's `PROMPT.md` to launch a dedicated execution agent. Do not ask one child agent to implement the entire nine-idea program in a single context.

Ideas:

1. `101-counterfactual-shadow-telemetry`
2. `102-doubly-robust-uplift-router`
3. `103-bayesian-semantic-memory`
4. `104-whitened-latent-gain-probe`
5. `105-conformal-safety-envelope`
6. `106-sequential-voi-controller`
7. `107-diversity-model-portfolio`
8. `108-multifidelity-synthetic-real`
9. `109-hermes-stage-router`

## Research premise

The next gains should come from changing at least one of:

- the **information/data-generating process** (identified shadow telemetry, real outcomes);
- the **decision mathematics** (causal uplift, uncertainty/risk control, VOI);
- the **representation/evidence source** (measured semantic memory, true hidden states);
- the **candidate model pool** (complementarity rather than leaderboard quality);
- the **fidelity mix** (synthetic as prior, real as authority);
- the **unit of routing** (agent workflow stage instead of whole prompt).

Do not merely build a larger prompt classifier.

## Non-negotiables

- RouterBench test remains **SEALED**.
- V1 remains the mandatory control where applicable; do not modify its frozen weights/threshold to make a new idea pass.
- Historical validation is finalists-only; use train-only development/holdout and record exposures.
- Default paid spend is **$0**. No child prompt currently authorizes paid calls.
- Paid work requires a fresh preregistration, current model/provider prices, explicit cap, fail-closed authorization and an explanation of why cheaper evidence is exhausted.
- Synthetic labels are not real truth.
- Deterministic historical shadow logs without known propensities do not become unbiased counterfactual data after the fact.
- Semantic cluster→fixed model routing remains retired.
- Generic symmetric LLM judge supervision, entropy-only acquisition, naive disagreement routing and larger embedding/classifier reruns remain retired unless a spec demonstrates materially new information/identification.
- Every idea must pass its own cheap falsification gate before expensive implementation.
- A failed gate is evidence. Do not relax it after seeing results.
- Stack only independently qualified components and measure marginal contribution/error overlap.
- Current model IDs/prices/provider/privacy constraints must be refreshed at execution time.
- Any user-text-driven routing candidate must receive basic adversarial cost-manipulation testing before promotion.

## Recommended orchestration order

Wave A, mostly parallel and $0:

- 101 Stage 0 telemetry/OPE simulator;
- 107 model-pool audit;
- 103 semantic performance memory;
- 104 latent feasibility/Stage 0;
- 105 safety envelope on V1/current scores.

Wave B:

- 102 retrospective Stage 0, then real phase only after 101 data exists;
- 108 retrospective transfer test, then real phase only after 101;
- 105 may wrap independently qualified finalists.

Wave C:

- 106 only after at least two actions/signals independently pay;
- 109 whenever Hermes trace viability permits; it is a separate estimand.

## Definition of done

The program is complete when all runnable ideas have converged to their exact spec-defined status and the orchestrator produces an integration recommendation identifying:

- what qualified;
- what was killed;
- what is stackable vs mutually exclusive;
- the current best single-turn routing architecture/model pool;
- the current best agentic-stage strategy;
- total evidence/spend;
- and the exact next Hermes shadow action—or a recommendation to stop router work.

A negative program conclusion is valid if the evidence shows a simpler model/workflow policy is superior.