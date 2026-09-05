# Research method and clean-room discipline

## Scope

This research asks how repeated router refresh can become cheap enough for Hermes to adapt as model pairs, prices and workloads change without sacrificing the v1 validation baseline.

It intentionally does **not** ship production router code, inspect the sealed test split, or rerun previously falsified experiments.

## Two-pass research process

### Pass 1 — broad clean-room discovery

Evidence lanes covered router supervision/transfer, correctness forecasting, sparse retrieval, noisy-label learning, LLM-judge calibration, adaptive juries, label-free cascades, synthetic routing data and parent-Hermes operational constraints.

### Pass 2 — adversarial review and targeted contradiction search

The second pass tried to falsify the first memo. It explicitly searched for:

- evidence that weak correctness is target-misaligned;
- semantic-routing systems and failure modes;
- online/bandit routing that avoids full-information labels;
- one-sided/noisy-label methods suggested by the project's judge error structure;
- 2026 evidence that architecture/embedding changes are lower value than supervision/model recall;
- selection-bias and counterfactual-blindness failures of active/sparse labeling.

This pass **changed the ranking**, which is treated as evidence that the red team was substantive rather than confirmatory.

## Evidence hierarchy

1. primary papers, official benchmark/dataset documentation and first-party project docs;
2. peer-reviewed conference/anthology sources;
3. current official engineering repositories/docs;
4. preprints where no stronger source exists, labeled as such;
5. secondary sources only for discovery or explicitly bounded historical context.

External lift numbers are priors, never project results.

## Ranking criteria

A method ranks higher when it:

- aligns the training target with **marginal mission value** rather than proxy difficulty;
- reduces or localizes strong-model counterfactual labels;
- can be falsified for $0 or <$0.50;
- preserves train/val/test integrity;
- changes only one causal factor at a time where possible;
- remains useful when either model or provider price changes;
- detects/supports OOD and label-selection blind spots;
- supports accepted mission quality and total economics, not merely classifier metrics.

## Clean-room distinctions

- Mission-provided project outcomes are fixed inputs, not re-derived from the sealed test.
- The algebraic judge-confusion analysis uses only reported train aggregate rates; its approximate row counts are clearly marked as rounded.
- Published RouterBench task distributions are not assumed to equal the pinned local hash split without local audit.
- Semantic-routing evidence is separated into **intent/control-plane evidence** versus **model-quality-selection evidence**.
- Conformal/judge guarantees are not transferred across different score definitions or exchangeability assumptions.
- Bandit approaches are strategic research candidates; production exploration would remain behind deterministic safety/policy gates.

## Stop criterion

The second pass stopped when targeted contradiction searches stopped changing the ranking and the surviving high-impact risks each had either direct evidence or a preregistered $0 falsification. Remaining gaps are explicitly tracked in `evidence/gap-matrix.md`.
