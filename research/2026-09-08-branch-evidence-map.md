# Branch and Evidence Map — 2026-09-08

## Purpose

This document freezes the repository state that informed the innovation research. It prevents a future agent from reading only `main` and missing the operational/shadow and generator-factory work that lives on divergent branches.

## Branches inspected

### `main`

Role: formal close-out of the first stackable-router experiment mission, plus later mission wording updates.

Important evidence:

- `PIVOT_FINAL_RECOMMENDATION.md`
- `results/P0_MODEL_POOL.md`
- `results/P1_CHEAP_SAMPLING.md`
- `results/P2_VERIFIERS.md`
- `results/P3_INTERNAL_CONFIDENCE.md`
- `results/P4_TRUST_STACK.md`
- `results/P5_THREE_TIER.md`
- `results/P6_WEAK_UPLIFT.md`
- older experiment preregistrations under `experiments/`

Main's declared conclusion — `ROUTING NOT ECONOMIC` — is scoped to the P0–P6 family and available corpus/signals. It must not be interpreted as a proof that every possible router is uneconomic.

### `feat/router-v1-operationalise`

Tip observed during review: `71458581987940aab81ec8fe94ae28a004ae1952`.

Relative to `main` when reviewed: branch was 16 commits ahead and 2 commits behind. It contains the V1 shadow service/CLI, A/B replay, latency tests, chaos checks and live HTTP agreement evidence.

Important files:

- `router_shadow.py`
- `router_v1_cli.py`
- `router_config.yaml`
- `experiments/007-shadow-ab-prereg.md`
- `evidence/ab/shadow-ab-memo-2026-09-06.md`
- `evidence/ab/live_http_agreement_2026-09-07.json`

### `feat/generator-pivot-r0`

Tip observed during review: `94d912741be3b7cbfc21d5d0e7b82fd50e50c964`.

Relative to `main` when reviewed: branch was 70 commits ahead and 2 commits behind. It contains the operationalisation branch work **plus** the synthetic generator/label factory and the 2026-09-08 V1 shadow-gap audit.

This branch is the base for `research/router-innovation-2026-09-08` because it contains the richest current evidence.

Important files:

- `MISSION_LOG.md`
- `GENERATOR_PREREG.md`
- `results/V1_BASELINE_GAPS.md`
- `evidence/gen_factory/*`
- `experiments/gen_factory/*`
- `evidence/shadow/shadow_log.jsonl`

## What the prior work actually established

### 1. V1 is a meaningful selector

The A/B replay shows the router is not merely spending a large budget randomly. On the historical validation replay it strongly beats always-weak and a cost-matched random policy. It remains slightly below always-strong accuracy while substantially reducing modeled cost. This result is in-sample with respect to V1's frozen validation threshold and must be treated as an upper-bound operational replay, but it establishes that the routing concept has real selection signal.

### 2. The old uplift stack failed for specific reasons

- **P1:** heterogeneous cheap-model disagreement escalated too often; string disagreement was ~88% and the policy cost more while losing quality. The oracle heterogeneous pair nevertheless exposed substantial theoretical headroom.
- **P2:** stored RouterBench outputs lacked machine-checkable contracts. Format/numeric/JSON/code-structure verifiers did not provide high-precision correctness evidence.
- **P3:** the experiment explicitly did **not** test true model hidden states or log probabilities. RouterBench stored responses did not contain them. The tested response-shape/verifier/V1 features were not enough to improve cascade economics.
- **P4:** composing the killed disagreement/verifier/probe layers did not create a paying stack.
- **P5:** a three-tier model pool has real oracle headroom, but only if the system has an arbiter that can identify when the first two answers are wrong.
- **P6:** under V1's weak-routed stratum, nearly all remaining failures were both-models-fail; only 94 train-safe rescue examples existed, making narrow LoRA uplift uneconomic for that historical pair.

These are strong negative results against rerunning the same information structure. They do **not** rule out methods that collect new information, use a different current model pool, use genuine internal states, or route at a different stage/unit.

### 3. The shadow implementation did not create learning data

`results/V1_BASELINE_GAPS.md` records six gaps. The critical ones are structural:

- CLI `prompt_id` is hardcoded to zero;
- the actual HTTP service path never appends a decision record;
- no prompt text/content hash or caller join key exists;
- no model answer/outcome/correctness join exists;
- the tiny log is mostly health traffic and not representative.

Consequence: the shadow period proved service health, threshold behavior and kill-switch mechanics, but produced **zero usable training rows** by construction.

This is why Spec 101 treats counterfactual telemetry as a learning-system primitive rather than a logging afterthought.

### 4. The generator factory improved substantially, but transfer is unproven

The generator branch is valuable work, not a dead end:

- R4 exposed an important key-integrity failure: a generated key could be wrong while the strong model produced the true answer and was graded incorrectly.
- R5 introduced strict K=3 self-consistency/key validation and measured 0 wrong keys in its audited accepted sample, albeit at low yield.
- R6 traded some integrity for yield and admitted a wrong numeric key.
- R7a removed that looser agreement arm; its audited numeric keys were 0/11 wrong, usable label yield among accepted items was high, both-fail was low and cost per usable synthetic label was tiny, while overall item yield remained only 26%.

The surviving conclusion is therefore **not** “synthetic labels are trustworthy.” It is: the project now has a relatively high-integrity low-yield synthetic factory whose real-traffic transfer value has not been established. Spec 108 is designed around that exact gap.

## Historical method boundaries for new work

The new specs must not accidentally rename old failures:

| Old/failed pattern | New work must differ by |
|---|---|
| prompt embedding → binary route | new outcome signal, causal target, latent representation, or multi-model ranking |
| semantic cluster → model | retrieve measured outcomes with uncertainty / capability decomposition |
| symmetric judge labels | selective/calibrated evidence only; real outcomes remain higher fidelity |
| entropy-guided label acquisition | known-propensity exploration or explicit coverage/diversity objective |
| disagreement → escalate | sequential value-of-information using calibrated action values, not raw disagreement |
| synthetic labels as truth | synthetic as low-fidelity prior corrected/tested against real outcomes |
| old model-pool scoring | current/diverse pool selection under explicit complementarity/cost objective |

## Base branch choice for this research

`research/router-innovation-2026-09-08` was created from `feat/generator-pivot-r0`, not `main`, so the research and specs can reference the latest operational/generator evidence directly.

No previous results were deleted or rewritten. The new branch adds a separate Spec Kit program and leaves historical artifacts available for audit.
