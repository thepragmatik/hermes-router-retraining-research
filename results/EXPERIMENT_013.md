# Experiment 013(+A) — Pair coherence of the rescue signal (results)

Prereg: experiments/013-pair-coherence-prereg.md + Amendment A
(experiments/013a-prereg-amendment.md, commit 5e19c0e). $0. Test SEALED.
The first run (wrong pair universe: 11 models, list-order roles) is VOID
per the amendment; this report covers the corrected run
(experiments/013a_pair_coherence.py): 9 non-control models, 36 pairs,
roles assigned on D1 by higher D1 accuracy. Both half-splits n = 18,177.

## Results

Selected on D1 (frozen before D2):

| Pair (weak → strong) | rescue D1 | rescue D2 |
|---|---|---|
| code-llama-34b → Yi-34B | 0.4448 | 0.4441 |
| code-llama-34b → gpt-3.5 | 0.4375 | 0.4359 |
| code-llama-34b → claude-v2 | 0.4326 | 0.4288 |
| claude-instant → claude-v2 | 0.1099 | 0.1057 |
| claude-instant → claude-v1 | 0.1032 | 0.0978 |
| claude-v2 → claude-v1 | 0.0872 | 0.0860 |

D2 top-3 mean 0.4362 vs bottom-3 mean 0.0965; **lift +0.3398**;
order preserved 6/6; n_d2 = 18,177 per pair.

## Verdict (declared vocabulary)

**PAIR-COHERENCE COHERENT** (all three prereg conditions met).

## Interpretation (scope frozen by the prereg)

1. Rescue structure is substantially a property of the MODEL PAIR: a
   code-llama weak arm is rescued 43–44% of the time by mid-tier strong
   arms, while same-family Claude pairs rescue <11%. The gap replicates
   across disjoint halves (D1/D2 deltas < 0.005 everywhere).
2. Mechanism is transparent: the weakest model in the pool (code-llama,
   D1 acc 0.105) fails so often that even modest strong arms rescue a
   large fraction; same-family pairs have highly overlapping failure
   sets, so rescue is structurally rare. Top pairs have BOTH high weak
   failure AND low failure overlap.
3. Per the frozen claim scope, this is PRE-REGISTRATION VALUE only: it
   says the next paid study, if any, should be a PAIR-COMPARISON study
   (a good weak arm is one whose failures the strong arm can fix —
   failure-diversity matters more than weak-arm accuracy). It does NOT
   claim label availability causally explains 003/009, and it does NOT
   change the KEEP-V1 decision: rescue rate is not routing quality, and
   the mission pair's problem (weak arm too weak, rescue prompt-
   idiosyncratic) was already closed at the router-quality level.

## Exposure note (per amendment)

code-llama→Yi and llama-2→Yi D2 values were seen in the VOID run; the
other four selected pairs' D2 values are fully held-out observations.
Order and lift conclusions do not depend on the exposed pairs
(removing both: top-3 mean 0.4324, lift +0.3365 — unchanged).

## Recommendation impact

KEEP V1 unchanged. Adds one operator decision item: a paid pair-comparison
study (~$11 for 10k gpt-4o-era labels) is now the highest-value next
experiment IF the operator wants to pursue the flywheel with a modern
pool. Recorded in IDEAS.md; not executed (over $5 mission cap).
