# Implementation Plan: Counterfactual Shadow Telemetry

## Purpose

Implement the minimum telemetry and off-policy-evaluation substrate required to turn shadow traffic into statistically usable routing evidence. This feature must prove the *data design* before changing the live shadow path.

## Constitution Check

This plan satisfies the research constitution by:

- leaving RouterBench test sealed;
- leaving V1 weights and threshold untouched;
- treating telemetry as part of the learning algorithm;
- requiring known propensities for randomized data;
- separating real/task-native outcomes from judges and synthetic labels;
- making Stage 0 a $0 full-information simulation;
- failing closed on exploration/spend;
- requiring support/overlap diagnostics before OPE claims.

## Technical Scope

### New modules

Suggested layout:

```text
telemetry/
  schema.py
  decision_log.py
  outcome_log.py
  join.py
  eligibility.py
  policy.py
  simulator.py
  ope.py
  diagnostics.py
  cli.py
configs/
  telemetry.yaml
results/101/
  stage0_ope.json
  stage0_ope.md
  stage1_data_quality.json
```

Reuse existing `router_shadow.py` and `router_v1_cli.py` only after Stage 0 passes. Do not refactor V1 internals.

## Data Model

### DecisionEvent

Required fields:

- `schema_version`
- `event_id` UUID/ULID
- `ts`
- `session_id_hash` or caller join id when permitted
- `message_id_hash` or caller join id when permitted
- `prompt_hash` only when privacy policy permits
- `traffic_stratum`
- `router_id`, `router_version`
- `representation_version`
- `policy_id`, `policy_config_hash`
- `action_set`
- `chosen_action`
- `chosen_propensity` nullable only for deterministic/non-OPE records
- `action_probabilities` optional but preferred for randomized events
- `scores`
- `model/provider/revision` map
- `price_snapshot_id`
- `exploration_mode`
- `eligibility_reason`

### OutcomeEvent

- `schema_version`
- `event_id`
- `outcome_id`
- `outcome_ts`
- `outcome_type`
- `outcome_value`
- `outcome_scale`
- `provenance_class`
- `evaluator_id/version`
- `finality` (`provisional|final|superseded`)
- `metadata`

No raw prompt is required in either ledger.

## Algorithmic Design

### Stage 0: logging-policy simulator

Use a train-only full-information matrix. For each simulation seed:

1. Define a stochastic logging policy with guaranteed action support, e.g. epsilon-mixture of V1 and uniform/random eligible actions.
2. Sample one action per row and store the exact probability of that action.
3. Hide all unchosen outcomes from the OPE layer.
4. Evaluate at least three target policies: V1, a materially different threshold/policy, and a random or always-action baseline.
5. Compute full-information truth separately.
6. Estimate target values with:
   - IPS;
   - self-normalized IPS as diagnostic;
   - doubly robust (cross-fitted outcome model);
   - SWITCH-DR or clipped DR where weights are heavy-tailed.
7. Report effective sample size, max/quantile importance weights, action coverage, confidence intervals, and policy-value error.

Cross-fitting is mandatory for learned outcome models used by DR to avoid training/evaluation reuse.

### OPE formulas

For target policy `pi` and logging propensity `p_i(a_i|x_i)`:

`w_i = pi(a_i|x_i) / p_i(a_i|x_i)`.

IPS value:

`V_IPS = mean(w_i * y_i)`.

DR value:

`V_DR = mean(sum_a pi(a|x_i)*mu_hat(a,x_i) + w_i*(y_i-mu_hat(a_i,x_i)))`.

For deterministic target policies, `pi(a|x)` is 0/1. Weight clipping/shrinkage must be preregistered and reported, never silently tuned on the evaluation slice.

### Support rule

A target policy is unsupported when any preregistered condition fires, such as:

- chosen target actions have zero logging probability;
- effective sample size falls below a frozen minimum;
- max importance weight exceeds a frozen diagnostic bound without a robust estimator;
- target action coverage is too small for a meaningful CI.

Unsupported results must render as `INSUFFICIENT_SUPPORT`, not as a numeric recommendation.

## Stage 1: service-side schema and join

Only after Stage 0 passes:

- implement append-only JSONL or SQLite/WAL decision logging behind an interface;
- make the HTTP `/route` path and CLI path use the same logger;
- preserve best-effort routing behavior: log failure increments a health counter but does not fail the route;
- use an explicit schema version;
- add fixture outcome ingestion and deterministic join reconciliation;
- emit daily/command-line data-quality reports.

Prefer SQLite/WAL if concurrent service writes are likely; JSONL is acceptable for a single-process research daemon if atomic append and corruption recovery are tested. Do not introduce Kafka/warehouse infrastructure for this research stage.

## Stage 2: exploration policy

Exploration modes, in preferred order:

1. `shadow_dual`: user sees base policy answer; additional action sampled only for eligible low-risk rows.
2. `randomized_sentinel`: selected action can differ from base policy only under explicit operator approval.
3. `disabled`: deterministic V1/base behavior.

Eligibility must be a deterministic policy evaluated *before* randomization and logged. High-risk, privacy-sensitive, security-sensitive, and cost-unbounded strata default to ineligible.

A simple epsilon-mixture is preferred initially because propensities are auditable. Avoid Thompson sampling/UCB in the telemetry feature; those belong to later policy research.

## Privacy and Security

- Use keyed/HMAC hashes rather than raw SHA256 if hashes could permit dictionary attacks on predictable prompts.
- Rotate keys only with an explicit hash-version field; never make historical joins uninterpretable.
- Store no secrets in repo/config examples.
- Add redaction tests ensuring prompt text cannot accidentally appear in decision logs.
- Treat outcome metadata as potentially sensitive; whitelist fields.

## Statistics

Stage-0 runs: minimum 10 deterministic simulation seeds. Use paired comparisons against full-information truth. Report mean absolute error, CI coverage, policy-order recovery, ESS and overlap.

Do not optimize estimator hyperparameters against the same simulation seeds used for the final gate. One preregistered diagnostic correction is allowed by the spec; after that, fail Stage 0 and revise the spec.

## Cost Plan

- Stage 0: $0; stored train-only matrix.
- Stage 1: $0; local fixtures and service tests.
- Stage 2 dry-run: $0.
- Any live/dual model calls: separate prereg + operator gate + explicit cap. Default remains disabled.

## Rollback / Stop Logic

- Stage 0 failure => no live logging/exploration modification beyond offline prototypes.
- Schema/join integrity < gates => fix data path; do not collect “maybe useful” traffic.
- Propensity corruption => quarantine affected rows permanently from IPS/DR use.
- Live exploration errors or spend drift => kill switch to deterministic base policy.

## Required Verification

- unit tests for schema validation and versioning;
- property tests: propensities in `(0,1]`, sampled action belongs to action set, probabilities sum to 1 where full distribution stored;
- crash/restart/concurrency logging tests;
- duplicate/out-of-order outcome tests;
- support-failure tests;
- simulator truth reconstruction tests;
- raw-prompt leakage scan.

## Deliverables

- code + tests;
- `results/101/STAGE0_OPE.md` and machine-readable JSON;
- `results/101/STAGE1_DATA_QUALITY.md`;
- schema documentation;
- explicit operator prereg template for any Stage-2 live exploration;
- decision entry in mission log: `KILLED | STAGE0_PASS | SHADOW_READY | LIVE_ELIGIBLE`.