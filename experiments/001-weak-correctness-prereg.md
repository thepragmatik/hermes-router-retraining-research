# Experiment 001 preregistration — Evaluator-First Weak Correctness v0

**Status:** Proposed; analysis only.  
**Spend:** $0. No paid call is authorized by this document.  
**Test split:** SEALED. Do not load or evaluate it.

## Objective

Test whether the deployed router can be retrained from locally reconstructed **weak-model correctness** labels, removing routine strong-model generations from future label acquisition on objective task families.

## Frozen data rules

- Train: existing SHA-256 hash train split only.
- Label reconstruction and error analysis: train only, plus the already-designated calibration subset where explicitly required.
- Validation: existing hash validation split, used only for the frozen candidate comparison.
- Test: never loaded or scored.

## Stage A — evaluator reconstruction audit

1. Inventory train rows by dataset/task family and available true/reference-answer fields.
2. Reconstruct weak-answer correctness from the stored weak response and task-native reference/evaluator. Do **not** use the stored weak correctness column as an input.
3. Compare reconstructed labels to stored weak correctness for audit only.
4. Report exact agreement, false-positive/false-negative counts, and parser/evaluator failure categories per task family.
5. Freeze the accepted objective task-family set before router validation.

### G0 evaluator-fidelity gate

Accepted objective families must achieve **>= 0.99 reconstructed-vs-stored correctness agreement**. Any disagreement must be categorized by a deterministic evaluator/parsing cause before proceeding.

## Stage B — router candidates

Freeze these candidates before validation APGR is observed:

- W0 — stored weak correctness target (sanity ceiling; not a future-labeling method).
- W1 — reconstructed weak correctness on G0-passing objective families; residual rows excluded.
- W2 — reconstructed weak correctness + evidence-mode judge weak-correctness labels only for residual strata whose cross-fit/train reliability clears a fixed error threshold.
- W3 — W2 with reliability weights derived only from cross-fit train error, not verbalized judge confidence directly.

No candidate may be added after validation APGR is observed.

## Training

Keep the v1 MF architecture, bge-small-en-v1.5 embeddings, optimizer family, epochs, batch size, seed and split unchanged. This experiment isolates target/label acquisition.

## Gates

- **G0 fidelity:** >= 0.99 reconstruction agreement on accepted objective families.
- **G1 viability:** validation APGR >= 0.55.
- **G2 meaningful rescue:** validation APGR >= 0.60.
- **G3 replacement:** validation APGR >= 0.6459.

If no reconstructed-label candidate reaches G2, stop this path before spend and proceed to Experiment 002 (Selective Hybrid Labeling v0). If multiple candidates pass G3 and are within 0.005 APGR, select the one with the lowest projected future label cost.

## Reporting

Report evaluator coverage, label reconstruction agreement by task, weak-label prevalence, APGR, PGR/quality curve near the deployed region, excluded/residual-row count, and current-quote projected label cost. Historical cost figures may be shown only as clearly labeled planning comparisons.
