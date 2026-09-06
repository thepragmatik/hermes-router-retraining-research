# P4 — Trust-stack composition by incremental ablation

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P4.md` (frozen `38c67d6`, before scoring) · Script: `experiments/p4_stack_composition.py` · Raw: `results/P4_raw.txt`

**Revised build order (prereg §0, evidence-justified):** P1–P3 killed every dynamic layer *as an add-on over v1*. The only composition with real headroom is the weak-first architecture (P1a oracle: +6.7pp / −39.8% vs v1), so the preregistered order tests the killed layers as a stack there: L1 weak-first re-serialization of v1's partition (structural control), L2 +Yi disagreement (P1b policy via `op_point`), L3 +VF sanity gate, L4 +P3 probe at the frozen P3 operating point (τ=0.373159, R+V+P, C=3.0). Marginal retention gates (dev-fit paired bootstrap, seed 42): keep a layer only if quality is not significantly worse AND cost is not significantly higher.

## Layer ladder (dev-fit, n=24,835)

| layer | acc | cost/row | Δ vs previous [95%] | verdict |
|---|---|---|---|---|
| L0/L1 = v1 (control) | 0.6400 | 0.0025682 | — | baseline |
| L2 +disagree | 0.6251 | 0.0025122 | −0.0098 [−0.0107,−0.0067] / +0.0002859 [+0.0003385,+0.0003871] | REMOVE |
| L3 +VF gate | 0.6251 | 0.0025122 | identical to L2 (VF adds no acceptances beyond disagreement on dev) | REMOVE |
| L4 +probe | 0.6284 | 0.0026824 | −0.0065 [−0.0065,−0.0031] / +0.0004561 [+0.0005563,+0.0005990] | REMOVE |

**Structural control verified in-code:** L1's partition equals v1's exactly (`assert np.array_equal`); on the holdout it reproduces v1's accuracy to the fourth decimal (0.6475) — quality identity confirmed. The reported L1 cost on the holdout (+$0.0001855 vs v1's c_w + v1m·c_s accounting) is purely an accounting-convention difference (pair-pipeline books a Yi mid call on every v1-weak row); quality and escalation partition are identical, and the composition verdicts do not depend on it.

**No layer survived retention.** The surviving "stack" is L1 = v1 itself; the ladder was never entitled to a holdout arm beyond the controls, and per prereg §3 the P4 outcome is declared directly.

## Holdout confirmation (single pass; all four arms reported for the record)

| arm | acc | cost/row | esc_share | d_acc [95%] | d_cost [95%] |
|---|---|---|---|---|---|
| v1 @0.30 (ref) | 0.6475 | 0.0025943 | 0.7749 | — | — |
| L1 (structural control) | 0.6475 | 0.0027799 | 0.7749 | +0.0000 [+0.0000,+0.0000] | +0.0001855 (convention) |
| L2 disagree | 0.6397 | 0.0031255 | 0.8800 | −0.0078 [−0.0124,−0.0032] | +0.0005312 |
| L3 +VF gate | 0.6397 | 0.0031255 | 0.8800 | −0.0078 [−0.0124,−0.0032] | +0.0005312 |
| L4 +probe | 0.6453 | 0.0033232 | 0.9401 | −0.0023 [−0.0057,+0.0014] | +0.0007289 |

Frozen qualification gates on the surviving stack: **Q1 FAIL** (d_acc +0.0000 < +0.020), **Q2 FAIL** (d_cost +0.0001855 > −0.0002). Error overlap: uniquely fixed 0, newly broken 0 (2822 both-correct, 1536 both-wrong) — L1 is v1, exactly.

## Why the weak-first composition also fails (mechanism, consistent with P1b/P3)

- v1's route signal is strong precisely where weak-first needs weak to be good: on v1-weak rows weak answers are only 4.7% correct, so "weak-first + escalate the v1-weak stratum" buys almost nothing — and disagreement/VF/probe triggers all escalate *more* rows than v1 does (esc_share 0.88–0.94 vs 0.775), spending mid/strong calls on rows where weak's 21.7% base was already the best available service.
- Disagreement with Yi is anti-informative at scale here: P(weak ok | agree) = 0.77 but the escalation side (disagree → strong) lands on rows where strong is only ~63% correct and weak+Yi sequential cost is always paid — hence −0.8pp at +20% cost, matching Phase C's P1b kill (−0.8pp at +22.1%) almost exactly. Two independent compositions of the same policy failing identically satisfies mission §14's "two clean ablations" kill rule.
- The probe cannot rescue the cascade: transplanted to the weak-first base it escalates 94% of rows and still nets −0.2pp (holdout CI spans zero; cost decisively worse). P3's kill was not an artifact of the v1 anchoring.

## Verdict

**P4 outcome (prereg §3, first branch): V1 ALONE IS THE STACK.** No composition of disagreement, verifier gating, or answer-aware probing — over v1 (P1b/P1c/P3) or on the weak-first architecture (this phase) — produces a paying dynamic layer on this corpus. The qualified routing layer for P5 onward is v1 @0.30 (holdout acc 0.6475 @ $0.0025943/row). Per mission §14 the trigger/verifier/probe layer family is killed after multiple clean ablations; revival conditions as recorded in P2/P3 docs (machine-checkable contracts; logprob-bearing corpus or weak-first prereg with a fundamentally better trigger signal).

Ledgers: frontier +5 rows (L2/L3/L4 dev + holdout as recorded), component_effects +2, error_overlap +1. Latency deltas: every killed layer adds ≥1 cheap/mid call per row plus a frontier call when triggered — strictly dominated by v1's single-call-per-row profile; no wall-clock data exists in this corpus.
