# P6 — Failure-focused cheap-tier uplift: MINING stage

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P6.md` (frozen `3715f34`, before scoring) · Script: `experiments/p6_weak_uplift_mining.py` · Raw: `results/P6_raw.txt` · Summary: `results/p6_mining_summary.json`

**Scope (prereg-disclosed):** P6's training stage (LoRA on the weak model) requires paid GPU runs — out of mission scope at $0 with no SPEND_GO. This phase executes the mining + economic-ceiling stage and hands off a training specification. Two harness bugs were caught and fixed before results were trusted: a v1-mask cast bug (`np.asarray(probs, dtype=bool)` makes every nonzero prob True → zero mined pairs, caught because SECTION 1 printed an impossible 0/0 stratum) and a stratum-label inversion in the first run (mined set larger than total v1 dev errors — caught by the sanity check that mined pairs must be a subset of v1's dev errors). Final run EXIT=0 with all cross-checks consistent.

## Findings (dev-fit)

1. **v1-weak failures are 98.3% both-fail stratum.** Of v1's dev failures on weak-routed rows: 5,420 rows are weak-fail AND strong-fail (98.30%), only **94 rows** (1.70%, 0.38% of dev) have repair signal (strong correct where weak failed). This confirms and sharpens the P3 structural finding on the train-safe stratum: the weak model's failures under v1 are concentrated where the frontier model also fails — there is almost nothing to mine.
2. **Mined pairs are idiosyncratic, not patterned.** Only 4 recurring prompt templates (≥2 occurrences) cover 37 of the 94 mined pairs; no family reaches the ≥20-row clusterable threshold (largest: bias_detection 17, mbpp 17). Semantic clustering shows the pairs are near their family centroids (0.915 mean coverage) but the families themselves are too small to form a curriculum.
3. **Perfect narrow-uplift ceiling under the unchanged v1 stack: +0.0038 accuracy** (94 rows repaired, 0.6400 → 0.6438) — matching the P3 realizable-ceiling estimate of +0.3–0.4pp. **Escalation savings: $0** — v1's trigger is independent of weak failures; any savings would accrue only to weak-first stacks, which P4 killed.

## Verdict

**P6 keep gate (≥ +2.0pp projected weak uplift at justified training cost): FAIL by an order of magnitude.** The mined curriculum is 94 rows with no recurring pattern mass and a +0.38pp ceiling under perfect repair. Mining-based cheap-tier uplift cannot pay on this corpus; the LoRA training handoff is **not justified** by these inputs (the preregistered training gate required ≥ +2.0pp projected). P6 closes as a negative result: the "convert rescues into cheap capability" lever has no material to work with — the weak model's residual failures under v1 are the both-models-fail stratum.

Ledgers: frontier +1 (mining ceiling), component_effects +1, MISSION_LOG updated.
