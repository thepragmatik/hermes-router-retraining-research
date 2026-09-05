# Experiment 003 preregistration: Factorized Escalation Value (FEV)

**Spend:** $0 retrospective  
**Primary goal:** estimate how little strong-model ground truth is needed when the router learns **value of escalation** rather than one-shot pairwise winner labels.

## Core hypothesis

For a two-model weak/strong pool, the useful decision quantity is approximately:

`EV_escalate(x) = E[Q_strong - Q_weak | x] - lambda * (C_strong - C_weak)`.

For binary correctness and a conservative positive-gain approximation:

`P(rescue | x) = P(weak fails | x) * P(strong succeeds | weak fails, x)`.

The first factor can often be learned from cheap weak-only outputs plus task-native grading. The second factor requires strong outcomes only on a **small, information-rich subset**, potentially cutting future labeling cost by an order of magnitude.

This directly follows the marginal-gain principle in [RouteLMT](https://arxiv.org/abs/2604.22520), while adapting it to a general weak/strong router.

## Data

- Hash-defined train split for all fitting/simulation.
- Existing weak correctness is visible for all train rows in the retrospective simulation.
- Existing strong correctness is **masked by default** and revealed only according to the frozen oracle budget below.
- Untouched validation split is used once per preregistered candidate family for APGR comparison.
- Sealed test remains untouched.

## Oracle budgets

Simulate future strong-label budgets of:

- 0.5%
- 1.0%
- 2.0%
- 5.0%

of train rows.

At each budget compare two acquisition policies:

A. uniform random;  
B. 80% value/uncertainty/semantic-stratified acquisition + 20% uniform random sentinel.

The random sentinel is mandatory to reduce selection-bias and blind-spot risk.

## Model families

Keep the experiment deliberately small and CPU-friendly:

1. **weak-failure model:** unchanged v1 embedding/head family trained on weak correctness;
2. **rescue model:** simple regularized linear/MF probability model trained only on revealed strong labels among weak-fail rows, with task/domain indicators when available;
3. **FEV score:** product or calibrated expected-gain composition fixed before validation.

No BERT-family classifier, KMeans cluster router, or large tower is authorized.

## Semantic augmentation

Run FEV first without new semantic features. Only if it clears viability, test the frozen semantic additions from Experiment 005 to determine whether domain/performance-memory/OOD signals improve data efficiency.

## Metrics

Primary: validation APGR using the project's existing evaluator.

Secondary:

- APGR vs percentage of strong labels revealed;
- strong-label count needed to come within 0.005 APGR of v1;
- calibration of predicted rescue probability;
- task-level rescue recall;
- fraction of high-value strong rescues missed;
- projected labeling cost at current execution-time model prices.

## Gates

- **G1 viability:** val APGR >= 0.55.
- **G2 meaningful rescue:** val APGR >= 0.60 with <=2% strong labels.
- **G3 replacement:** val APGR >= 0.6459 with <=5% strong labels.
- **G4 economic win:** among G3 passers, select the least strong-label budget within 0.005 APGR of the best candidate.

If no candidate clears G2 at <=2%, do not pay for strong labeling yet; investigate target/model misspecification first.

## Biggest falsification risk

If strong rescue is highly idiosyncratic at the prompt level and cannot be forecast from prompt/task/performance-memory features, sparse strong labels may not generalize. Experiment 000 measures this risk before training.
