# Verification note — binarization convention (dev-probe, pre-holdout)

**Date:** 2026-09-06 · **Status:** VERIFIED — no exposure occurred (dev-fit + probe only; pivot holdout not yet scored)

## Finding

Raw RouterBench correctness columns are **partial credit** (values 0/0.25/0.5/0.75/1.0
on grade-school-math; 0/1 elsewhere). The pinned derived frame
`~/transfer-bundle/analysis/winrate_table.parquet` — the source of every frozen
metric (weak 0.2289, strong 0.6448, v1 0.6395, APGR 0.6459) — binarizes with
`fillna(0).astype(int)` (i.e. **truncation**: 0.75→0, 0.5→0), per
`build_winrate.py` (verified in source this session).

Therefore this session's P0/P1/P2 scripts, which used the identical
`fillna(0).astype(int)` truncation on the same columns, are **consistent with the
frozen metric convention**. The earlier mid-session concern that truncation was a
bug is resolved: it is the historical convention and must be preserved for
comparability (changing it would make every number incomparable to B1's anchors).

## Consequences

- P0 audit numbers stand as computed (truncation convention, matches frozen
  anchors). Noted: truncation slightly understates mid-tier quality on
  grade-school-math; this affects all policies equally.
- The first P1/P2 run was voided for two REAL bugs, both fixed and dev-probe
  verified before any holdout scoring:
  1. `vf()` received a pandas Series where it expected a scalar → VF coverage
     read 0.0000 (impossible). Fixed; dev-probe coverage now plausible
     (choice 0.858, hellaswag/mbpp/open 1.0, gsm8k 0.059).
  2. `run_surface` scaled cost/frac_strong by the surface's share of all train
     rows (e.g. ×0.1493 on holdout) instead of reporting within-surface means.
  - Extraction patterns were also corrected against dev-fit response formats
    (stored choice answers are bare `"A"`/`"A)"`; gsm8k responses never emit
    `####` — trailing-number pattern added).
- Dev-probe verifier observations (selection inputs, dev-fit only):
  - gsm8k: weak acc 0.4121 (family-level), but VF/NA precision on accepts is
    ~0.0 for the weak model — trailing-number extraction accepts mostly wrong
    answers; VN family likely fails its 0.90 precision gate.
  - choice: accept precision 0.333 ≈ base rate (0.3058) — format check carries
    almost no correctness signal for the weak model.
  - mbpp: prompts-with-asserts = 0 → VM-exec coverage 0 by data; only
    structural compile (precision expected ≈ base rate).

## Rule going forward

All correctness aggregation in this mission uses `fillna(0).astype(int)`
truncation, matching `build_winrate.py`. Any deviation is a protocol amendment,
not a silent choice.
