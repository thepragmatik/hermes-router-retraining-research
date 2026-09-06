# PREREG-P5 — three-tier / specialist cascade (weak → mid → frontier)

**Frozen BEFORE any scoring.** Protocol: `experiments/PIVOT_PROTOCOL.md`. Spend $0 (stored responses). Test SEALED (never loaded; 3678-row assert only). Validation untouched. Pivot holdout (4,358) scored ONCE.

## Motivation (mission §P5 + P0)

All dynamic triggers are dead (P1b/P1c/P2/P3/P4). The only untested lever is
the **shape of the escalation ladder** itself. P0: Yi-34B-Chat repairs 47.02%
of weak failures at 4.05× weak cost — the best mid-tier by complementarity.
Weak-first architecture is the only one with headroom (P1a oracle +6.7pp at
−39.8% cost vs v1), so the cascade arms live there. Reference layer: v1 @0.30
(only qualified layer; holdout acc 0.6475 @ $0.0025943/row).

## Frozen operating points (built on TRAIN-derived signals; dev-fit only)

Trigger: v1's own partition (`P(strong) >= 0.30` from the cached MF probs) is
the single surviving signal — used verbatim, never refit.

### Cascade arms (evaluated on the v1-WEAK stratum — the only rows where a cascade can act)

- **C1 two-tier baseline:** v1-weak → strong (this is v1 itself; $0 extra structure).
- **C2 three-tier cascade:** v1-weak → Yi (mid) → strong iff Yi also wrong
  (oracle-success variant: **C2a** escalate to strong only when Yi's answer is
  correct — measures the tier's real resolution; conservative deployable
  variant **C2b**: escalate to strong whenever a fixed static trigger fires —
  the only triggers available are dead per P4, so C2b is instantiated as
  escalate-on-ALL v1-weak rows).
- **C3 always-three-tier:** every row pays weak + Yi; strong only when both
  wrong (oracle-success).

### Success accounting (oracle-success disclosure)

C2a/C3 use stored correctness to decide the strong call — they are **upper
bounds on what a perfect mid-tier arbiter would achieve**, the same status as
P1a's oracle ceiling. The mission question here is economic: does inserting a
mid tier reduce frontier spend at non-negative quality vs the two-tier
baseline, under a PERFECT arbiter? If even the perfect-arbiter bound fails the
keep gate, the mid tier cannot be justified by any real trigger (all triggers
are dead, P4).

## Keep gate (frozen)

The mid tier survives iff, vs C1 (v1):
- **G1 (cost):** total cost/row ≤ C1 − 0.0002 with acc not below C1 − 0.002, OR
- **G2 (quality):** acc ≥ C1 + 0.020 with cost not above C1 + 0.0002.

Both arms evaluated on dev-fit first; the arm(s) passing the gate (if any) go
to the single holdout pass. If no arm passes on dev-fit, declare NO-GO without
touching the holdout (mission economics: don't spend a holdout pass on a dead
arm). Bootstrap: paired, seed 42, 1000 resamples, 95% percentile CIs.

## Anti-leakage

Features/decisions use only: v1 cached probs, weak/Yi/strong stored responses
and correctness-for-oracle-accounting. No validation split, no test split, no
threshold refitting. Binarization: `fillna(0).astype(int)` truncation
convention (BINARIZATION_NOTE).

## Deliverable

`results/P5_THREE_TIER.md`; ledgers appended; MISSION_LOG updated.
