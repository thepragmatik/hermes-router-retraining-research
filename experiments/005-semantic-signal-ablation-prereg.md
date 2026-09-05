# Experiment 005 preregistration: semantic signals without semantic-route repetition

**Spend:** $0  
**Purpose:** test whether semantic routing adds useful information **without re-running the falsified cluster router**.

## Explicit non-goals

Do not:

- train KMeans clusters and assign a fixed weak/strong model to each cluster;
- re-run the failed BERT-family classifier;
- replace `bge-small` merely because a newer embedding model exists.

## Hypothesis

Semantic information is more useful as **conditioning, retrieval support and OOD risk** than as a direct route label.

## Frozen variants

Use the strongest label/target method available after Experiments 000/001/003. Compare:

A. base router, no additional semantic feature;  
B. + task/domain family only;  
C. + kNN historical performance memory only;  
D. + embedding support/OOD distance only;  
E. + task/domain + performance memory + OOD distance.

The kNN feature must aggregate **measured historical outcomes**, not cluster membership. Recommended features are local weak-success rate, local strong-rescue rate, neighbor count/effective support and distance quantiles.

## Why this is not a redo

ContextualRouter reports that retrieving similar historical queries and averaging measured model performance can remain effective with as little as 1% history. That method preserves outcome information at neighbor level; it is not `prompt -> semantic cluster -> fixed route`.

Source: [ContextualRouter, EACL 2026](https://aclanthology.org/2026.eacl-srw.22/).

## Metrics

- validation APGR;
- APGR improvement per added semantic feature family;
- high-value rescue recall;
- OOD-distance vs error curve;
- fraction of validation rows sent to conservative fallback by an OOD guard.

## Gates

Semantic augmentation is retained only if it improves APGR by >=0.005 **or** materially reduces catastrophic/high-value rescue misses without worsening aggregate APGR by >0.002.

If no variant passes, semantic routing stays a policy/observability layer only and is not added to the learned model.
