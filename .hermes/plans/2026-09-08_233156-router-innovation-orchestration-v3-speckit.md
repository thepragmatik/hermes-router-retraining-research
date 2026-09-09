# Plan v3 — Router Innovation Program Orchestrator (Spec Kit linkage confirmed)

Supersedes plan v2 (`.hermes/plans/2026-09-08_232253-router-innovation-orchestration.md`),
which is otherwise unchanged in its Wave A/B/C structure, worktree isolation
strategy, and launch template. This v3 exists to answer the operator's question
—"will the plan actually use the Spec Kit packages to build each idea?" — with
verified evidence, and to add the two mechanisms that make Spec Kit usage
*enforceable* rather than assumed.

## Goal

Launch the nine-idea Router Innovation Program using each idea's GitHub Spec
Kit package (`specs/<idea>/{spec,plan,tasks,PROMPT}.md`) as the sole build
authority per idea, in dependency-gated waves, with autonomous progress and
verifiable Spec Kit compliance.

## Current context / assumptions

All verified this session (read-only):

- **Every one of the nine PROMPT.md files explicitly references its own Spec
  Kit package.** `grep -o "spec\.md\|plan\.md\|tasks\.md" specs/*/PROMPT.md`
  finds spec.md, plan.md, and tasks.md references in all of 101–108 (109's
  PROMPT.md names the folder's spec/plan/tasks directly: "Read the
  constitution and this folder's `spec.md`, `plan.md`, `tasks.md`"). So the
  Spec Kit packages are not documentation garnish — each PROMPT.md's
  read-order and non-negotiable rules are the child's build authority.
- **The packages are committed on the program branch** (`git ls-tree HEAD
  --name-only specs/` lists all ten directories), so each worktree created
  from `research/router-innovation-2026-09-08` carries its idea's full
  package locally — children read their spec without network access.
- `ideas/package-manifest.json` declares `required_package_files` =
  ["spec.md","plan.md","tasks.md","PROMPT.md"] and wave/dependency per idea;
  `ideas/validate_packages.py` enforces completeness (filesystem + JSON
  structure checks; "does not execute experiments, access RouterBench, call
  networks, or authorize spend").
- PROMPT.md files define per-idea read-order (constitution → spec.md →
  plan.md → tasks.md → research docs → branch evidence) and each carries a
  "Non-negotiable execution rule" (101's example: "Do Stage 0 first… do not
  compensate by loosening gates").
- Worktree pool, dataset paths (`~/transfer-bundle/…`), STATUS.md ledger,
  and the child launch template are as specified in plan v2 — unchanged.
- Assumption: subagents receive the PROMPT.md verbatim (they see nothing of
  this conversation) and can read the Spec Kit files inside their worktree.

## Architecture / proposed approach

Each child agent's contract IS its Spec Kit package: the orchestrator pastes
the idea's `specs/<idea>/PROMPT.md` verbatim into the child's context (it
names spec.md, plan.md, and tasks.md in mandatory read-order), the child
works in its own worktree where those files exist at commit HEAD, and
compliance is verified by two automated checks — the existing
`ideas/validate_packages.py` gate at Phase 0, plus a new per-child
task-list citation check (the child must map every T-number it executes to
its tasks.md row, and the orchestrator diff-checks the mapping). Wave
gating follows the manifest's dependency graph; the orchestrator never
replaces Spec Kit content with its own paraphrase — the paste is verbatim.

## Step-by-step tasks

### Phase 0 — Spec Kit compliance bootstrap (before any child launches)

- [ ] **P0-1. Validate package completeness.**
      ```
      cd /Users/rath/src/hermes-router-retraining-research
      /usr/bin/python3 ideas/validate_packages.py; echo "exit=$?"
      ```
      Expected: `exit=0`, no "missing" lines. This checks the manifest's
      constitution / orchestrator_prompt / status_ledger / roadmap files and
      each idea's four required package files. Failure → stop and report.
- [ ] **P0-2. Machine-check that every PROMPT.md references its package.**
      (This is the TDD version of "confirm the plan uses the specs": write
      the check, see it pass.)
      ```
      for f in specs/1*/PROMPT.md specs/109*/PROMPT.md; do
        n=$(grep -c -E "spec\.md|plan\.md|tasks\.md" "$f")
        d=$(dirname "$f"); echo "$d: $n"
      done
      ```
      Expected: every line `specs/<idea>: >=3`. A package whose PROMPT.md
      names fewer than 3 of its own files is a defect → record in
      STATUS.md blockers for that idea before launch.
- [ ] **P0-3. Governance reading + dataset check + worktree pool** —
      identical to plan v2 (P0-1…P0-5 of v2, unchanged; do not repeat here:
      read `ideas/META_PROMPT.md` §"Read first", constitution, roadmap,
      evidence map; verify `~/transfer-bundle/…` files exist; create the
      five Wave-A worktrees with the v2 `git worktree add` loop; set
      STATUS.md "Last updated" line; commit on the program branch).

### Phase 1 — Wave A children (Spec Kit paste-verbatim, launch template)

Use the v2 launch template unchanged, with these Spec Kit-specific
additions in the child context:

```
Spec Kit authority (in addition to the pasted PROMPT.md):
- Your build authority is this idea's Spec Kit package inside YOUR worktree:
  specs/<slug>/spec.md   (requirements, gates, verdict vocabulary)
  specs/<slug>/plan.md   (architecture, statistics, rollback logic)
  specs/<slug>/tasks.md  (ordered T-numbered task list — execute top-down,
                          cheapest falsification first; do not skip ahead)
- Read them in the PROMPT.md's stated order BEFORE writing any code.
- In your Stage-0 report, include a "Task coverage" section listing every
  tasks.md T-number you executed and one line of outcome each. Skipped
  T-numbers require a one-line justification (blocked / N-A per spec).
- The spec's gate thresholds are the contract. If a gate fails, the only
  permitted response is the spec's own bounded-correction clause.
```

- [ ] **P1-A..P1-E. Launch Wave A per v2:** 101 → 107 → 103 first, then 104
      and 105 as slots free; max 3 concurrent children; per-idea gates and
      verdict vocabulary are in each idea's `spec.md` (v2 lists them
      verbatim; do not re-derive). Worktrees already exist from P0-3.
- [ ] **P1-F. Per-child Spec Kit compliance check on return** (new, cheap):
      ```
      slug=101-counterfactual-shadow-telemetry
      # 1. child did not modify its own spec package:
      git -C ../idea-worktrees/$slug diff \
        research/router-innovation-2026-09-08..HEAD --name-only -- specs/ | wc -l
      # expected: 0 (specs are read-only build authority)
      # 2. Stage-0 report cites task coverage:
      grep -c "^- T[0-9]" ../idea-worktrees/$slug/results/101/STAGE0_OPE.md \
        || grep -rc "T0" ../idea-worktrees/$slug/results/101/*.md
      # expected: >0
      ```
      If check 1 shows specs/ changed → reject the child's verdict (it
      modified its own contract) and relaunch with an explicit
      specs-are-frozen instruction.

### Phase 2 — Wave B (102, 108, 109) and Phase 3 — Wave C (106, wrappers)

- [ ] Identical to plan v2 (P2-A…P2-E, P3-A…P3-C), with the same Spec Kit
      child-context block added to every launch. Worktrees for 102/108/109
      are created at wave launch with the v2 `git worktree add` pattern;
      each child again executes its own T-numbered tasks.md.
- [ ] **P2-E ledger updates, Spec Kit clause:** when recording a verdict in
      `ideas/STATUS.md`, cite the source section, e.g.
      `Gate result: Stage-0 gates per specs/102-…/spec.md 'Success Criteria / Stage 0' → PASS`.

### Phase 4 — Convergence

- [ ] Identical to plan v2 Phase 4 (P4-1…P4-3): convergence check,
      `ideas/INTEGRATION_RECOMMENDATION.md` with the ten META_PROMPT
      sections, STATUS.md integration-notes fill, push, memory checkpoint.

## Tests / validation

- Spec Kit completeness: `ideas/validate_packages.py` → exit 0 (P0-1).
- Spec Kit reference coverage: all nine PROMPT.md files name ≥3 of their
  own package files (P0-2, loop output above).
- Child compliance: per-child checks in P1-F — (a) specs/ untouched in the
  idea worktree diff, (b) Stage-0 report contains task-coverage citations
  mapping executed work to tasks.md T-numbers, (c) prereg file predates
  Stage-0 report (`git log --oneline --reverse -- results/<ID>/PREREG.md`).
- All v2 checks remain: worktree isolation, verdict-vocabulary match
  against each spec.md's vocabulary, sealed-test file-diff guard, spend
  column sum == $0.00 through Wave B, merge hygiene on the program branch.

## Risks, tradeoffs, and open questions

- **Risk: a child paraphrases or "improves" its Spec Kit instead of
  following it.** Detected by the specs-diff check (P1-F); rejected and
  relaunched with specs-frozen instruction. Specs are version-controlled
  evidence, not scratch space.
- **Risk: a child invents gates instead of reading spec.md.** Mitigated by
  pasting PROMPT.md verbatim (it mandates the read order) + the output
  schema requiring the child to name its gate source; the orchestrator
  spot-reads each spec.md gate section before accepting a verdict.
- **Tradeoff: verbatim PROMPT.md paste makes child contexts long (~2–4 KB
  each).** Accepted: children are isolated and must not depend on this
  conversation; the paste plus in-worktree package reads is the only way
  to guarantee zero-context children execute the actual spec.
- **Open question: none blocking.** Package completeness is machine-checked
  (P0-1), reference coverage machine-checked (P0-2), and per-child
  compliance is diff-checked (P1-F) — Spec Kit usage is now verified at
  three layers instead of being an assumption.
