# DRAFT PREREG — Idea 101 Stage-2 Live Exploration (randomized sentinel / shadow dual)

> **STATUS: DRAFT — NOT EXECUTED.** This file is a template only. No live
> randomization, no paid calls, and no production-service changes have been
> made or are authorized by this document. Every field in section 9 must be
> filled by the operator BEFORE any live exploration begins. Until then the
> only valid exploration mode is `disabled` (the shipped default).

## 1. What this prereg would authorize (if countersigned)

A bounded, fail-closed randomized-sentinel / shadow-dual slice on
policy-safe traffic through the 101 telemetry path, for the purpose of
obtaining counterfactual coverage (known propensities) on real traffic.

## 2. Preconditions (all must hold at activation time)

- [ ] Idea 101 terminal status `SHADOW_READY` with all Stage-1 gates measured PASS (see `results/101/STAGE1_DATA_QUALITY.md`);
- [ ] Stage-1 evidence regenerated on the current HEAD within 14 days;
- [ ] kill switch verified in BOTH states on the production service (orchestrator);
- [ ] current model IDs/prices/provider constraints refreshed (constitution XII);
- [ ] 102/108 downstream data requirements reviewed so the sentinel answers a real estimand;
- [ ] operator sign-off recorded in section 9.

## 3. Frozen exploration configuration (fill before activation)

- `mode`: `shadow_dual` | `randomized_sentinel` (prefer shadow_dual; the spec prefers shadow-only when it can answer the same question) — TBD
- `epsilon`: TBD (proposal: 0.10)
- `seed`: TBD (fixed integer; logged with every event)
- `sentinel_rate_cap`: TBD (proposal: 0.05, fail-closed)
- `spend_cap_units`: TBD (explicit cap + fail-closed hook already implemented)
- `eligible_strata`: TBD (deny-by-default allowlist; unknown strata fail closed)
- `excluded_strata`: security, privacy, high_risk, pii, secret, prod_unsafe (non-negotiable defaults, FR-012)

## 4. Estimand and analysis plan (frozen before activation)

- Primary: IPS on sentinel-covered traffic; DR/SWITCH-DR (Stage-0 estimators, frozen M=20) as secondary.
- Support rule: identical to Stage-0 prereg (`results/101/PREREG.md`); unsupported strata render `INSUFFICIENT_SUPPORT`, never numeric claims.
- Minimum coverage before any analysis: TBD events with outcomes joined.
- Success question: TBD (must name the decision the data will inform, per constitution IX).

## 5. Safety commitments (already implemented, to be verified at activation)

- propensities logged EXACTLY on every randomized event (FR-005);
- eligibility evaluated deterministically before randomization and logged;
- rate cap + spend cap trip fail-closed to the deterministic base policy;
- kill switch (`router.enabled: false`) reverts every path to deterministic V1 without deploy;
- logging failure never breaks a route (error counter on /health);
- no live randomization on excluded strata; unknown strata fail closed.

## 6. Stop rules

- any propensity-integrity alarm (missing/out-of-range propensity on a randomized event) → quarantine affected rows permanently, halt exploration;
- realized rate drifting above cap +1 event tolerance → halt;
- any user-visible behavior change outside approved sentinel rows → immediate kill switch + incident review;
- spend within epsilon of cap → halt before crossing.

## 7. Rollback

git revert of the exploration-config commit + orchestrator-side service
restart; config-only kill switch is instantaneous and preferred.

## 8. Spend

TBD by operator. Default $0: this draft authorizes NO model calls.

## 9. Operator approval (REQUIRED — leave unfilled in draft)

- Operator name: ______________
- Approval date: ______________
- Authorized mode: ______________
- Authorized epsilon/rate cap/spend cap: ______________
- Authorized strata: ______________
- Signature/link to approval record: ______________
