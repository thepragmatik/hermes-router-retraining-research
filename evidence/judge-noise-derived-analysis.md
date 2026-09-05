# Derived analysis: what the failed judge labels are actually telling us

**Date:** 2026-09-05  
**Status:** algebraic analysis from mission-provided aggregate rates; no new dataset access or paid calls.

## Inputs

The mission reports, on the 29,170-row judge-labeled train set:

- ground truth says **needs strong** on 78.3% of rows;
- judge says **needs strong** on 67.5% of rows;
- judge-vs-ground-truth agreement = **0.8382**.

Let `Y=1` mean ground truth needs strong and `J=1` mean the judge says needs strong.

Given prevalence `P(Y=1)=a`, predicted-positive rate `P(J=1)=b`, and accuracy `A`, the normalized confusion matrix is identified:

`TP = (A + a + b - 1) / 2`.

Using the reported rates gives approximately:

| Cell | Fraction of all rows | Approx. rows out of 29,170* |
|---|---:|---:|
| TP: judge says strong, truth strong | 64.81% | 18,905 |
| FP: judge says strong, truth weak | 2.69% | 785 |
| FN: judge says weak, truth strong | 13.49% | 3,935 |
| TN: judge says weak, truth weak | 19.01% | 5,545 |

\*Approximate because the published prevalence numbers are rounded.

Derived conditional rates:

- **precision of `judge says strong` ≈ 96.0%**;
- recall of true strong-needed ≈ 82.8%;
- specificity ≈ 87.6%;
- **negative predictive value of `judge says weak` ≈ 58.5%**.

Allowing for ordinary rounding of the reported inputs keeps the conclusion intact: strong-label precision is about **95.94–96.09%**, while the weak-label NPV is only about **58.39–58.59%**.

## Why this matters

The failed v2 label set is **not merely an 83.82%-accurate noisy dataset**. It is an **asymmetric label source**:

- a judge `needs strong` label is usually trustworthy;
- a judge `weak sufficient` label is dangerously ambiguous—roughly 41.5% of that predicted-weak region is actually strong-needed under the project ground truth.

That explains why ordinary hard-label training can distort ranking even with high aggregate agreement: the false negatives are concentrated exactly in the economically dangerous class.

## New design implication: do not treat judge-weak as a negative label

A better three-state label factory is:

```text
ESCALATE_CONFIRMED  = high-precision judge positive or exact strong-rescue evidence
WEAK_CONFIRMED      = deterministic weak correctness / trusted verifier evidence
UNKNOWN             = judge says weak without independent confirmation, disagreement, OOD, residual tasks
```

This suggests **positive-unlabeled (PU) or semi-supervised learning**, not conventional binary supervised learning over all judge labels.

Classic non-negative PU learning provides a principled way to train from positive and unlabeled examples while controlling overfitting: [Kiryo et al., NeurIPS 2017](https://papers.nips.cc/paper/2017/hash/7cce53cf90577442771720a370c3c723-Abstract.html).

### Important caveat

Off-the-shelf PU learning often assumes the labeled positives are selected under conditions such as SCAR (selected completely at random) or known variants. Here the judge's positive selection is likely **instance-dependent**: task, difficulty and semantic structure affect whether it emits a strong label. Its positives also have ~4% contamination rather than being perfectly clean.

Therefore the recommended test is not “install nnPU and trust it.” It is an ablation:

1. judge positives + everything else unlabeled;
2. confidence-restricted judge positives + unlabeled;
3. task/semantic-stratified positive propensities;
4. trusted deterministic weak negatives added where available;
5. compare against the failed hard-label baseline.

See [`../experiments/004-one-sided-pu-prereg.md`](../experiments/004-one-sided-pu-prereg.md).

## Risk retired by this analysis

This algebra retires one assumption from the first memo: **the judge label source should not be summarized by its aggregate 0.8382 agreement.** Its two polarities have radically different reliability. Any future judge-label method must report precision/recall or conditional error by label and task, not just accuracy/agreement.
