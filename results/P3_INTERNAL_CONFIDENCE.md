# P3 — Answer-aware internal confidence

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P3.md` (frozen `b10df12`, before any holdout scoring) · Script: `experiments/p3_internal_confidence.py` · Raw: `results/P3_raw.txt`

**Feasibility declaration (prereg):** RouterBench-0shot stores one TEXT response per model per row — no log-probs, no hidden states. The true-internal family was NOT tested and is not claimed. Signals tested (runtime-visible, $0): **R-shape** (length, ends-with-number, code fence, hedging, digit count, short-answer), **V-out** (VF/VN/VM verifier outputs on the weak response), **P-conf** (v1 cached P(strong); baseline arm only).

**Leakage audit:** features built only from the weak model's response text, eval-family, and v1 cached P. Correctness/cost/oracle/other-model fields never enter feature matrices (enforced in `build_features`).

## Dev-fit selection (5-fold OOF, md5 fold blocks, 3 salts, C grid honored)

| set | best AUROC | note |
|---|---|---|
| R | 0.6711 (C=0.3) | response shape alone |
| V | 0.6665 | verifier outputs alone |
| R+V | 0.6924 (C=0.3) | |
| **R+V+P** | **0.7385 (C=3.0)** | SELECTED |

Task-family AUROC (adversarial rule §P3): gsm8k 0.7846, open 0.8208, mbpp 0.7127, choice 0.6514, **hellaswag 0.5596 (marginal — signal dropped there** per the drop-below-0.55-near rule; family heterogeneity confirmed).

## The decisive structural finding (why the ceiling collapsed)

The Phase C target (+6.7pp / −39.8% vs v1) was the **weak-first** oracle ceiling. Measured under the preregistered v1-anchored realizable definition:

- v1 routes weak on 22.5% of holdout rows — and on exactly those rows weak is **4.7%** correct and strong is **5.5%** correct (dev-fit). v1's prompt-side signal already isolates the rows where BOTH cheap-and-strong answers fail; almost nothing is recoverable behind v1's weak-side decision.
- **Realizable oracle ceiling over v1 (holdout): +0.32pp acc [+0.0018,+0.0050] at +$0.0000106/row** — economically meaningless, and it is an ORACLE (unreachable).
- Meanwhile v1's routed-strong rows sit at 82.0% strong-accuracy: v1 is already capturing nearly all available (strong−weak) mass.

Interpretation: the +6.7pp P1-a headroom exists only for a **weak-first architecture** (pay weak's 21.7% base on every row, escalate on weak failure). v1-first architecture cannot harvest it because v1 only routes weak where weak is worse than useless. Reaching the P1-a frontier therefore requires replacing v1's operating point, not adding an answer-aware trigger on top of it.

## Frozen operating points → single holdout pass (all gates pre-registered in `PREREG_P3.md`)

| arm | acc | cost/row | esc_share | d_acc [95%] | d_cost [95%] | verdict |
|---|---|---|---|---|---|---|
| v1 @0.30 (ref) | 0.6475 | 0.0025943 | 0.7749 | — | — | — |
| O1 quality (τ=0.3732) | 0.5656 | 0.0025558 | 0.7632 | −0.0819 [−0.0918,−0.0723] | −0.0000385 | **FAIL** |
| O2 cost (τ=0.2118) | 0.6485 | 0.0033105 | 0.9927 | +0.0009 [−0.0009,+0.0030] | +0.0007162 | **FAIL** |
| O3 coverage-matched | 0.5665 | 0.0025611 | 0.7648 | −0.0810 | −0.0000332 | **FAIL** |
| control wf-v1-trigger | 0.6475 | 0.0025943 | 0.7749 | 0 | 0 | — |
| realizable ceiling | 0.6508 | 0.0026049 | 0.0005 | +0.0032 | +0.0000106 | diagnostic |

Frozen-gate outcomes (holdout):

- **O1 (quality arm): FAIL** — quality −8.2pp vs v1. Root cause (measured, dev in-sample diagnostic reproducing 0.5566 ≈ printed 0.5567): the probe's "safe" rows are only 42.7% weak-correct (vs 21.7% base) while its "risky" rows are hard for BOTH models (strong only 20–28% correct there). Escalating the risky rows buys strong's failures, not repairs; the weak tier's recoverable mass sits on rows v1 already routes strong.
- **O2 (cost arm): FAIL** — meets the quality bar by +0.1pp (inside noise: CI [−0.0009,+0.0030]) but costs **+27.6%** per row (esc_share 0.993 — the balanced-weight probe marks 99% of rows risky at τ_c).
- **O3: FAIL** (same failure mode as O1 at v1's coverage).
- **Control check:** the weak-first cascade with v1's own trigger EQUALS v1 (it is v1's partition re-serialized) — so no answer-aware trigger beats the control either.
- Capture of the realizable ceiling lift: O1 −2550%, O2 28.6%, O3 −2521% — none reaches the frozen 50% bar with non-positive cost delta.

## Verdict

**P3: KILLED under the frozen gate.** Answer-aware signals extractable from stored weak responses (shape + verifier outputs, with or without the prompt-side P) rank weak-failure with OOF AUROC 0.67–0.74 but cannot convert that ranking into cascade economics **on top of v1**, because:

1. v1's prompt-side signal and the answer-side signal are nearly redundant (P-conf alone carries most of R+V+P's lift: AUROC 0.6924 → 0.7385);
2. v1's weak-side rows are a "both models fail" stratum — nothing to rescue;
3. the weak-first frontier (P1-a: 0.7148 @ $0.00154) is architecturally unreachable by a v1-anchored trigger — reaching it requires a new preregistered weak-first router with a runtime trigger better than disagreement/verifier gating (both already killed in Phase C).

Per mission §14 (kill rules) and §17 (no retuning after a failed gate): the answer-aware trigger family is **KILLED for this corpus/architecture**. Conditional revival requires either (a) per-token log-probs / hidden states (not present in this corpus; would need paid generation or a different dataset), or (b) a weak-first architecture prereg where the trigger competes against the naive disagree/verifier gates instead of against v1's already-optimal prompt-side signal.

## Honest bookkeeping

- Prereg C-grid {0.03, 0.3, 3.0} was fully evaluated (12 CV cells) and C=3.0 selected on dev-fit — no post-hoc deviation (an earlier draft collapsed the grid to one C before running; the committed version honors the grid).
- Two crashed runs (array-shape and mask-shape bugs) died BEFORE the holdout section in one and before SECTION 3 in the other; no holdout results were consumed from a crashed run. The final complete run is the single holdout pass. One reporting-only defect (escalated-share printed full-length instead of surface-length in two dev-side ceiling lines) was fixed before the final complete run.
- Selection + freeze all occurred on dev-fit; thresholds never moved after holdout scoring.
