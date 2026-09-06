# PREREG-P6 — failure-focused cheap-tier uplift: MINING stage

**Frozen BEFORE any scoring.** Protocol: `experiments/PIVOT_PROTOCOL.md`.
Spend $0 (stored responses; no SPEND_GO — training stage out of mission scope,
prereg-disclosed). Test SEALED (never loaded). Validation untouched.

## Scope decision (frozen)

P6's full loop is: mine failures → LoRA/QLoRA the weak model → re-evaluate.
Training requires paid GPU runs, so **this mission executes the mining +
economic-ceiling stage only**; the training stage is handed off as a
specification (below). No routing decision may be inferred from semantics
(mission rule: semantics for failure clustering/analysis, not direct routing).

## Frozen questions

1. How many v1-weak failures on train-safe data have real repair signal
   (strong model correct where weak failed) vs the both-fail structural
   stratum (no signal, P3 finding)?
2. What fraction of the repair-signal rows are *recurring* (same normalized
   prompt template, ≥2 occurrences) — i.e. patterned rather than idiosyncratic?
3. What is the **perfect narrow-uplift ceiling** under the unchanged v1 stack:
   if every mined pair were repaired into the weak model, what accuracy gain
   results, and what escalation savings? (Hypothesis from P3/P4: the gain is
   the ~0.3–0.4pp realizable ceiling found there; v1 escalation savings are
   structurally zero because v1's trigger is independent of weak failures.)
4. Clusterability (analysis only): share of mined rows in families with ≥20
   rows and within cosine 0.55 of their family centroid — curriculum-feasible
   mass for the training handoff.

## Keep gate (frozen) — for the TRAINING HANDOFF, not this mission

The training stage is justified only if the mined curriculum projects a
weak-model accuracy gain of ≥ +0.020 standalone at training cost ≤ 2× the
projected 12-month escalation savings. This gate is evaluated by a future
prereg with SPEND_GO; this mission only reports the ceiling inputs.

## Handoff specification (training stage, out of mission scope)

Curriculum = mined pairs (weak prompt, strong correct answer), replayed with
≥3× previously-solved easy examples (mission replay-mixture rule), LoRA on
mistral-7b-chat, 3 seeds, ≤5k-pair controlled volume, eval on dev-fit
families + regression check on weak-correct rows.

## Anti-leakage / integrity

Mined pairs come from the TRAIN split only (dev-fit subset for analysis);
mining uses correctness + prompt templates, never validation/test rows;
embedding model runs on CPU with cached weights ($0). Pivot holdout may be
reported descriptively for stratum sizes but the mining set is dev-fit only.

## Deliverable

`results/P6_WEAK_UPLIFT.md`, `results/p6_mining_summary.json`, ledgers,
MISSION_LOG, and the mission-level final recommendation
(`PIVOT_FINAL_RECOMMENDATION.md`).
