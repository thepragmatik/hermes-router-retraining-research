# Agent handoff

## Mission

Research and qualify cheap, repeatable routing supervision for [`thepragmatik/hermes-pi-agentic-stack`](https://github.com/thepragmatik/hermes-pi-agentic-stack). The durable objective is a self-renewing routing control plane, not a one-off benchmark classifier.

## Current research status

**Ready for experimental execution, not production promotion.** Read [`RESEARCH_SIGNOFF.md`](RESEARCH_SIGNOFF.md) first. It separates established findings from hypotheses that still require the preregistered $0 tests below.

## Non-negotiables

- Do not write/ship production router code from this research repo.
- Do not rerun FALSIFIED cluster/BERT attempts unless a written hypothesis is materially different.
- Never access the sealed RouterBench test split.
- Default spend $0. Any spend requires fail-closed gating and total mission spend < $5.
- Remote judge requests require ZDR with no silent fallback.
- Normalize local paths to `~/`; publish no personal home paths/usernames.
- v1 validation APGR **0.6459** is the replacement baseline; **0.55** is only viability.

## Read order

0. [`RESEARCH_SIGNOFF.md`](RESEARCH_SIGNOFF.md)
1. [`memo/2026-09-05_ranked-options-memo.md`](memo/2026-09-05_ranked-options-memo.md)
2. [`evidence/adversarial-review.md`](evidence/adversarial-review.md)
3. [`evidence/semantic-routing-review.md`](evidence/semantic-routing-review.md)
4. [`evidence/judge-noise-derived-analysis.md`](evidence/judge-noise-derived-analysis.md)
5. [`designs/router-learning-flywheel.md`](designs/router-learning-flywheel.md)
6. experiment preregistrations 000, 003, 004, 005, 006
7. [`evidence/source-ledger.md`](evidence/source-ledger.md)

## Current recommendation

Run **Experiment 000 first**. It determines whether weak correctness is an acceptable final proxy or only the first factor of **Factorized Escalation Value**.

If strong rescue among weak failures is heterogeneous/non-universal, run **Experiment 003** with 0.5/1/2/5% revealed strong-label budgets. Then test the existing judge as a one-sided labeler (Experiment 004), semantic performance-memory/OOD features (Experiment 005), and bandit replay (Experiment 006).

Do not spend on new judges until these $0 paths are exhausted.

## Semantic routing rule

Semantic routing is allowed only as a **materially different** use from the falsified cluster router: task/domain conditioning, measured-outcome kNN retrieval, OOD/support, calibration or active-label coverage. `prompt -> cluster -> fixed weak/strong route` remains falsified.
