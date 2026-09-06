# Prereg 007 — Shadow A/B replay impact study (2026-09-06)

Substrate: mf_val_frame.parquet (n=3626, RECORDED outcomes; zero API spend).
Sealed split: mf_test_frame.parquet must not be read (integrity = sha256 match, Task 0 vs Task 8).
Status of val w.r.t. threshold 0.30: IN-SAMPLE (threshold frozen on val) — deltas are
upper bounds on out-of-sample impact; stated as such in the memo.

Arms (policy → decision per row):
  A router_v1_030:     route() decision (frozen threshold 0.30, cached)
  B always_strong:     strong for all rows
  C always_weak:       weak for all rows
  D random_parity:     seeded random (seed 42) with frac_strong chosen so mean cost
                       matches arm A (cost_parity_frac)
  E oracle:            per-row max(strong_correct, weak_correct) — ceiling, not achievable

Metrics per arm: acc, frac_strong, cost_mean, n.
Primary comparisons (paired bootstrap, 10000 resamples, seed 42, percentile CI):
  H1: acc(A) - acc(C) > 0            (router vs always-weak)
  H2: acc(A) - acc(D) > 0            (router vs budget-matched random)
  H3: cost(A) vs cost(B) at ~equal acc (cost saving vs always-strong, reported not gated)

Acceptance (frozen before eval run):
  A1 replay reproduces frozen point: |acc(A)-0.6395|<=0.0002 and |frac_strong(A)-0.7686|<=0.0002
  A2 bootstrap CI low of H1 > 0
  A3 bootstrap CI low of H2 > 0
  A4 headroom = oracle_acc - acc(A), reported
  A5 latency: HTTP warm p95 < 0.5 s; CLI-enabled mean > 5x in-process mean;
     CLI-disabled mean < 1 s
  A6 chaos: 4/4 checks match specified behaviour
  A7 sha256(mf_test_frame.parquet) unchanged Task 0 -> Task 8

If A2/A3 fail: record the negative result verbatim. Do NOT retune the threshold
(it is frozen by prereg); the finding "no measurable value over budget-matched
naive routing on val" is a legitimate outcome.
