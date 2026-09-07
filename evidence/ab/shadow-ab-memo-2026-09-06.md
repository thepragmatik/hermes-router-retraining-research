# Shadow A/B impact memo — 007 (2026-09-06)

**Question:** what does the frozen V1 router (threshold 0.30) actually buy the
stack, versus not using it? **Method:** replay of RECORDED per-row outcomes on
`mf_val_frame.parquet` (n=3626) — zero API spend, zero model calls in the A/B
itself (router decisions cached once in `evidence/ab/val_decisions.npz`).
Prereg: `experiments/007-shadow-ab-prereg.md`, frozen BEFORE the eval run.

## 1. Acceptance table (prereg A1–A7)

| Gate | Spec | Result | Verdict |
|---|---|---|---|
| A1 | replay reproduces frozen point: \|acc−0.6395\|<=0.0002 and \|frac_strong−0.7686\|<=0.0002 | acc 0.6395477109762824 (Δ 0.0000477), frac_strong 0.7686155543298401 (Δ 0.0000156) | PASS |
| A2 | bootstrap CI low of H1 (router vs always-weak) > 0 | CI [0.3927, 0.4286], low 0.3927 > 0 | PASS |
| A3 | bootstrap CI low of H2 (router vs random cost-parity) > 0 | CI [0.2201, 0.2507], low 0.2201 > 0 | PASS |
| A4 | headroom = oracle_acc − acc(A), reported | 0.0378 | reported |
| A5 | HTTP warm p95 < 0.5 s; CLI-enabled mean > 5× in-process mean; CLI-disabled mean < 1 s | 0.0158 s; 7.276 s vs 0.0186 s (391×); 0.041 s | PASS |
| A6 | chaos: 4/4 checks match specified behaviour | 4/4 PASS (`chaos_checks_2026-09-06.md`) | PASS |
| A7 | sha256(mf_test_frame.parquet) unchanged Task 0 → Task 8 | identical (§5) | PASS |

`shadow_ab_results.json` → `"acceptance"` verbatim:

```json
{"A1_replay_matches_frozen": true, "A2_ci_low_vs_always_weak_gt0": true,
 "A3_ci_low_vs_random_parity_gt0": true, "A4_headroom_oracle_minus_router": 0.0378}
```

A2 and A3 both PASS: no negative-result statement is required by the prereg.

## 2. Impact table (arms A–E, n=3626; values verbatim from shadow_ab_results.json)

| Arm | acc | frac_strong | cost_mean (per row) | 95% CI (paired bootstrap, Δacc vs A) |
|---|---|---|---|---|
| A router_v1_030 | 0.6395477109762824 | 0.7686155543298401 | 0.0014418713734142305 | — |
| B always_strong | 0.6447876447876448 | 1.0 | 0.0032632570325427466 | [−0.008, −0.0025] (acc) |
| C always_weak | 0.2289023717595146 | 0.0 | 4.517854384997242e-05 | [+0.3927, +0.4286] (acc) |
| D random_parity (target frac 0.434, seed 42) | 0.4040264754550469 | 0.43408714837286266 | 0.0014106532818532822 | [+0.2201, +0.2507] (acc) |
| E oracle (ceiling, not achievable) | 0.6773303916161059 | — | — | — |

Hypotheses (paired bootstrap, 10000 resamples, seed 42):

- **H1 router vs always-weak:** +0.410645 acc, CI [0.3927, 0.4286] — CI low > 0. PASS.
- **H2 router vs budget-matched random:** +0.235521 acc, CI [0.2201, 0.2507] at
  matched cost (Δcost 3.12e-05/row, +2.2% vs D) — CI low > 0. PASS. The router's
  value is the *selection*, not the budget: a seeded random policy spending the
  same money reaches only 0.4040.
- **H3 router vs always-strong (reported, not gated):** −0.00524 acc, CI
  [−0.008, −0.0025], for **55.81% lower cost** (0.0014419 vs 0.0032633 per row).
  On val, the router retains ~99.2% of always-strong accuracy at ~44% of its cost.
- **Headroom (A4):** oracle 0.6773 − router 0.6395 = **+0.0378 acc** — the
  bound on any better trigger on this substrate.

Limitation: D uses mean costs (no variance modeling) — adequate for replay,
noted per prereg.

## 3. Latency under the three wirings (latency_bench.json, verbatim)

| Wiring | n | p50 | p95 | mean |
|---|---|---|---|---|
| in-process `route()` | 100 | 0.0186 s | 0.1014 s | — |
| CLI subprocess (enabled) | 5 | — | — | 7.276 s |
| CLI subprocess (disabled) | 5 | — | — | 0.041 s |
| HTTP service (localhost) | 20 | 0.0094 s | 0.0158 s | — |

**Wiring implication:** CLI-per-call reloads the model every invocation
(7.276 s mean ≈ 391× the in-process p50, ≈ 774× the HTTP p50). Any stack
integration must use the HTTP service (or in-process import); CLI-per-prompt is
operationally non-viable. The kill switch adds ~0.04 s via the disabled CLI
path and ~0.01 s per HTTP request — negligible.

## 4. Threshold sweep — 0.30 row (threshold_sweep.csv, VERBATIM)

```
0.3,0.6395477109762824,0.7686155543298401,0.0014418713734142305,3626
```

Equals arm A exactly (0.6395477109762824 acc, 0.7686155543298401 frac_strong).
**Sweep is analysis-only; deployed threshold remains frozen at 0.30.**
(Sweep shape: acc is monotone-ish in [0.05, 0.30], peaks 0.6456 at 0.05–0.10 at
+~1.5% cost, and collapses toward always-weak 0.2289 above 0.85 — the frozen
point sits on the knee, trading ~0.6pp acc vs threshold 0.05 for 7% lower cost.)

## 5. Sealed-split integrity (A7)

```
$ shasum -a 256 ~/transfer-bundle/analysis/mf_test_frame.parquet > /tmp/testframe_sha_after.txt
$ diff /tmp/testframe_sha_before.txt /tmp/testframe_sha_after.txt && echo SEALED_OK
SEALED_OK
```

Hash line (Task 0 == Task 8, byte-for-byte):
`e938142c835b27bc13c7633745c4631fa4336dbe067d8d3b5a41dafa9f389bd1  ~/transfer-bundle/analysis/mf_test_frame.parquet`
The sealed test split was never read; only hashed.

## 6. In-sample caveat (from the prereg, verbatim)

> Status of val w.r.t. threshold 0.30: IN-SAMPLE (threshold frozen on val) — deltas are
> upper bounds on out-of-sample impact; stated as such in the memo.

All deltas above are on the val frame the threshold was frozen on, so they are
**upper bounds on out-of-sample impact**. The gated live leg
(`experiments/007_live_ab.py`, SPEND_GO=1-gated) exists to spot-check live
agreement and was deliberately NOT run today.

## Artifacts

- `evidence/ab/shadow_ab_results.json` — arms, CIs, acceptance flags
- `evidence/ab/threshold_sweep.csv` — 19 thresholds, 0.05→0.95
- `evidence/ab/val_decisions.npz` — cached per-row decisions + confidences
- `evidence/ab/latency_bench.json` — wiring latency
- `evidence/ab/chaos_checks_2026-09-06.md` — kill-switch checks 4/4
- Commits: prereg dc93803 · harness 27fba9c/e4a4d52 · replay 3b74248 ·
  latency 11a0214 · chaos 863cd80 · gated live draft c9a6d88
- Spend: $0.00
