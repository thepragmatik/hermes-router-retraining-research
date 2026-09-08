# Feature Specification: Counterfactual Shadow Telemetry

**Feature Branch:** `101-counterfactual-shadow-telemetry`  
**Created:** 2026-09-08  
**Status:** Survived research — ready for implementation  
**Input:** Repair the shadow-learning substrate so real traffic can produce statistically valid, privacy-conscious, joinable routing feedback.

## Why this feature exists

The current shadow implementation cannot produce training data: the HTTP service does not log route decisions, CLI `prompt_id` is hardcoded, there is no stable prompt/message hash/join key, and no outcome is joined. A useful next-generation router needs data that supports both ordinary learning and counterfactual/off-policy evaluation.

This feature is **not** a router uplift algorithm. It is the minimum statistical infrastructure required to learn and evaluate routing policies from deployment-like partial feedback.

## User Scenarios & Testing

### User Story 1 — Reconstruct policy value from simulated logs (P1)

As a routing researcher, I want the telemetry schema and OPE harness to reconstruct known policy values from a full-information dataset after counterfactual outcomes are hidden, so I know the data design is statistically usable before touching live shadow traffic.

**Independent Test:** On RouterBench train-only/full-information matrices, simulate a logging policy with known propensities, retain only chosen outcomes, and estimate the value of at least V1 plus two alternate policies using IPS and DR/SWITCH-style estimators. Compare estimates and intervals with their full-information truth.

**Acceptance Scenarios**

1. Given a simulated stochastic logging policy, when records are written and counterfactual outcomes hidden, then each chosen action has its exact nonzero logging propensity stored.
2. Given target policies whose true values are known from the full matrix, when OPE runs, then the policy ordering and values are recovered within the frozen error/coverage gate.
3. Given a target policy with inadequate support, when OPE runs, then the system flags insufficient overlap rather than returning an authoritative value.

### User Story 2 — Produce joinable shadow decisions (P2)

As an operator, I want every real shadow route decision on the service path to carry a stable privacy-conscious identity and reproducibility metadata so it can later be joined to an outcome.

**Independent Test:** Send repeated, distinct and duplicate requests through a test HTTP service; verify unique/stable request keys, deterministic prompt hashes for duplicates, service-side log parity, model/router version provenance and no raw prompt leakage in the decision ledger.

### User Story 3 — Join delayed outcomes safely (P2)

As a researcher, I want an append-only outcome join that distinguishes true task outcomes, user acceptance, tool/test results, judge annotations and synthetic/proxy labels so downstream learners cannot confuse evidence fidelity.

**Independent Test:** Feed fixture outcomes with multiple evidence types and delayed timestamps; verify exactly-one request join semantics, provenance tags, unresolved/ambiguous joins and late updates.

### User Story 4 — Run bounded randomized sentinels (P3)

As an operator, I want a fail-closed, low-rate exploration mechanism with known propensities on explicitly eligible traffic, so the system can obtain counterfactual coverage without silently experimenting on high-risk requests.

**Independent Test:** In simulation/test mode, verify rate cap, eligibility exclusion, deterministic seeded randomization, exact propensity logging, spend cap, kill switch, and that disabled exploration reduces to the frozen/base policy.

## Edge Cases

- duplicate prompts across different sessions;
- prompt hashes collide or hashing configuration changes;
- service restarts between decision and outcome;
- an outcome arrives twice or contradicts a prior proxy outcome;
- eligible action becomes unavailable after probability assignment;
- provider/model price changes mid-day;
- target policy chooses an action with zero/near-zero logging support;
- privacy policy forbids even a content hash for a traffic stratum;
- user-visible exploration is not permissible: system must support shadow-only dual evaluation instead.

## Requirements

### Functional Requirements

- **FR-001:** Service-side `/route` decisions MUST be logged on the actual HTTP path used by shadow traffic.
- **FR-002:** Every record MUST contain a unique request/event id and a stable caller join key or privacy-approved content hash; `prompt_id=0` style placeholders are forbidden.
- **FR-003:** Raw user prompt text MUST NOT be required in the decision ledger.
- **FR-004:** Records MUST include timestamp, router version, feature/model representation version, action set, chosen action, decision score(s), threshold/policy id, model/provider/revision and price-snapshot id.
- **FR-005:** When exploration/randomization is active, the record MUST include the exact chosen-action propensity and enough policy metadata to reproduce the probability distribution.
- **FR-006:** Outcome records MUST be append-only/joinable and MUST label evidence provenance/fidelity (`task_native`, `human_acceptance`, `randomized_model_outcome`, `benchmark`, `judge`, `synthetic`, `unknown`).
- **FR-007:** Unjoined and multiply joined outcomes MUST be surfaced in a data-quality report.
- **FR-008:** The system MUST support an offline logging-policy simulator using full-information train data.
- **FR-009:** The OPE harness MUST implement at least IPS plus one doubly robust estimator and a variance/overlap diagnostic; SWITCH or weight shrinkage is preferred.
- **FR-010:** The OPE harness MUST refuse or visibly qualify estimates when effective sample size/support is below the preregistered threshold.
- **FR-011:** Randomized sentinel eligibility, maximum rate, allowed actions, spend cap and kill switch MUST be configuration-controlled and fail closed.
- **FR-012:** High-risk/security/privacy-sensitive strata MUST be excluded by default from user-visible randomized exploration.
- **FR-013:** A pure shadow/dual-evaluation mode MUST exist so additional model outcomes can be sampled without changing the response shown to the user.
- **FR-014:** Every schema/config version MUST be recorded so historical logs remain interpretable.
- **FR-015:** The implementation MUST not modify the frozen V1 model weights/threshold.

### Non-Functional Requirements

- Decision logging overhead target: p95 < 5 ms locally excluding fsync/network export.
- Logging failure MUST NOT break a route response; failures MUST increment a visible health/error counter.
- Tests MUST cover crash/restart, duplicate event, missing outcome, unavailable action and propensity invariants.

## Data Contract

Minimum decision fields:

`event_id, ts, session/message join id OR prompt_hash, traffic_stratum, router_id/version, policy_id, action_set, chosen_action, chosen_propensity|null, scores, model/provider/revisions, price_snapshot_id, exploration_mode, schema_version`

Minimum outcome fields:

`event_id, outcome_ts, outcome_type, outcome_value, evaluator/provenance, evaluator_version, finality, metadata, schema_version`

No downstream learner may infer missing propensities as if they were known.

## Success Criteria

### Stage 0 — mandatory cheap falsification

On a train-only full-information replay with at least three target policies:

- OPE MUST rank the target policies correctly in at least **9/10 deterministic simulation seeds**;
- for the base/V1 target and one materially different target, absolute policy-value error MUST be <= **0.015 quality units** or the 95% CI must contain full-information truth in at least **90% of simulation seeds**;
- unsupported-policy diagnostics MUST fire when the target action probability has inadequate overlap;
- deliberately corrupted/missing propensity tests MUST fail loudly.

If these gates fail after one bounded estimator/configuration correction that was preregistered from diagnostics, **kill live randomized telemetry work** and fix the estimator/data design first.

### Stage 1 — shadow data quality

On >=1,000 test/replay/service events:

- >=99.9% valid unique event ids;
- 100% action/model/router version provenance;
- 100% propensities present for randomized events;
- >=99% join success for fixture outcomes;
- 0 raw prompt text in the decision ledger unless an explicit separate privacy-approved artifact is used;
- service-side logging parity verified.

### Stage 2 — live eligibility (operator gated)

No live randomization until Stage 0/1 pass, an explicit operator spend/exploration gate exists, and the sentinel rate/cost/traffic eligibility are frozen in a new preregistration.

## Expected Benefits If Successful

- converts shadow traffic into statistically useful learning data;
- enables unbiased/less-biased evaluation of future policies without exhaustive dual calls;
- unlocks Specs 102 and 108;
- makes model-pool/price changes evaluable with replay/OPE;
- provides a reusable evidence substrate even if no new router ultimately beats V1.

## Stackability / Exclusivity

- **Foundation / stackable with everything.**
- Required for real-data claims in 102 and 108.
- Does not itself stack quality gains and should not be credited as router uplift.
- User-visible randomized sentinel and shadow-only dual evaluation are alternative acquisition modes; prefer shadow-only when it can answer the same question.
