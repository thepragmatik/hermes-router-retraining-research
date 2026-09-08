Idea 107 Stage 0 — corrected analysis note.

The initial selection run chose {weak, Yi, gpt-3.5} because the frozen G1 clause
"all-called portfolio cost <= 2x best single" is trivially satisfied by any
cheap-pool subset, and gpt-3.5-turbo's conditional-rescue structure over Yi is
nearly symmetric (P(yi ok | gpt3.5 fail) = 0.2823 vs P(gpt3.5 ok | yi fail) = 0.2221),
so the optimizer found a cheap triad with oracle quality 0.6683 (>= 2pp over the
best single model gpt-4-1106-preview at 0.6429).

Sanity check (experiments/107/sanity_sel.py) shows the oracle-quality-optimal
3-subset is {weak, Yi, gpt-4-1106-preview} at oracle 0.7283, +8.54pp over the best
single model at all-called cost 0.003520 = 1.07x the best single model's cost —
a strictly larger quality gain at a still-gate-compliant cost ratio.

The G1 gate does not say "pick the cheapest passing subset"; it says the portfolio
must improve oracle attainable quality by >= 2pp at <= 2x cost (or cut cost >= 15%
at matched quality). Under the spec's optimization objective (maximize attainable
quality subject to the size/cost constraint), the oracle-optimal subset is the
correct selection; the earlier cheap-pool pick maximized a different (unstated)
economic objective. Selecting {weak, Yi, gpt-4-1106-preview}:
  - still passes G1 (+8.54pp at 1.07x cost);
  - passes G2 marginal gates (computed in stage0_results.json under G2 alt);
  - changes the realizability picture: the fixed per-task policy captures 0.5306 of
    oracle quality vs best-single 0.6482, i.e. below the single model — so simple
    runtime signals do not realize the pool's oracle gain.

This note is a correction of the selection step toward the frozen objective, made
before any verdict was issued; gates themselves are unchanged.
