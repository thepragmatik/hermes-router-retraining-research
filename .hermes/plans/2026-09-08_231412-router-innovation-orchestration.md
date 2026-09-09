# Plan — Router Innovation Program Orchestrator (research/router-innovation-2026-09-08)

## Goal

Launch the nine-idea Router Innovation Program per `ideas/META_PROMPT.md`: run every
cheap, independently qualified Stage-0 falsification gate in parallel-safe waves, track
status in `ideas/STATUS.md`, and converge to a final integration recommendation without
spending money or weakening any gate.

## Current context / assumptions

- Repo: `/Users/rath/src/hermes-router-retraining-research`, branch
  `research/router-innovation-2026-09-08` (verified: HEAD 6fad0ee, clean).
- All nine Spec Kit packages exist at `specs/<idea>/` with `spec.md`, `plan.md`,
  `tasks.md`, `PROMPT.md` (verified by directory listing). All Stage-0 phases are $0;
  no prompt authorizes paid calls (verified by subagent summary).
- **Critical known constraint (from `research/2026-09-08-branch-evidence-map.md`):**
  idea 109's prerequisite — replayable Hermes traces — does NOT exist.
  `evidence/shadow/shadow_log.jsonl` is mostly health traffic; the shadow path never
  appended decision records, has no join keys, no outcomes → idea 109 Stage-0 step T004
  will correctly terminate with `TRACE_DATA_INSUFFICIENT` + telemetry-gap contract.
- Known data-quality gaps: `results/V1_BASELINE_GAPS.md` (on feat/generator-pivot-r0)
  documents shadow-log gaps G1–G6; idea 101's spec directly targets those gaps.
- Assumption: each idea runs on its own feature branch (from this base) and each
  Stage-0 is a bounded 2–4 h agent workload. One child agent per idea, one idea per
  context — never one agent for all nine.
- Assumption: the program runs across multiple user sessions; `ideas/STATUS.md` +
  `mnemosyne` task-progress records are the durable state, not the chat transcript.

## Architecture / proposed approach

Three dependency waves per META_PROMPT: Wave A launches 101, 103, 104, 105, 107 as
parallel, mutually independent $0 Stage-0 agents (each on its own feature branch).
Wave B (102 Stage 0 now; 108 retrospective now; their real-data phases gated on 101
finishing with qualified telemetry) runs opportunistically. Wave C (106, 109) waits
on earned prerequisites (≥2 independently qualified signals; trace viability). Every
idea writes prereg FIRST, freezes gates, then runs; a failed gate is final evidence —
never relaxed. The orchestrator (you, the main session) merges nothing, does not
implement ideas itself, only launches children, records verdicts, and enforces gates.

## Step-by-step tasks

### Phase 0 — Orchestrator bootstrap (single task, ~10 min, do first)

- [ ] **P0-1. Read the governance docs.** Read these six files in this order before
      launching anything (do not skim — gates and status vocabulary live here):
      1. `.specify/memory/constitution.md`
      2. `ideas/README.md`
      3. `specs/router-innovation-2026-09-08/roadmap.md`
      4. `research/2026-09-08-innovation-deep-research.md`
      5. `research/2026-09-08-adversarial-review.md`
      6. `research/2026-09-08-branch-evidence-map.md`
      Verification: you can state, without re-reading, (a) what a KILLED verdict
      means for an idea, (b) why 109's trace data is insufficient, (c) why 102/108's
      real-data phases cannot start yet.
- [ ] **P0-2. Create the status ledger.** Create `ideas/STATUS.md` from the template
      `11781aa ideas: add orchestrator status ledger template` (check
      `git show 11781aa --stat` for the template path; if it's `ideas/STATUS.md`
      itself, edit that file). One row per idea, exactly the META_PROMPT status
      contract: id, title, spec status, Stage reached, latest commit SHA, spend to
      date ($0.00 everywhere), data/validation exposures, primary metric/gate
      result, blockers, exact decision vocabulary from that idea's PROMPT.md.
      Initial states: all nine rows, status `survived-research`, stage
      `not-started`, spend `$0.00`.
      Verification: `cat ideas/STATUS.md | grep -c '| 10'` returns 9 rows; commit:
      `git add ideas/STATUS.md && git commit -m "ideas: initialize program status ledger (Wave A pending)"`.
- [ ] **P0-3. Sanity-check child-agent capacity.** Confirm the delegation tool can
      spawn ≥3 concurrent children (historically supported). Decide per-wave
      parallelism: launch at most 3 Wave-A children simultaneously, remainder
      queued. Rationale: keeps transcript pressure low and lets you steer
      mid-flight; queue 104/105 behind 101/103/107 completion.

### Phase 1 — Wave A: five parallel $0 Stage-0 gates (core of this plan)

Each is a child agent launched via `delegate_task` with the idea's own
`specs/<idea>/PROMPT.md` pasted into the child's `context` field (children see
nothing of this conversation). Launch pattern per idea:

```
delegate_task(tasks=[{ goal: "Execute Stage 0 for idea 1XX exactly as
specs/1XX-.../PROMPT.md directs", context: "<paste full PROMPT.md> +
'You are on branch <feature-branch>; create it from
research/router-innovation-2026-09-08 first with:
git checkout -b <feature-branch>'. Do NOT authorize paid calls. Do NOT
touch RouterBench test split. Stop at the first frozen-gate failure and
report the exact terminal-status vocabulary from PROMPT.md." }])
```

Launch order (by foundation priority per META_PROMPT):

- [ ] **P1-A. Idea 101 — Counterfactual Shadow Telemetry** (highest foundation
      priority, no deps). Branch: `101-counterfactual-shadow-telemetry`.
      Child tasks: read governance docs; write `results/101/PREREG.md` FIRST
      (freezing train-only source, seeds, target policies, OPE estimators,
      support thresholds, gates); then T010–T020 from
      `specs/101-counterfactual-shadow-telemetry/tasks.md` (DecisionEvent /
      OutcomeEvent dataclasses, logging-policy simulator with exact propensities,
      IPS/SNIPS/cross-fitted DR/SWITCH-DR estimators, ESS/overlap diagnostics,
      corrupted-propensity tests that fail loudly, `STAGE0_OPE.json/md`).
      Gate (from spec): OPE ranks target policies correctly in ≥9/10 seeds; |error| ≤ 0.015
      quality units OR 95% CI contains truth in ≥90% of seeds; unsupported-policy
      diagnostics fire. Failure → single preregistered diagnostic correction,
      re-run once, else `KILLED`, stop, never touch live shadow code.
      Deliverable: child returns terminal status + `results/101/STAGE0_OPE.md` path.
- [ ] **P1-B. Idea 107 — Diversity-Optimized Model Portfolio**. Branch:
      `107-diversity-model-portfolo` (typo guard: use
      `107-diversity-model-portfolio` — copy exact name from PROMPT.md).
      Child tasks: read `results/P0_MODEL_POOL.md`, `results/P5_THREE_TIER.md`,
      `DATASETS.md`; prereg `results/107/PREREG.md`; refresh current model/
      provider/pricing snapshot with timestamps (NO historical GPT-4/Mistral
      assumptions); load train-safe outcome matrix + ≥1 compatible public
      routing matrix; compute pairwise co-failure, unique successes, conditional
      rescue; brute-force subsets ≤3 + cost-aware greedy; portfolio frontier;
      marginal-contribution gates.
      Gates: portfolio survives if ≥2pp oracle quality gain at ≤2x cost of best
      single model, OR ≥15% oracle cost cut at matched quality; each added
      model contributes ≥0.5pp unique rescue or ≥5% cost improvement;
      simple realizability test must capture ≥35% of oracle gain (else
      `ORACLE_ONLY_PORTFOLIO`); if one model dominates → `SINGLE_MODEL_PIVOT`.
      Deliverable: terminal status + `results/107/` complementarity table +
      frontier + realizability report.
- [ ] **P1-C. Idea 103 — Bayesian Semantic Performance Memory**. Branch: same base
      (no separate feature branch named in PROMPT.md — use
      `103-bayesian-semantic-memory` anyway for isolation).
      Child tasks: prereg `results/103/PREREG.md` FIRST (train folds, embedding
      version, k grid, decay grid, prior strengths, support rule, cost grid);
      reuse frozen BGE embeddings + train-only neighbor index; global-prior and
      task-prior baselines; raw kNN with n_eff; empirical-Bayes shrinkage;
      per-neighbor provenance; train-CV Brier/log-loss/gain ranking; cost-aware
      frontier; paraphrase/format/distractor perturbation fixtures; OOD/low-support
      back-off tests.
      Gate: shrinkage beats kNN and task-prior on ≥8/10 folds AND (≥0.5pp quality
      at matched cost OR ≥3% relative cost cut at matched quality OR material OOD
      improvement without >0.2pp quality loss); paraphrase perturbation must not
      inflate route-flip >10pp; low-support rows show worse calibration.
      Possible verdicts: `KILLED` | `KNN_ONLY` | `SEMANTIC_MEMORY_PASS`.
      Deliverable: terminal status + `results/103/STAGE0_REPORT.md` + frontier CSV.
- [ ] **P1-D. Idea 104 — Whitened Latent Marginal-Gain Probe**. Branch:
      `104-whitened-latent-gain-probe`.
      Child tasks: T002 feasibility FIRST — confirm an accessible local/cheap
      model exposes hidden states/logits at $0; if not, record
      `REPRESENTATION_BLOCKED` and stop immediately (this is an expected,
      non-failure outcome). If feasible: prereg `results/104/PREREG.md` (model
      revision, layers, token summaries, PCA dims, target pair, folds, seeds);
      streaming latent extraction (no full activation dumps); BGE/logit/shape
      controls on identical rows; leakage + label-shuffle tests; covariance
      spectrum/condition number; raw/PCA/whitened probes; frozen dim/layer grid;
      pairwise-gain AUPRC/AUROC + task-stratified metrics; cost-aware frontier.
      Gate: whitened probe beats prompt-embedding + logit-only baselines by ≥0.03
      absolute AUPRC/AUROC in ≥8/10 folds AND survives task stratification AND
      cost-aware policy achieves ≥0.5pp quality at matched cost or ≥3% cost cut.
      Verdicts: `KILLED` | `RAW_OR_PCA_PASS` | `WHITENED_PASS`.
      Deliverable: terminal status + `results/104/` Stage-0 report.
- [ ] **P1-E. Idea 105 — Conformal Safety Envelope**. Branch:
      `105-conformal-safety-envelope`.
      Child tasks: prereg `results/105/PREREG.md` (exact risk event, α ∈
      {0.01, 0.025, 0.05}, confidence delta, min calibration size, V1 score +
      strongest other qualified score, optional strata); nested score-threshold
      acceptance sets; exact one-sided binomial / conformal risk bound with unit
      tests against known examples; NO_SAFE_COVERAGE behavior; risk/coverage
      curves on V1 (mandatory control) + other existing score; cost economics;
      drift alarms.
      Gate: ≥1 target risk with held-out empirical risk ≤ target in ≥9/10 folds;
      cheap coverage ≥10% on useful traffic OR ≥5% with material cost/risk gain;
      matched-quality cost improves ≥3% vs unwrapped baseline; drift alarm
      deactivates/widens envelope correctly. No useful coverage → `KILLED`
      (never weaken α). V1 success → `V1_SAFE_SLICE`.
      Deliverable: terminal status + `results/105/STAGE0_REPORT.md` +
      `coverage_risk.csv`.

**Wave-A execution rule:** do NOT start Wave B until at least three of the five
Wave-A children have returned terminal statuses. Do NOT let one slow child block
the others; if one exceeds ~45 min with no progress (check
`delegate_task(action='list')`), steer or stop it and queue a retry.

### Phase 2 — Wave B: conditional Stage-0 launches (opportunistic)

- [ ] **P2-A. Idea 102 — Doubly Robust Uplift Router — Stage 0 ONLY**. Branch:
      `102-doubly-robust-uplift-router`. Launch as soon as capacity frees up
      (its Stage 0 is $0 simulation-only and independent). Child tasks: prereg
      `results/102/PREREG.md` (pair, quality metric, train split, ≥3 logging
      regimes broad→V1-skewed, seeds, λ grid, nuisance models, clipping rules);
      simulated propensity logs from full-information train rows; V1/always/
      direct-correctness/T-learner controls; cross-fitted nuisances; DR
      pseudo-outcomes on exact simulated propensities; ESS/overlap diagnostics;
      λ-sweep frontiers; ≥10 seeds; oracle-capture fraction + paired bootstrap;
      adversarial support tests (skewed logging, zero-overlap, corrupted
      propensity).
      Gate: DR policy-value |error| ≤ 0.015 on ≥2/3 logging regimes; beats
      direct-correctness baseline on ≥8/10 seeds; τ̂-policy captures ≥35% of
      oracle lift at ≤50% cost-advantage loss; unsupported regimes flagged.
      V1-skew collapse → `NEEDS_101_COVERAGE` (NOT qualified).
      Deliverable: terminal status + `results/102/STAGE0_REPORT.md`.
- [ ] **P2-B. Idea 108 — Multi-Fidelity Synthetic→Real Fusion — retrospective Stage 0**.
      Branch: `108-multifidelity-synthetic-real`. Prereq: R7a synthetic rows on
      feat/generator-pivot-r0 (they exist — `evidence/gen_factory/*`,
      `GENERATOR_PREREG.md`); merge/rebase that branch's data in first.
      Child tasks: prereg `results/108/PREREG.md` (synthetic source/version,
      real train rows, budgets 0.5/1/2/5/10%, seeds, fusion arms, weight grid);
      provenance manifest + schema validation so synthetic can never load as
      real; task/embedding/label shift diagnostics; deliberate known-bias
      simulator for code-path validation; frozen matched real-row samples per
      budget; real-only / synthetic-only (non-promotable) / synthetic-pretrain
      →real-update / weighted-joint arms; real held-out evaluation; budget
      curves; paired uncertainty.
      Gate: fusion beats real-only at ≥3/5 budgets incl. one ≤2% AND ≥0.5pp
      quality at matched cost / ≥3% cost cut / ≥25% real-label saving;
      synthetic-only never promotes; biased control flagged lower-trust;
      survives ≥8/10 seeds. Verdicts: `KILLED` | `LOW_FIDELITY_PRIOR_ONLY` |
      `SAMPLE_EFFICIENCY_PASS`.
      Deliverable: terminal status + `results/108/` budget curves + Stage-0 report.
- [ ] **P2-C. Record Wave-A/B outcomes.** After each child returns, append a row to
      `ideas/STATUS.md` (exact verdict vocabulary, commit SHA of that idea's
      branch tip, spend, gate result, blockers) and commit:
      `git add ideas/STATUS.md && git commit -m "ideas: record idea 1XX Stage-0 verdict <VERDICT>"`.
      Also update `mnemosyne` task-progress under key
      `router-innovation-2026-09-08` so the next session can resume from disk.

### Phase 3 — Wave C: only if prerequisites are EARNED

- [ ] **P3-A. Idea 109 — Hermes Stage-Aware Agent Router (trace-viability check only)**.
      Branch: `109-hermes-stage-router`. Expected outcome (pre-recorded in
      STATUS.md as assumption): `TRACE_DATA_INSUFFICIENT`. Child tasks: prereg
      `results/109/PREREG.md`; inventory available Hermes traces and write
      `results/109/trace_quality.json`; if trace gates fail (≥100 completed
      missions or ≥500 stage decisions across ≥3 task types, ≥95% steps with
      model id/step order, outcomes for ≥80% missions, retries/tool/test
      logged), write the exact telemetry-gap contract and STOP — no policy
      modeling. This is the cheapest idea to run (≈15 min) and produces a
      concrete, actionable telemetry spec for a future shadow re-run.
      Deliverable: `results/109/trace_quality.json` + telemetry-gap contract.
- [ ] **P3-B. Idea 106 — Sequential VOI Controller**. HARD GATE: do NOT launch
      until ≥2 of {103, 104, 105, 107} have independently passed their gates
      (`SEMANTIC_MEMORY_PASS`/`KNN_ONLY`, `RAW_OR_PCA_PASS`/`WHITENED_PASS`,
      `V1_SAFE_SLICE`, `PORTFOLIO_PASS`). If fewer than two pass, mark 106
      `BLOCKED_PREREQ_NOT_MET` in STATUS.md and do not launch.
      Child tasks: prereg `results/106/PREREG.md` (max 3 dynamic actions, state
      features, utility/cost grid, replay split, seeds); replay environment
      with strict policy-visible vs evaluator-only separation; V1/base,
      best-fixed-cascade, cheapest-first, single-action controls; oracle
      headroom diagnostic; cross-fitted action incremental-utility models;
      positive-VOI choice + stop; λ sweep; ≥10 folds/seeds; paired bootstrap
      vs best fixed cascade.
      Gate: myopic VOI beats best fixed cascade by ≥3% relative cost at matched
      quality OR ≥0.5pp quality at ~matched cost; no degenerate fixed order
      >95% of rows; VOI calibration directionally correct; ≥8/10 seeds, no
      oracle leakage. Myopic fail → `KILLED`/`FIXED_POLICY_WINS`, NO RL.
- [ ] **P3-C. 105-wraps-finalists (only if ≥1 of 102/103/104 qualifies).** Launch a
      small child to re-run idea 105's calibration over the newly qualified
      candidate score(s) (not just V1), reusing `results/105/PREREG.md` α grid
      frozen earlier — do NOT retune the candidate score. Append outcome rows to
      STATUS.md.

### Phase 4 — Program convergence

- [ ] **P4-1. Convergence check.** When all nine ideas have terminal statuses in
      STATUS.md, verify every row has: verdict vocabulary, commit SHA, spend,
      gate result, exposure count. Missing → go back to that idea.
- [ ] **P4-2. Write integration recommendation.** Produce
      `ideas/INTEGRATION_RECOMMENDATION.md` with the ten META_PROMPT sections
      (statuses; spend/evidence tier per idea; qualified components; killed
      ideas + why; stackability/error-overlap findings; selected portfolio;
      recommended single-turn architecture; recommended agentic-stage
      architecture; telemetry improvements valuable regardless of router; exact
      next Hermes shadow action or a stop recommendation). Note explicitly:
      101→(102+103 and/or 104)→105 is the hypothesized stack; only stack
      components with measured marginal contribution and error overlap.
      Commit and push the branch.
- [ ] **P4-3. Wrap-up memory.** Write a `mnemosyne` task-progress record with the
      final status table summary and the integration-recommendation path so a
      fresh session can pick up without reading the full transcript.

## Tests / validation

Each idea's own tasks.md embeds TDD discipline (invariant tests, corrupted-input
tests, leakage tests). The orchestrator's own validation is:

- Verify each idea's prereg file exists BEFORE its Stage-0 report:
  `test -f results/<id>/PREREG.md && test -f results/<id>/STAGE0_*.md` (or
  equivalent per-idea filename) — a report without a prereg is a gate violation;
  discard that child's result and relaunch.
- Verify each child's terminal status string matches its PROMPT.md's allowed
  vocabulary exactly (e.g. 103 must be one of `KILLED`, `KNN_ONLY`,
  `SEMANTIC_MEMORY_PASS`; "promising", "looks good" etc. are invalid).
- Verify sealed-test integrity: child must assert in its report that
  RouterBench test split was never loaded; spot-check no test-split path appears
  in the child's changed files (`git diff --stat` on its branch).
- Verify spend: sum of all spend fields in STATUS.md must equal $0.00 at Wave A/B
  close (no prompt authorizes paid calls this phase).
- Verify branch hygiene: each idea's work lands on its own branch; STATUS.md
  updates land on `research/router-innovation-2026-09-08`.

## Risks, tradeoffs, and open questions

- **Risk: parallel children exceed context/attention.** Mitigation: max 3
  concurrent children; steer/stop via `delegate_task(action='list'/'steer')`.
- **Risk: a child weakens a gate to pass.** Mitigation: prereg-first ordering
  (enforced by verifying PREREG.md predates STAGE0 report), exact verdict
  vocabulary required, orchestrator rejects non-vocabulary statuses.
- **Risk: 107's "refresh current pricing" accidentally authorizes spend.**
  Mitigation: pricing refresh = metadata lookup only; no inference calls; child
  prompt states this explicitly.
- **Tradeoff: 102/108 Stage 0 could run in Wave A.** Chosen: keep in Wave B per
  META_PROMPT ordering (they have more moving parts; Wave A breadth-first
  information value is higher). If Wave A finishes early, pull 102 forward.
- **Known non-failure: 109 will end `TRACE_DATA_INSUFFICIENT`.** Pre-declare in
  STATUS.md; the deliverable is the telemetry-gap contract, which feeds a future
  shadow re-run (deferred shadow fix documented in `results/V1_BASELINE_GAPS.md`
  requires a fresh prereg before any code).
- **Open question: does the host have a local model exposing hidden states for
  104?** T002 answers this cheaply; expected fallback `REPRESENTATION_BLOCKED`.
- **Open question: Wave-A results may invalidate downstream assumptions** (e.g.
  107 selects a new pool → 102/103/105 must recalibrate; historical V1
  thresholds do not transfer). Handle at Phase 3, not by re-running Wave A.
