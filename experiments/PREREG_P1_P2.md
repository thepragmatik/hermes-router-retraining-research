# Preregistration — Phase C: P1 adaptive cheap sampling + P2 deterministic verifiers

**Frozen before any policy scoring on the pivot surface. 2026-09-06. Spend: $0.**
Protocol basis: `experiments/PIVOT_PROTOCOL.md` (frozen). Data: train split only
(29,193 rows). Test split SEALED (asserted, never loaded). Historical validation
split NOT touched in this phase.

## Development surface

Pivot holdout: seed 42, `int(md5(f"42:{prompt}")[:8], 16) % 10000 < 1500` over
train rows = 4,358 rows (14.93%); the remaining 24,835 train rows are the dev-fit
surface. The mask is deterministic across runs/machines. No threshold, verifier
rule, or stack parameter may be selected on the pivot holdout before this
preregistration is frozen — selection happens on dev-fit only; the holdout is
scored ONCE per preregistered policy at the end of the phase.

## P1 — adaptive cheap sampling (stored-label simulation, $0)

The 0-shot pool stores exactly one response per model per row, so repeated
sampling from one model is NOT simulable. Preregistered P1 variants (per mission
§P1, feasible subset):

- **P1-a heterogeneous pair (weak + Yi-34B):** accept weak's answer iff
  `weak_correct == 1`; else if `yi_correct == 1` accept Yi (simulating
  "second cheap sample repairs"); else escalate to strong. Oracle-pick variant —
  the acceptance signal is correctness itself, so P1-a is an UPPER BOUND
  diagnostic, not a deployable policy (deployable requires a runtime-visible
  trigger, measured in P1-b/c).
- **P1-b disagreement-triggered escalation:** answer weak and Yi; if they agree
  (exact answer-string match after normalization) accept weak's answer;
  if they disagree escalate to strong. Runtime-visible; deployable.
- **P1-c verifier-gated pair:** weak's answer accepted iff it passes the P2
  deterministic verifier (defined below); else Yi's answer if IT passes; else
  escalate to strong. Runtime-visible; deployable.
- **P1-d adaptive frontier-call simulation:** for each variant, report
  frontier-call rate and total cost/row = Σ per-tier stored costs of calls made.

### P1 measures (mission §P1)

quality vs N (N=1 weak, N=2 pair); P(additional sample repairs first answer)
= P(yi ok | weak fail); P(confident co-failure) = P(weak & yi both wrong AND
agree); agreement→correctness calibration (P(weak ok | weak==yi) with Wilson 95%
CI); frontier calls avoided vs always-strong; task-family heterogeneity (quality
delta by eval_name prefix, min cell 50); cost/row with per-call stored costs.
All policies scored on dev-fit AND the frozen holdout (one pass each).

### P1 keep gate (frozen)

Keep a P1 variant only if, on the pivot holdout, it improves end-to-end
**quality at ≤ matched cost/row** relative to router v1's train-side operating
point, or reduces **cost ≥ 5% relative at ≥ matched quality** (mission §4
materiality). Marginal value is measured OVER v1 composition (P4), so P1's
standalone gate is frontier movement vs the P0 naive cascade and vs v1.

## P2 — deterministic verifiers ($0, applied to stored responses)

### Feasible families on this corpus (task semantics check done on dev-fit only)

1. **answer-format extraction check** (all families): the stored response must
   contain an extractable answer under the family's canonical pattern —
   GSM8K-style "#### <number>", MMLU/Arc/Winogrande-style "letter is X"/"(X)",
   Hellaswag-style non-empty ending selection. A response with no extractable
   answer fails the check (abstain allowed → treated as fail).
2. **schema/JSON validity** where the response contains fenced JSON (rare;
   measure coverage, expect <2%).
3. **Python-executable answer cell** for mbpp (exec the stored snippet against
   the prompt's assert if present in the prompt text; else structural checks
   only — compile() success + function definition presence).
4. **numeric recomputation** for GSM8K: recompute the final "#### N" value by
   eval of the response's own arithmetic steps is NOT possible (no stored
   reasoning-chain ground truth) — therefore numeric recomputation is limited
   to self-consistency of the extracted number (regex-integer parse + range
   sanity), recorded as a WEAK verifier with its measured precision.

### P2 measures (mission §P2)

per verifier: coverage (fraction of rows where the verifier returns a verdict),
precision of accept decisions P(weak ok | verifier accept), false-accept rate
P(weak wrong | accept), false-reject rate P(weak ok | reject), and frontier
calls avoided in the P1-c cascade. Task-family breakdown for the top-5 families.
**Verifier quality is never judged by AUROC — only by the cascade's end-to-end
quality/cost movement** (mission §7).

### P2 keep gate (frozen)

A verifier family is retained only if its accept-precision on dev-fit ≥ 0.90
AND coverage ≥ 5% of rows (below either bar it cannot move the frontier
materially at near-zero cost). The composed P1-c policy must beat P1-b
(disagreement) on the holdout to justify the verifier's complexity (mission
§14 kill rule: gain must survive composition with a simpler layer).

## Falsification risks (declared in advance)

- P1-b string-agreement may be dominated by format artifacts (both models
  emitting the same wrong format counts as agreement); the co-failure
  agreement rate is measured explicitly to size this.
- P1-a's oracle acceptance overstates any deployable pair policy; it is a
  ceiling diagnostic only and must not be cited as a keepable policy.
- Stored 0-shot responses may include few-shot artifacts (response wrapped as
  a Python list string: `['...']`); all extraction normalizes this wrapper
  before parsing, and the wrapper-normalization is tested on dev-fit first.
- Verifier precision measured on train-family mix may not transfer to
  deployment mix; task-family table is reported so any adoption decision can
  weight the Hermes-relevant families explicitly.

## Scoring plan

1. Dev-fit: select the ONE agreement rule, ONE verifier configuration, and any
   thresholds using dev-fit rows only.
2. Freeze this file's operating points (recorded in the results doc BEFORE
   holdout scoring).
3. Score each preregistered policy ONCE on the pivot holdout.
4. Report `results/P1_CHEAP_SAMPLING.md` + `results/P2_VERIFIERS.md` with
   frontier/component ledgers updated; commit; boundary report; STOP.
