# P0 — Model-pool audit (stored-label screening)

**Date:** 2026-09-06 · **Spend:** $0 · **Data:** frozen TRAIN split (29,193 rows; test SEALED, never loaded) · Script: `experiments/p0_model_pool_audit.py` · Raw output: `results/P0_MODEL_POOL_raw.txt` · Screen table: `results/p0_model_pool_screen.csv`

## Question

Is the historical weak tier (`mistralai/mistral-7b-chat`) still the right foundation, or is model choice now a bigger lever than routing sophistication?

## Headline answer (from stored labels only)

**No cheap candidate in the stored pool dominates the historical pair on any axis that matters end-to-end — but the audit materially reshapes the mid-tier question for P5.**

Key numbers (train split, stored labels/costs):

- weak acc **0.2167** @ \$0.000046/call · strong acc **0.6429** @ \$0.003289/call
- ceiling on single-tier rescue: P(strong ok | weak fail) = **0.5806**
- best stored rescuers of weak failures: claude-v2 (0.4763, but \$0.002417/call = 52.8× weak), **Yi-34B (0.4702 @ \$0.000186 = 4.05× weak)**, gpt-3.5-turbo (0.4602 @ \$0.000243)
- co-failure Jaccard vs weak is high everywhere (0.47–0.85): every stored model's failures correlate substantially with the weak model's failures — **no stored model is a silver-bullet complement**.

## Selection decision (per §P0 rules)

1. **Keep the historical weak tier as the primary cheap tier for P1–P4.** No stored candidate improves the frontier at the weak tier's price point, and the R5 router (tag `router-v1-frozen`) is trained for this exact pair — swapping now would invalidate the frozen baseline for zero measured gain.
2. **Carry Yi-34B-Chat forward as the candidate mid-tier / heterogeneous second sample for P1/P5**: it nearly matches claude-v2's rescue rate (0.4702 vs 0.4763) at 1/13th of claude-v2's cost (4.05× weak vs 52.8× weak), i.e. the best rescue-per-dollar in the pool by a wide margin.
3. **Drop code-llama-34b** (rescue 0.0125, Jaccard 0.8532 — duplicates weak failures while adding cost) and llama-2-70b (rescue 0.2017 < 1−acc of the weak tier itself, economically pointless as an escalation).
4. **Claude-v2 is NOT selected as mid-tier**: its rescue-per-extra-dollar is ~17× worse than Yi-34B; at \$0.0024/call it is 73% of the strong model's price while rescuing less than strong would (0.4763 < 0.5806) — direct-frontier use dominates it (kill rule §14).

## Naive-cascade sanity (no learned layer)

weak+Yi with disagreement→strong escalation: acc 0.5278, frac_strong 0.4219, cost/row \$0.001521, PGR 0.7299, savings 53.7%.
**This does NOT beat router v1** (val: acc 0.6395 @ \$0.001442, PGR 0.9874, savings 55.81%) on either axis — v1 stays Tier-0, and any P1–P5 layer must show marginal value over v1, not over this strawman.

## Error-overlap evidence (feeds `results/error_overlap.csv`)

Top complements to the weak model (lowest co-failure Jaccard) involve code-llama-34b, which is economically dead — confirming that low overlap alone is not selection criterion; complementarity must be per unit cost (§P0 selection rule).

## Caveats

- All figures are historical-model stored labels (2023-era pool). Current cheap models (e.g. DeepSeek-class, gpt-oss-class per `costs/model_prices.json`) are NOT in this audit; measuring them requires either free public stored results (DATASETS.md Tier B: LLMRouterBench) or paid calls (SPEND_GO-gated). This is logged as the open "pool currency" question for a follow-up screen, not silently assumed away.
- Costs are RouterBench-recorded historical prices — used for *relative* complementarity here; absolute frontier economics must use the current price snapshot when comparing to live deployment.

## Frontier rows added (train, stored-label simulation)

| policy | acc | cost/row | note |
|---|---|---|---|
| always_weak | 0.2167 | 0.0000458 | |
| always_strong_simulated | 0.6429 | 0.0032889 | |
| cascade_disagree_weak+Yi | 0.5278 | 0.0015213 | no learned layer |
| router_v1_tagged | 0.6395 | 0.0014420 | val-side, B1, tag `router-v1-frozen` |
