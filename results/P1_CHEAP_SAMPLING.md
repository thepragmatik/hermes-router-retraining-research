# P1 — Adaptive cheap sampling (stored-label simulation)

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P1_P2.md` (frozen `d8af031`, before any holdout scoring) · Script: `experiments/p1_p2_sampling_verifiers.py` · Raw: `results/P1_P2_raw.txt`

**Surfaces:** dev-fit 24,835 train rows (selection) · pivot holdout 4,358 rows (seed-42 md5, scored ONCE) · validation untouched · test SEALED.

**Methodology note (honesty):** the run was executed three times. The first two passes are VOID (harness bugs: vectorization error in the verifier, cost-scaling error in anchor rows). All bugs were fixed and dev-probe verified BEFORE the final pass; the final pass is the only holdout exposure. Fixes are documented in `results/BINARIZATION_NOTE.md`. No threshold was tuned on the holdout.

## Headline (pivot holdout, single pass)

| policy | acc | cost/row | frac_strong | PGR | Δacc vs v1 [95%] | cost vs v1 |
|---|---|---|---|---|---|---|
| always_weak | 0.2175 | 0.0000458 | 0.0000 | 0.0000 | −0.4300 | −98.2% |
| always_strong | 0.6494 | 0.0032889 | 1.0000 | 1.0000 | +0.0018 [−0.0002,+0.0039] | +28.5% |
| **router v1 @0.30** | **0.6475** | **0.0025589** | **0.7749** | **0.9957** | — | — |
| P1-a oracle pair (ceiling) | 0.7148 | 0.0015411 | 0.4105 | 1.1514 | +0.0672 [+0.0594,+0.0748] | −39.8% |
| P1-b disagreement escalate | 0.6397 | 0.0031255 | 0.1314 | 0.9777 | −0.0078 [−0.0124,−0.0032] | +22.1% |
| P1-c verifier-gated pair | 0.2545 | 0.0000999 | 0.0262 | 0.0855 | −0.3931 [−0.4091,−0.3768] | −96.1% |

## P1 measures (dev-fit)

- P(mid repairs | weak fails) = **0.4693** — the second cheap sample has real repair potential.
- Agreement→correctness calibration: P(weak ok | weak & Yi agree) = **0.7704** (Wilson95 [0.7552, 0.7850], n=3,058).
- P(confident co-failure, i.e. co-failure AND string-agreement) = **0.0283**.
- Disagreement rate = 0.8769 — string-level agreement between two different models is rare, so disagreement-escalation escalates almost always.

## Frozen-gate verdicts (holdout)

- **P1-b disagreement-escalate: FAIL** (and dominated by v1: lower acc, +22.1% cost). Root cause: cross-model string agreement is nearly always absent (87.7% disagreement), so the policy pays weak+Yi on every row AND strong on 87.7% of rows — the worst of both worlds. The v1 router's learned P(strong wins) is a far more efficient trigger.
- **P1-c verifier-gated pair: FAIL** (acc 0.2545 vs v1 0.6475). Root cause: the VF format-check accepts 74% of weak responses (format ≠ correctness; accept precision 0.29–0.34 ≈ base rate), so P1-c degenerates to "almost always ship weak". Also fails the preregistered secondary rule (must beat P1-b: NO).
- **P1-a oracle pair: PASS on the frozen gate but NOT adoptable** — it is a preregistered ceiling diagnostic (acceptance uses the correctness label itself, invisible at runtime). It bounds what a perfect runtime trigger for the weak→Yi→strong cascade could achieve: +6.7pp quality at −39.8% cost vs v1. **This is the P3/P4 design target**, not a keepable policy.

## Consequences

1. Neither deployable P1 variant beats v1. Keep gate kills both (mission §P1: retain only policies that move the end-to-end frontier after their own cost is counted).
2. The oracle-pair ceiling (+6.7pp / −39.8% vs v1) proves the heterogeneous cascade has headroom **if** a runtime-visible trigger can capture ≥50% of the oracle's quality lift (preregistered proxy bar) — that trigger is exactly what P3 (internal confidence) and P4 (stack composition) must supply. P1's evidence feeds P4's composition order rather than entering the stack itself.
3. v1's learned trigger remains the strongest single routing signal measured; the naive "extra cheap sample" family is closed as a standalone layer.

## What was measured vs not

- Measured: weak+Yi heterogeneous pair with three trigger families, on 29,193 stored rows, with paired bootstrap CIs (1,000 resamples, seed 42).
- Not measurable at $0: true repeated sampling from one model (0-shot pool stores one response per model per row); current-generation cheap models (pool-currency follow-up, logged in P0).
