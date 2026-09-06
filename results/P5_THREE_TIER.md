# P5 — Three-tier / specialist cascade (weak → mid → frontier)

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P5.md` (frozen `f3837b8`, before scoring) · Script: `experiments/p5_three_tier.py` · Raw: `results/P5_raw.txt`

**Setup:** with every dynamic trigger dead (P1b/P1c/P2/P3/P4), the only untested lever is the escalation ladder's shape. Per prereg, arms act on the v1-WEAK stratum; reference C1 = v1 @0.30 (dev acc 0.6400 @ $0.0025682/row). Mid tier = Yi-34B-Chat by P0 complementarity (repairs 47.0% of weak fails at 4.05× weak cost) — not globally-strongest heuristics.

## Dev-fit arms (frozen gates vs C1: G1 cost −$0.0002 @ acc ≥ −0.002; G2 acc +2.0pp @ cost ≤ +$0.0002)

| arm | acc | cost/row | d_acc [95%] | d_cost [95%] | gate |
|---|---|---|---|---|---|
| C2a weak→Yi→strong, oracle arbiter | 0.4862 | 0.0019302 | −0.1538 [−0.1583,−0.1495] | −0.0006380 | FAIL both |
| C2b weak→Yi, no strong (deployable) | 0.5301 | 0.0002232 | −0.1099 [−0.1155,−0.1046] | −0.0023450 | FAIL both |
| C3 weak+Yi everywhere, strong iff both wrong (oracle) | 0.7080 | 0.0015987 | +0.0680 [+0.0651,+0.0711] | −0.0009695 | **PASS both** |

C2a collapses because inserting Yi *before* strong on v1-weak rows swaps a 5.5%-correct strong answer for a mid answer most of the time — the oracle only escalates when Yi is right, which it usually isn't where it matters. C2b shows pure weak+Yi service is 11pp below v1 at low cost. C3's value comes almost entirely from the oracle "strong iff both wrong" selection — numerically it reproduces the P1a oracle-pair ceiling (+6.7pp at −39.8% vs v1; C3: +6.8pp at −38%), i.e. adding the mid tier adds nothing the pair oracle didn't already contain.

## Holdout (single pass, C3 only, per prereg)

C3_always3_oracle: acc **0.7148** (+0.0672 [+0.0594,+0.0748]), cost **0.0015814** (−0.0010129 [−0.0010869,−0.0009397]) — G1 PASS, G2 PASS.

**Status: ORACLE UPPER BOUND, not deployable.** The prereg states this explicitly: C3's "strong iff both wrong" step uses stored correctness — a perfect mid-tier arbiter. The mission question it answers is economic: *does a mid tier pay under perfect arbitration?* Yes — but the arbiter does not exist on this corpus: all four deterministic verifier families failed the 0.90 precision gate (P2, best 0.67), the answer-aware probe failed all three arms (P3), and no surviving trigger exists (P4). Under any real trigger the cascade degenerates to C2b (−11pp) or C2a (−15pp).

## Verdict

**P5 keep gate: the mid tier survives ONLY under a perfect arbiter; with all real triggers dead (P4), no deployable three-tier cascade exists.** The qualified routing configuration remains v1 @0.30 alone (holdout acc 0.6475 @ $0.0025943/row). The measured oracle bound (+6.7pp at −39% cost) is real headroom in the model pool, but realizing it requires a capability this corpus cannot supply (a reliable correctness arbiter) — the same revival condition recorded in P2/P3 (machine-checkable contracts, logprob-bearing corpus, or paid generation for a trained arbiter).

Ledgers: frontier +3 (C2a/C2b dev, C3 dev+holdout as recorded), component_effects +1, MISSION_LOG updated.
