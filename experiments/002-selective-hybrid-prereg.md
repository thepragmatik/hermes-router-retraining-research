# Experiment 002 preregistration — Selective Hybrid Labeling v0

**Status:** Proposed; no spend authorized by this document.  
**Spend:** $0 for Stage A/B. Any paid continuation requires a separate fail-closed `SPEND_GO=1` gate and total mission spend < $5.  
**Test split:** SEALED. Do not evaluate it.

## Objective

Determine whether task-aware abstention plus a simulated 0.5–2% clean-label budget can lift the existing evidence-mode judge labels from v2 val APGR 0.5304 to at least 0.60 and ideally v1 parity (0.6459), while keeping the current MF architecture fixed.

## Frozen data rules

- Train: existing SHA-256 hash train split only.
- Calibration/error modeling: training data via cross-fitting plus the already-designated calibration subset.
- Validation: existing hash validation split, used only for the pre-registered candidate comparison.
- Test: never loaded or scored.

## Frozen baselines / gates

- v2 control: 0.5304 val APGR (must reproduce within predeclared implementation tolerance).
- G1 viability: >= 0.55.
- G2 meaningful rescue: >= 0.60.
- G3 replacement: >= 0.6459.

## Label policies (freeze before validation)

1. P0 — all existing judge labels (control).
2. P1 — confidence top 75% only.
3. P2 — task-conditioned confidence acceptance, thresholds derived cross-fit on train.
4. P3 — task-conditioned risk model; fixed target auto-label error <= 10% where achievable.
5. P4 — P3 + 0.5% selected clean labels.
6. P5 — P3 + 1.0% selected clean labels.
7. P6 — P3 + 2.0% selected clean labels.
8. P7 — P3 + 1.0% selected + 0.25% random audit clean labels, with reliability-weighted accepted judge labels.

No new policy may be added after any validation APGR is observed.

## Selector features allowed

- dataset/task family;
- primary judge class;
- primary judge self-reported confidence;
- prompt embedding / simple distance features already locally available;
- deterministic answer-format/verifier signals that do not read GT;
- response length/format features of the stored weak answer.

Forbidden: validation/test outcomes or features derived from them.

## Training

Hold router architecture, embedding tower, seed, optimizer family, epochs and split constant unless the v2 reproduction demonstrates a documented mismatch. This experiment isolates label policy.

## Selection rule

Choose the passing policy with the highest validation APGR. If two policies are within 0.005 APGR, choose the one requiring fewer simulated clean labels. If none reaches 0.60, stop this branch before paid labeling.

## Reporting

Report APGR, PGR/call curves, accepted-label coverage, label agreement overall/by task, weak/strong persona sensitivity, simulated clean-label count, and historical-equivalent clean-label cost.
