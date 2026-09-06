# PIVOT FINAL RECOMMENDATION — Stackable Routing Mission

**Date:** 2026-09-06 · **Outcome declared: `ROUTING NOT ECONOMIC` (promotion decision E)** · Spend $0.00 of $5.00 cap · Sealed test split never loaded · Repo HEAD at close: see git log

## The outcome in one paragraph

Across seven preregistered experiment families (P0–P6), no deployable routing
or cascade component beat the frozen V1 router's simple rule on this corpus.
Every dynamic layer failed its frozen gate on both architectures (P1b/P1c/P2/
P3/P4), the three-tier cascade pays only under a perfect correctness arbiter
that this data cannot supply (P5), and the mined curriculum for cheap-model
uplift is too small to matter (P6). The mission's own success criterion —
marginal frontier movement per layer — was never met by any candidate layer.
Per mission §15 this is outcome E: recommend the simplest fixed policy
supported by evidence, which is V1 itself.

## Final operational artifact

**V1 @ threshold 0.30** (tag `router-v1-frozen`, commit `7e8a7be`,
`router_v1/route.py` + `mf_router.pt`): BGE-small embeddings → MF head →
P(strong) ≥ 0.30 routes to gpt-4-1106-preview, else mistral-7b-chat.
Pivot-holdout: accuracy **0.6475** at **$0.0025943/row**, 77.5% strong share,
PGR 0.9874, APGR 0.6459 (vs always-strong 0.6459 APGR at ~78× the weak-tier
cost on the weak share). Reproduced exactly by `experiments/b1_baseline_repro.py`.

## Revival conditions (evidence-recorded, not speculative)

The +6.7pp / −39% oracle headroom in the model pool is real and
holdout-confirmed (P5 C3) but requires a capability absent from this corpus:

1. A reliable answer-correctness arbiter (P2 best verifier precision 0.67 vs
   the required 0.90; P3's probe and P4's stack both failed on the same
   weakness). Revival path: a corpus with logprobs/hidden states, machine-
   checkable answer contracts (code with asserts, math with verified keys),
   or paid generation of a trained arbiter — under a NEW prereg.
2. Any model-pool change that moves the both-fail stratum (98.3% of v1's
   weak-routed failures are both-models-fail; P3/P6). A better weak or mid
   model re-runs P0 → P5 under a new prereg.

No other lever exists on this data: this is why the outcome is E and not B
(PARTIAL STACK) — a partial stack needs at least one paying deployable layer,
and there are none.

## What was measured (all frozen preregs, single holdout passes, $0 spend)

See the table in MISSION_LOG.md and the per-phase documents:
`results/P0_MODEL_POOL.md` … `results/P6_WEAK_UPLIFT.md`,
`results/frontier.csv` (22 operating points), `results/component_effects.csv`
(13 layer decisions), `results/error_overlap.csv`.

## Discipline statement

- 7 preregistrations frozen and committed BEFORE any holdout scoring.
- 2 voided passes total (Phase C harness bugs), both dev-side, both disclosed.
- 0 threshold movements post-hoc; failed gates killed layers, never retuned.
- Validation split untouched (finalists-only reserve); sealed test split
  loaded 0 rows across the entire mission (3678-row membership assert only).
- Total spend $0.00; no SPEND_GO issued; no external calls.
