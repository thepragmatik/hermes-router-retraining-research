# Plan v2 — Router Innovation Program Orchestrator (adversarially reviewed)

Supersedes `.hermes/plans/2026-09-08_231412-router-innovation-orchestration.md`.
This v2 fixes four flaws found in the adversarial review of v1: (1) parallel
git branches in one working tree would have clobbered each other; (2) the
primary dataset lives OUTSIDE the repo and its absolute path was never given
to children; (3) `ideas/STATUS.md` already exists — v1 said "create" it; (4)
no copy-pasteable launch template / worktree bootstrap was specified, leaving
the implementer to guess the most error-prone step.

## Goal

Launch the nine-idea Router Innovation Program per `ideas/META_PROMPT.md` and
make maximum autonomous progress in one session: run every cheap Stage-0
falsification gate in parallel-safe worktrees, record verdicts in
`ideas/STATUS.md`, and converge toward the integration recommendation —
without spend, without weakening gates, and without a human in the loop
unless a hard gate fires.

## Current context / assumptions

All verified by read-only commands in this session (2026-09-08, HEAD 6fad0ee,
branch `research/router-innovation-2026-09-08`, clean):

- Repo root: `/Users/rath/src/hermes-router-retraining-research`.
- **`git worktree list` shows exactly ONE worktree** (the repo itself). All
  idea feature branches must be created as SEPARATE WORKTREES — a subagent
  doing `git checkout -b` in the shared tree would move the branch for every
  other concurrent agent (branch + index are repo-global, not per-process).
- **Primary dataset is outside the repo** (from `experiments/p0_model_pool_audit.py`
  header): `~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl`
  (train 29,193 rows, model-outcome matrix) and
  `~/transfer-bundle/analysis/winrate_table.parquet` (frozen hash split; test
  rows = 3,678, SEALED — only a membership count may ever be taken). It is
  read-only input, so concurrent readers in separate worktrees are safe.
- **`ideas/STATUS.md` already exists** with the exact ledger schema (9 rows,
  status `SURVIVED-RESEARCH`, evidence-tier vocabulary, integration-notes
  section). It is update-only — never recreate it, never delete failed rows.
- `ideas/package-manifest.json` is the machine-readable wave/dependency map
  (waves: A = 101,103,104,105,107; B = 102,108; C = 106; 109 =
  C-independent). `ideas/validate_packages.py` is a completeness checker.
- All nine packages exist under `specs/<idea>/` with spec.md, plan.md,
  tasks.md, PROMPT.md. No PROMPT.md authorizes paid calls; default spend $0.
- Host: 16 CPU, 128 GB RAM, `/usr/bin/python3` 3.9.6 with torch 2.8.0 +
  sentence_transformers 5.1.2 — concurrent children each run their own
  python; memory is ample.
- Known outcome pre-declared: idea 109's trace prerequisite does not exist
  (`results/V1_BASELINE_GAPS.md` G1–G5: shadow log has hardcoded prompt_id=0,
  no outcome capture, no content hash, 67 health-probe rows). Expect
  `TRACE_DATA_INSUFFICIENT` + telemetry-gap contract; that is success for
  this idea's Stage 0, not failure.
- Assumption: subagents (delegate_task) can run concurrently (limit 3 at a
  time) and each gets an isolated terminal session; they share the
  filesystem, hence the worktree rule. They cannot ask the user questions.
- Assumption: the user wants autonomous progress; the plan therefore
  front-loads everything that can run without operator input and defines
  exact BLOCK conditions where operator authorization is mandatory.

## Architecture / proposed approach

Each idea gets its own `git worktree` under `../idea-worktrees/<id>-<slug>`
(created from the program branch), so up to three subagents can build and
run their Stage-0 pipelines simultaneously without git-state collisions;
they read the shared read-only dataset in `~/transfer-bundle/` and write only
inside their own worktree. The orchestrator (main session) never edits
idea code: it bootstraps worktrees, pastes each idea's `specs/<idea>/PROMPT.md`
verbatim into a child's context (children see nothing of this conversation),
enforces prereg-before-report ordering and exact verdict vocabulary, then
aggregates verdicts into `ideas/STATUS.md` on the program branch. Waves
follow `ideas/package-manifest.json`: Wave A (101, 107, 103, 104, 105) →
Wave B (102, 108) → Wave C (106 gated on ≥2 qualified signals; 109
independent trace check, expected TRACE_DATA_INSUFFICIENT).

## Step-by-step tasks

Every task names exact paths and exact commands. Where a task says
"expected output", that is the acceptance check.

### Phase 0 — Orchestrator bootstrap (one session, ~15 min, sequential)

- [ ] **P0-1. Validate packages.**
      ```
      cd /Users/rath/src/hermes-router-retraining-research
      /usr/bin/python3 ideas/validate_packages.py
      ```
      Expected output: exit code 0, no "missing" errors printed.
      If it fails: stop, report the missing package — do not improvise.
- [ ] **P0-2. Read governance docs** (in this order; gates and verdict
      vocabulary live here):
      1. `.specify/memory/constitution.md`
      2. `specs/router-innovation-2026-09-08/roadmap.md`
      3. `research/2026-09-08-branch-evidence-map.md`
      4. `research/2026-09-08-adversarial-review.md`
      5. skim each child's `specs/<idea>/PROMPT.md` at launch time (paste
         verbatim into the child).
      Acceptance: you can state (a) what KILLED means and why gates cannot
      be relaxed after results are observed, (b) why 102/108 real-data
      phases wait for 101, (c) the sealed-test rule (membership count only).
- [ ] **P0-3. Create the worktree pool.** One worktree per idea, on its own
      feature branch, from the program branch:
      ```
      cd /Users/rath/src/hermes-router-retraining-research
      mkdir -p ../idea-worktrees
      for slug in 101-counterfactual-shadow-telemetry \
                  103-bayesian-semantic-memory \
                  104-whitened-latent-gain-probe \
                  105-conformal-safety-envelope \
                  107-diversity-model-portfolio; do
        git worktree add "../idea-worktrees/$slug" -b "$slug" \
          research/router-innovation-2026-09-08
      done
      git worktree list
      ```
      Expected output: `git worktree list` shows 6 entries (1 repo + 5
      worktrees) each on its own branch.
      Note: 102/108/106/109 worktrees are created later, at their wave
      launch, with the same command pattern (YAGNI — don't create early).
      If `git worktree add` fails because the branch exists: check
      `git branch --list <slug>` — if a stale branch exists from a prior
      aborted run, inspect it with `git log -1 <slug>` and REUSE it (do not
      delete evidence branches).
- [ ] **P0-4. Verify dataset accessibility (read-only).**
      ```
      ls -la ~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl \
             ~/transfer-bundle/analysis/winrate_table.parquet
      ```
      Expected: both files exist with nonzero sizes. If missing: ideas
      101/102/103/105/107 are all BLOCKED (they all consume this matrix);
      stop and report — do not substitute other data.
- [ ] **P0-5. Update the status ledger header only** (rows already exist;
      leave every row as-is until verdicts arrive). Edit
      `ideas/STATUS.md` line `**Last updated:** initialize when
      orchestration begins.` →
      `**Last updated:** 2026-09-08 — orchestration started, Wave A launching.`
      Commit on the program branch:
      ```
      git add ideas/STATUS.md && git commit \
        -m "ideas: orchestration started, Wave A worktrees bootstrapped"
      ```

### Phase 1 — Wave A: five parallel $0 Stage-0 gates (the core)

Concurrency rule: at most **3 children running** at once (subagent cap and
attention limit). Launch order: 101, 107, 103 first; 104 and 105 as slots
free. Never let one slow child block the others — that is what worktrees
solve.

**Copy-pasteable child launch template** (fill `<ID>` fields per idea):

```
delegate_task(tasks=[{
  "goal": "Execute Stage 0 for idea <ID> exactly as the pasted PROMPT.md directs; report the exact terminal-status vocabulary.",
  "context": "You are a dedicated execution agent for ONE spec-kit idea.
You know nothing else. Work inside your assigned git worktree:
/Users/rath/src/idea-worktrees/<slug>  (branch <slug> is already checked out
there; commit frequently on that branch only). NEVER run git checkout in
other directories; NEVER touch any other worktree.

Paste of the idea's execution prompt (follow it exactly):
----BEGIN PROMPT----
<verbatim contents of specs/<slug>/PROMPT.md>
----END PROMPT----

Hard constraints (supersede nothing in the prompt, they agree):
- $0 spend. No paid API/model calls are authorized. Model/pricing refresh
  means metadata lookup only (documentation/web text), never inference.
- RouterBench TEST split is SEALED. The only permitted touch is a
  membership count via the split table. Data paths:
  ~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl (train rows)
  ~/transfer-bundle/analysis/winrate_table.parquet (frozen split)
- Write results/<ID>/PREREG.md FIRST and freeze all gates in it BEFORE any
  pipeline code runs. A Stage-0 report without a prereg is invalid.
- Frozen V1 (router_v1/, threshold 0.30) is the mandatory control where the
  prompt says so; never modify it.
- On gate failure: at most the single preregistered diagnostic correction,
  then the frozen verdict vocabulary. Never weaken a gate after seeing
  results.
- Deliverable: terminal status (exact vocabulary from PROMPT.md), the
  report path under results/<ID>/, the branch tip SHA, and total spend.",
  "output_schema": {
    "type": "object",
    "required": ["idea_id","terminal_status","prereg_path","report_path","branch_sha","spend_usd","gate_summary"],
    "properties": {
      "idea_id": {"type":"string"},
      "terminal_status": {"type":"string"},
      "prereg_path": {"type":"string"},
      "report_path": {"type":"string"},
      "branch_sha": {"type":"string"},
      "spend_usd": {"type":"number"},
      "gate_summary": {"type":"string"}
    }
  }
}])
```

Per-idea specifics (child gets these added to the template):

- [ ] **P1-A. 101 — Counterfactual Shadow Telemetry** (highest priority, no
      deps). Worktree `../idea-worktrees/101-counterfactual-shadow-telemetry`.
      Key tasks (from `specs/101-counterfactual-shadow-telemetry/tasks.md`):
      T002 prereg `results/101/PREREG.md` (train-only source, seeds, target
      policies, OPE estimators, support thresholds, gates) → T010–T019:
      `DecisionEvent`/`OutcomeEvent` dataclasses, event-id/privacy-safe hash
      helpers (production hash key stays external), epsilon-mixture logging
      simulator with exact propensities, full-information truth evaluator,
      IPS + SNIPS + cross-fitted DR + one heavy-weight variant (SWITCH-DR
      or frozen clipping), ESS/overlap diagnostics, corrupted-propensity
      tests that fail loudly, frozen-seed simulation → `results/101/STAGE0_OPE.json` + `.md`.
      Gate: OPE ranks target policies correctly ≥9/10 seeds; |error| ≤ 0.015
      quality units OR 95% CI covers full-information truth in ≥90% of
      seeds; unsupported-policy diagnostics fire on inadequate overlap.
      Verdicts: PASS / KILLED (one preregistered correction max).
- [ ] **P1-B. 107 — Diversity-Optimized Model Portfolio**. Worktree
      `../idea-worktrees/107-diversity-model-portfolio`. Reads
      `results/P0_MODEL_POOL.md`, `results/P5_THREE_TIER.md`, `DATASETS.md`,
      and `experiments/p0_model_pool_audit.py` as the pattern for loading
      the shared matrix. Prereg `results/107/PREREG.md`, refresh current
      model/pricing snapshot WITH source timestamps (metadata only — no
      historical GPT-4/Mistral pricing assumptions), eligibility filters,
      pairwise co-failure / unique successes / conditional rescue, brute-force
      subsets ≤3 + cost-aware greedy validated against brute force,
      portfolio frontier, marginal-contribution gates, simple runtime-proxy
      realizability test.
      Gates: ≥2pp oracle quality gain at ≤2x best-single cost, OR ≥15%
      oracle cost cut at matched quality; each model contributes ≥0.5pp
      unique rescue or ≥5% cost improvement; realizability ≥35% of oracle
      gain (else `ORACLE_ONLY_PORTFOLIO`); one model dominating →
      `SINGLE_MODEL_PIVOT`.
- [ ] **P1-C. 103 — Bayesian Semantic Performance Memory**. Worktree
      `../idea-worktrees/103-bayesian-semantic-memory`. Prereg
      `results/103/PREREG.md` (train folds, embedding version — the frozen
      BGE model already in the environment — k grid, decay grid, prior
      strengths, support rule, cost grid); raw kNN with n_eff + distance
      diagnostics; empirical-Bayes hierarchical shrinkage; per-neighbor
      provenance; train-CV Brier/log-loss/gain ranking; cost-aware frontier;
      paraphrase/format/distractor perturbation fixtures; OOD/low-support
      back-off tests.
      Gate: shrinkage beats kNN AND task-prior on ≥8/10 folds AND (≥0.5pp
      quality at matched cost OR ≥3% cost cut at matched quality OR material
      OOD improvement without >0.2pp quality loss); perturbations must not
      inflate route-flip >10pp; low-support rows show worse calibration.
      Verdicts: `KILLED` | `KNN_ONLY` | `SEMANTIC_MEMORY_PASS`.
- [ ] **P1-D. 104 — Whitened Latent Marginal-Gain Probe**. Worktree
      `../idea-worktrees/104-whitened-latent-gain-probe`. T002 feasibility
      FIRST: confirm a local model exposes hidden states/logits at $0
      (torch 2.8.0 + sentence_transformers 5.1.2 are installed; the child
      must find an actual model artifact with accessible internals — e.g.
      a locally loaded HF checkpoint — NOT an API). If not:
      record `REPRESENTATION_BLOCKED` in `results/104/` and STOP — this is
      an expected, non-failure outcome. If feasible: prereg `results/104/PREREG.md`;
      streaming latent extraction (no full activation dumps); BGE/logit/
      response-shape controls on identical rows; row-join/no-leakage/
      label-shuffle tests; covariance spectrum/condition number; raw/PCA/
      whitened probes with eigenvalue floor; frozen dim/layer grid;
      pairwise-gain AUPRC/AUROC + task stratification; cost-aware frontier.
      Gate: whitened beats prompt-embedding and logit-only baselines by
      ≥0.03 absolute on the primary metric in ≥8/10 folds AND survives task
      stratification AND policy-level ≥0.5pp quality at matched cost or ≥3%
      cost cut. Verdicts: `KILLED` | `RAW_OR_PCA_PASS` | `WHITENED_PASS`.
- [ ] **P1-E. 105 — Conformal Safety Envelope**. Worktree
      `../idea-worktrees/105-conformal-safety-envelope`. Prereg
      `results/105/PREREG.md` (exact risk event; α ∈ {0.01, 0.025, 0.05};
      confidence delta; min calibration size; V1 score MANDATORY + strongest
      other existing score; optional coarse strata); nested score-threshold
      acceptance sets; exact one-sided binomial/conformal bound with unit
      tests against known examples; NO_SAFE_COVERAGE behavior; risk/coverage
      curves; cost economics vs unwrapped baseline; drift alarms.
      Gate: ≥1 target risk with held-out risk ≤ target in ≥9/10 folds;
      coverage ≥10% on useful traffic OR ≥5% with material gain; matched-
      quality cost improves ≥3%; alarms deactivate/widen on drift tests.
      No useful coverage → `KILLED` (never weaken α). V1 success →
      `V1_SAFE_SLICE`.

**Wave-A guardrail:** if a child exceeds ~45 min with no file changes in
its worktree (`git -C ../idea-worktrees/<slug> status --short` empty and no
new commits), steer it via `delegate_task(action='steer')`; if still stuck
after one correction, `action='stop'`, record the blockage in STATUS.md,
and queue a fresh child with a narrowed scope.

### Phase 2 — Wave B (opportunistic, still $0)

- [ ] **P2-A. Create worktrees for the wave** when ≥3 Wave-A children have
      returned:
      ```
      for slug in 102-doubly-robust-uplift-router \
                  108-multifidelity-synthetic-real \
                  109-hermes-stage-router; do
        git worktree add "../idea-worktrees/$slug" -b "$slug" \
          research/router-innovation-2026-09-08
      done
      ```
- [ ] **P2-B. 102 — Doubly Robust Uplift Router, Stage 0 ONLY.** Simulation
      on exact simulated propensities over the shared train matrix; ≥3
      logging regimes (broad → V1-skewed); V1/always-action/direct-
      correctness/T-learner controls; cross-fitted nuisances; DR pseudo-
      outcomes; λ sweep frontiers; ≥10 seeds; oracle-capture + paired
      bootstrap; adversarial support tests (skewed logging, zero-overlap
      stratum, corrupted propensity).
      Gate: |policy-value error| ≤ 0.015 on ≥2/3 regimes; beats direct-
      correctness baseline on ≥8/10 seeds; τ̂-policy captures ≥35% of oracle
      lift at ≤50% cost-advantage loss; unsupported regimes flagged.
      V1-skew collapse → `NEEDS_101_COVERAGE` (NOT qualified). Real-data
      phase stays locked until 101 finishes with qualified telemetry.
- [ ] **P2-C. 108 — Multi-Fidelity Synthetic→Real, retrospective Stage 0.**
      Needs R7a synthetic rows, which live on `feat/generator-pivot-r0`
      (GENERATOR_PREREG.md, evidence/gen_factory/*, experiments/gen_factory/*).
      Get them WITHOUT switching branches in any live worktree:
      ```
      cd ../idea-worktrees/108-multifidelity-synthetic-real
      git checkout feat/generator-pivot-r0 -- GENERATOR_PREREG.md \
        results/V1_BASELINE_GAPS.md
      git checkout main -- results/  # restore, if needed
      # or, preferred: read the files via `git show feat/generator-pivot-r0:<path>`
      # and copy into results/108/inputs/ with a provenance note.
      ```
      Then: prereg `results/108/PREREG.md` (budgets 0.5/1/2/5/10%, seeds,
      fusion arms, synthetic-weight grid); provenance manifest + schema
      validation so no synthetic row can load as real; shift diagnostics;
      deliberate known-bias simulator; frozen matched real-row samples;
      real-only / synthetic-only(non-promotable) / pretrain→update /
      weighted-joint arms; real held-out eval; budget curves.
      Gate: fusion beats real-only at ≥3/5 budgets incl. one ≤2% AND
      (≥0.5pp quality at matched cost OR ≥3% cost cut OR ≥25% real-label
      saving); survives ≥8/10 seeds. Verdicts: `KILLED` |
      `LOW_FIDELITY_PRIOR_ONLY` | `SAMPLE_EFFICIENCY_PASS`.
- [ ] **P2-D. 109 — trace-viability check (cheap, ~15 min, run any time a
      slot is free).** In its worktree: prereg `results/109/PREREG.md`;
      inventory Hermes traces (`evidence/shadow/shadow_log.jsonl` and any
      other trace sources) → write `results/109/trace_quality.json`; the
      evidence (G1–G5 in `results/V1_BASELINE_GAPS.md`) says gates will
      fail → write the exact telemetry-gap contract and STOP. Expected
      verdict: `TRACE_DATA_INSUFFICIENT`. Record the telemetry-gap contract
      path in STATUS.md — it is the concrete spec for a future shadow
      re-run (which itself needs a fresh prereg before any code).
- [ ] **P2-E. Ledger updates.** After EACH child returns, in the main repo:
      1. verify the child's outputs exist:
         ```
         test -f ../idea-worktrees/<slug>/results/<ID>/PREREG.md && \
         ls ../idea-worktrees/<slug>/results/<ID>/
         ```
         (a report without a prereg = invalid; discard and relaunch)
      2. merge the idea branch into the program branch:
         ```
         git merge --no-ff <slug> -m "merge idea <ID> Stage-0: <VERDICT>"
         ```
         (resolve conflicts by keeping results/<ID>/ additions only; idea
         branches touch disjoint paths by design — if a conflict appears,
         stop and inspect rather than force-resolving)
      3. update that idea's row in `ideas/STATUS.md`: stage, exact verdict
         vocabulary, branch SHA, spend ($0.00), gate result, blockers;
         commit `git commit -am "ideas: record idea <ID> Stage-0 verdict <VERDICT>"`.
      4. update `mnemosyne` task-progress key `router-innovation-2026-09-08`
         with the verdict so a fresh session resumes from disk.

### Phase 3 — Wave C (gated on EARNED evidence)

- [ ] **P3-A. 106 — Sequential VOI Controller. HARD GATE:** launch ONLY if
      ≥2 of {103, 104, 105, 107} returned a qualifying verdict
      (`SEMANTIC_MEMORY_PASS`/`KNN_ONLY`, `RAW_OR_PCA_PASS`/`WHITENED_PASS`,
      `V1_SAFE_SLICE`, `PORTFOLIO_PASS`). Count them explicitly and write
      the count in STATUS.md. If <2: mark 106 `BLOCKED_PREREQ_NOT_MET` and
      skip. If ≥2: worktree + child per template; myopic VOI vs best fixed
      cascade on train-derived holdout; NO RL/POMDP.
      Gate: ≥3% relative cost cut at matched quality OR ≥0.5pp quality at
      ~matched cost; no degenerate fixed order >95% of rows; VOI
      calibration directionally correct; ≥8/10 seeds; no oracle leakage.
- [ ] **P3-B. 105-wraps-finalists (only if ≥1 of 102/103/104 qualifies).**
      Small child re-runs 105's calibration over the new candidate score,
      reusing the FROZEN α grid from `results/105/PREREG.md`; never retune
      the candidate score. Append outcome to STATUS.md.
- [ ] **P3-C. If 107 selected a NEW model pool** (`PORTFOLIO_PASS` or
      `SINGLE_MODEL_PIVOT`): do NOT transfer historical V1 thresholds.
      Note in STATUS.md integration section that downstream recalibration
      is required, and identify it as a Phase-4 recommendation rather than
      silently rerunning old policies.

### Phase 4 — Convergence (same session if evidence allows, else next)

- [ ] **P4-1. Convergence check:** every STATUS.md row has verdict, SHA,
      spend, gate result, exposure count. Missing → chase that idea.
- [ ] **P4-2. Integration recommendation.** Write
      `ideas/INTEGRATION_RECOMMENDATION.md` with the ten META_PROMPT
      sections (statuses; spend/evidence tier per idea; qualified
      components; killed ideas + why; stackability/error-overlap findings;
      selected portfolio; recommended single-turn architecture; agentic-
      stage recommendation; telemetry improvements regardless of router;
      exact next Hermes shadow action OR a stop recommendation). Fill the
      "Program integration notes" section of `ideas/STATUS.md`. Commit and
      push: `git push origin research/router-innovation-2026-09-08`.
- [ ] **P4-3. Memory checkpoint.** `mnemosyne` task-progress record with the
      final table summary + integration-recommendation path.

## Tests / validation

Idea-internal TDD lives in each idea's tasks.md (invariant tests,
corrupted-propensity tests, leakage/label-shuffle tests, binomial-bound unit
tests). The orchestrator's own checks:

- Package completeness: `/usr/bin/python3 ideas/validate_packages.py` →
  exit 0 (P0-1).
- Worktree isolation: `git worktree list` shows one entry per launched idea,
  each on its own branch; no child ever ran `git checkout` outside its
  worktree (spot-check: `git -C ../idea-worktrees/<slug> branch --show-current`
  returns its own slug for every active worktree).
- Prereg ordering: `test -f ../idea-worktrees/<slug>/results/<ID>/PREREG.md`
  BEFORE accepting any Stage-0 report; also check the prereg commit
  predates the report commit:
  `git log --oneline --reverse -- results/<ID>/PREREG.md | head -1`.
- Verdict vocabulary: child's terminal_status must be one of that idea's
  PROMPT.md-allowed strings (e.g. 103 ∈ {KILLED, KNN_ONLY,
  SEMANTIC_MEMORY_PASS}). Anything else → reject, ask child (via steer) to
  restate, else discard.
- Sealed-test integrity: in each idea worktree,
  `git diff --name-only research/router-innovation-2026-09-08..HEAD | grep -i test`
  must return nothing touching split/test data files; child report must
  assert the membership-count-only rule.
- Spend: sum the `Spend` column of STATUS.md at each wave close; must be
  exactly $0.00 through Wave B (no prompt authorizes paid calls).
- Merge hygiene: after each `git merge --no-ff`, `git status` must be clean
  and `ls results/<ID>/` in the program branch must show the idea's outputs.

## Risks, tradeoffs, and open questions

- **Risk (mitigated by design): git collisions between parallel children.**
  Solved by dedicated worktrees; children are told their absolute worktree
  path and forbidden from checking out branches elsewhere. Residual risk:
  a child ignoring instructions and running `git checkout` at repo root —
  mitigated by the worktree isolation spot-check after each child returns;
  if violated, discard that child's uncommitted state, re-derive from its
  branch tip, and record the violation.
- **Risk: two children editing `ideas/STATUS.md` concurrently.** Prevented
  structurally: children never touch STATUS.md; only the orchestrator
  (main session) edits it, on the program branch.
- **Risk: dataset file contention.** None — `~/transfer-bundle/` files are
  read-only inputs; concurrent reads are safe.
- **Risk: 104's feasibility fails** (no accessible local model internals).
  Expected outcome; `REPRESENTATION_BLOCKED` is recorded and 104 exits
  cheaply without blocking other ideas.
- **Risk: 108's R7a artifacts span branches.** Mitigated in P2-C with
  `git show feat/generator-pivot-r0:<path>` extraction into the 108
  worktree — no branch switching in live worktrees.
- **Tradeoff: launching 102/108 only after ≥3 Wave-A returns adds latency
  but keeps the orchestrator's attention bounded.** If Wave A returns
  quickly (fast children), pull 102 forward immediately — the plan
  explicitly allows this.
- **Tradeoff: one child per idea burns more subagent calls than batching,
  but it is the constitution-mandated isolation** (one idea per context;
  per-idea gates, verdicts, and branches).
- **Open question: does a local HF checkpoint with accessible hidden states
  actually exist on this host?** 104's T002 answers this in minutes;
  no other idea depends on the answer.
- **Open question: could 107's pool change invalidate 105's calibration?**
  Yes — if 107 selects a new pool, 105's envelope must be recalibrated on
  scores from the new pool; handled at Phase 3/4, never by silently
  reusing historical thresholds.
- **Known non-failure: 109 → TRACE_DATA_INSUFFICIENT.** Pre-declared; the
  deliverable (telemetry-gap contract) feeds a future shadow re-run that
  itself requires a fresh prereg before any code.
