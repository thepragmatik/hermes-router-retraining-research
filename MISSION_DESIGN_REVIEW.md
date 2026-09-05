# Final mission-design review

**Date:** 2026-09-05  
**Status:** **PASS — ready for an execution-capable research agent**

## Review question

Can an autonomous agent read `AGENTS.md` and execute toward a concrete answer to the real business/engineering problem — preserve router quality while reducing refresh supervision cost — without needing unstated assumptions about code scope, datasets, metrics, spend, experiment order, or deliverables?

## Verdict

**Yes.** No blocking contradiction remains.

The mission is intentionally an **experimental execution mission**, not another literature-review mission and not a production-deployment mission.

## Correctness audit

### Objective — PASS

The north star is explicit: recover or exceed router-v1 validation quality while minimizing strong-model supervision and quantifying refresh/runtime economics.

### Baseline and metrics — PASS

- v1 replacement baseline: validation APGR `0.6459`;
- viability floor: `0.55`;
- strong-label budget is explicitly defined as the fraction of train rows whose fresh strong counterfactual would need to be purchased in a future refresh;
- weak-label cost, refresh cost and runtime cost are reported separately;
- external metrics may not be silently relabeled as project APGR/PGR.

### Code authorization — PASS

Research code is explicitly expected: analysis, data loading, training, evaluation, ablations, plots and reproducibility utilities. Only production/runtime integration into the parent Hermes stack is excluded.

### Data leakage/test sealing — PASS

The local RouterBench test split remains sealed. External-data deduplication is performed only against local train/validation; the test split is not inspected even for hygiene checks.

### Spend controls — PASS

Default spend is `$0`; paid work remains fail-closed behind an explicit environment gate and mission spend remains `< $5`. Remote judging requires ZDR with no silent fallback.

## Coherence audit

### Experiment order — PASS

The execution order follows information value:

1. reproduce v1 validation;
2. Experiment 000 target/rescue audit at `$0`;
3. branch to evaluator-first weak correctness or Factorized Escalation Value based on observed rescue structure;
4. test recovered one-sided judge signal;
5. test semantic performance-memory/OOD only after target/supervision is understood;
6. run an external robustness check for serious finalists;
7. test bandit replay as the long-term refresh architecture;
8. if <=5% strong truth fails, map the larger strong-label cost frontier before proposing real spend.

No phase depends on evidence that is produced only later.

### Negative-result path — PASS

The mission does not require the innovative hypotheses to win. If they fail, the agent must identify the minimum strong-label fraction needed for v1-level quality, price it, and decide whether router economics remain worthwhile.

### Semantic routing — PASS

The mission clearly distinguishes the falsified-adjacent direct cluster selector from the allowed use of semantics as task/domain conditioning, measured-performance retrieval, OOD/support, calibration and label-budget coverage.

## Dataset strategy audit — PASS

`DATASETS.md` now separates public data into roles:

- exact-pair qualification;
- transfer priors;
- external stress tests;
- unlabeled/OOD prompt distributions.

The preferred external method stress test is `Wikit/RoutingCompendium`; `LLMRouterBench` is the modern cross-pool stress test; RouteLLM and EmbedLLM are optional transfer/method datasets; Arena/LMSYS data is prompt-distribution/OOD evidence rather than pairwise correctness truth.

Important caveat: RoutingCompendium splits inherit the licenses of their source benchmarks. The execution agent must record the exact split/revision/license actually used.

## Completeness audit

The mission specifies:

- objective and decision being made;
- success/failure gates;
- metric definitions;
- authorized/prohibited work;
- required starting artifacts;
- public dataset policy;
- leakage/provenance rules;
- experiment sequence and branch logic;
- spend/security constraints;
- refresh and runtime cost accounting;
- fallback if low-label methods fail;
- required result artifacts;
- explicit final decision categories;
- boundary between research qualification and Hermes production/shadow integration.

## Final execution contract

A next agent should not stop after implementing experiments. It must continue until it can produce `FINAL_RECOMMENDATION.md` answering:

1. What routing/refresh method wins?
2. What validation APGR does it achieve?
3. What percentage of strong labels does a future refresh require?
4. What is the estimated refresh cost at execution-time prices?
5. What runtime savings/quality frontier does it provide?
6. Did the method survive at least one compatible external robustness test?
7. Should it be promoted to Hermes shadow evaluation, should v1 be retained with a cheaper refresh strategy, or are the router economics not justified?

## Sign-off

`AGENTS.md` is coherent and complete enough to serve as the primary autonomous-agent instruction for the next phase.

The next highest-value activity is **execution against the mounted local artifacts**, beginning with v1 validation reproduction and Experiment 000 — not another broad research pass.
