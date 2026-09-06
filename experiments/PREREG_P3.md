# Preregistration — Phase D: P3 answer-aware internal confidence

**Frozen before any policy scoring on the pivot surface. 2026-09-06. Spend: $0.**
Protocol basis: `experiments/PIVOT_PROTOCOL.md` (frozen). Data: train split only
(29,193 rows). Test split SEALED (asserted, never loaded). Historical validation
split NOT touched in this phase.

## Question (mission §P3)

Does the weak model contain useful runtime-visible reliability information after
answering that the prompt-only router (v1) could not see — enough to serve as the
escalation trigger of the weak→strong cascade, capturing the P1-a oracle headroom
(+6.7pp acc / −39.8% cost vs v1, Phase C)?

## Feasibility declaration (corpus limitation)

RouterBench-0shot stores exactly one TEXT response per model per row: no per-token
log-probabilities, no hidden states, no latency. The "true internal" signal family
(log-prob summaries, entropy/margin, frozen hidden states, prompt-embedding+hidden
probes) is **NOT FEASIBLE AT $0 on this corpus** and is explicitly not claimed as
tested. Feasible answer-aware signals, all derived from the weak model's own stored
response text (plus the prompt via v1's cached P(strong)):

1. **R-shape** — response length (log1p), ends-with-number, code-fence marker,
   hedging regex (sorry/cannot/unable/as-an-ai), digit-group count, short-answer flag.
2. **V-out** — Phase C verifier outputs on the weak response: VF answer-extraction
   accept, VN numeric sanity (gsm8k), VM structural compile (mbpp).
3. **P-conf (baseline only)** — v1's cached P(strong) (prompt-side signal; the
   thing answer-aware signals must complement/beat).

## Leakage guards (hard)

- Features use ONLY: weak model's stored response text, eval_name family, and v1's
  cached P(strong). An audit assertion prints at run start.
- NEVER used as features: any model's correctness value, any model's total_cost,
  oracle_model_to_route_to, any other model's response.
- The risk target y = 1[weak_correct == 0] is used only for fitting/evaluation,
  never as a feature.

## Development surface

dev-fit = 24,835 train rows (pivot holdout = seed-42 md5 bucket < 1500, mask
unchanged from Phase C). Feature design, C selection, calibration, and ALL
thresholds are selected on dev-fit only, via 5-fold CV over deterministic
md5-bucket fold blocks (3 hash salts for fold-assignment stability, per mission
§7 multiple-seeds rule). The pivot holdout is scored ONCE at the end on the
frozen operating points.

## Probe (frozen candidate set)

- Model: L2 logistic regression (sklearn pipeline: StandardScaler → Logistic),
  class_weight="balanced", C grid {0.03, 0.3, 3.0}, max_iter 1000.
- Feature sets compared on dev-fit OOF AUROC (diagnostic) AND OOF cascade
  economics (selection): [R-shape], [V-out], [R+V], [R+V+P] (last one to test
  complementarity with the prompt-side signal).
- Selection rule: choose the feature set × C by dev-fit OOF cascade quality at
  ≤ v1 cost (mission §P3: select by cascade economics, not AUROC).
- Final frozen probe = refit on full dev-fit at the selected (features, C).
  Thresholds τ below are read off the dev-fit OOF risk curve (declared, minor
  refit-optimism accepted; the holdout is the guard).

## Frozen operating points (all selected on dev-fit, scored ONCE on holdout)

- **O1 quality trigger:** escalate (call strong, ship its outcome) iff p_risk ≥ τ_q,
  τ_q = OOF threshold maximizing cascade quality subject to cascade cost/row ≤
  v1's dev-fit cost/row. Otherwise ship weak's outcome.
- **O2 cost trigger:** τ_c = OOF threshold minimizing cascade cost subject to
  cascade quality ≥ v1's dev-fit quality.
- **O3 coverage-matched:** escalate on the riskiest rows up to v1's dev-fit
  strong-share (architecture-neutral, strong-share-matched comparison).
- **Control arm wf-v1-trigger:** weak-first cascade escalating iff v1 P(strong) ≥
  0.30 (frozen) — isolates the architecture confound (weak-first vs prompt-side
  routing) from trigger quality. P3's trigger must beat THIS arm, not only v1-as-is.
- **Baselines:** v1@0.30 (frontier benchmark); VF-accept trigger (Phase C result).
- **Realizable oracle ceiling (operator-frozen definition, 2026-09-06):** the
  policy that keeps v1's decision everywhere except escalating exactly on rows
  where (v1 routed weak) ∧ (weak fails) ∧ (strong correct). Ceiling quality and
  its cost (v1 cost + c_strong × escalated share) are computed once per surface
  and reported.

## Cascade economics (exact, stored prices)

cost_P3(τ) = c_weak + c_strong × share(escalate)   [weak always called first]
cost_v1    = c_weak × (1−fs_v1) + c_strong × fs_v1  [fs_v1 from cached probs @0.30]
Stored train means: weak $0.0000458/call, strong $0.0032889/call. Latency is not
measurable on this corpus (declared); call counts per arm are reported instead.

## Keep gate (frozen)

Retain the P3 signal iff on the pivot holdout the best frozen operating point
(O1 or O2; O3 and control reported alongside):

- **Quality arm:** capture ≥ 50% of the REALIZABLE oracle ceiling's quality lift
  over v1, at cascade cost/row ≤ v1's; OR
- **Cost arm:** ≥ 5% relative cascade cost reduction at ≥ v1 quality;

and the frozen trigger must also beat the wf-v1-trigger control on the same
arm's metric (trigger quality, not architecture, must be the source of the win).
Capture < 50% on both arms → P3 KILLED as a trigger (mission §14; no re-threshold).

Adversarial rule (mission §P3): per-task-family OOF AUROC/lift table is reported;
families with AUROC ≤ 0.55 are flagged as no-signal; the final recommendation
drops the signal there rather than averaging it away.

## Falsification risks (declared in advance)

- VF-accept precision is ~0.33 (Phase C): V-out alone is expected to be a weak
  trigger; the probe's job is to add shape evidence beyond VF.
- Class imbalance (weak correct ≈ 0.77): risk AUROC may look acceptable while
  escalation economics fail; the gate is economic, not AUROC.
- OOF thresholds + full-dev refit carry mild optimism; the single holdout pass is
  the guard. No threshold is moved after holdout scoring.
- Multiple comparisons: exactly three operating points + one control, all frozen
  above before holdout scoring.

## Scoring plan

1. Build features from weak responses (all train rows); run leakage audit.
2. Dev-fit: CV table (AUROC + cascade economics per feature set × C); freeze the
   probe, τ_q, τ_c, O3 share, and print the FROZEN section.
3. Single pivot-holdout pass: baselines, O1, O2, O3, control, realizable ceiling;
   paired bootstrap CIs (1,000 resamples, seed 42) on quality and cost deltas.
4. Deliverable `results/P3_INTERNAL_CONFIDENCE.md` + ledger rows; commit;
   boundary report; STOP.
