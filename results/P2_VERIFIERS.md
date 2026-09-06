# P2 — Deterministic and tool-grounded verifiers

**Date:** 2026-09-06 · **Spend:** $0 · **Prereg:** `experiments/PREREG_P1_P2.md` (frozen before holdout scoring) · Script: `experiments/p1_p2_sampling_verifiers.py` · Raw: `results/P1_P2_raw.txt`

## Verifier families implemented (per prereg)

| family | what it checks | task semantics |
|---|---|---|
| VF | family-aware answer extraction (choice letter / gsm8k number / mbpp code block / non-empty for hellaswag+open) | all |
| VN | numeric parse + finite-range sanity on the extracted gsm8k number | grade-school-math |
| VJ | fenced-JSON validity | any (abstains when no JSON block) |
| VM | mbpp: structural compile; exec-against-prompt-asserts in a sandboxed subprocess | mbpp |

All operate on stored 0-shot responses (list-repr unwrapped first — normalization verified on dev-fit).

## Measurements (dev-fit, weak model unless noted)

| verifier | family | coverage | accept precision | false-reject |
|---|---|---|---|---|
| VF | choice | 0.8576 | 0.3343 (base 0.3058) | 0.0000 |
| VF | gsm8k | 0.0581 | 0.0000 | 0.0054 |
| VF | hellaswag | 1.0000 | 0.2550 (= base) | — |
| VF | mbpp | 1.0000 | 0.3388 (base 0.3388) | — |
| VF | open | 1.0000 | 0.1959 (= base) | — |
| VF (mid Yi) | choice | 0.9999 | 0.6716 (base 0.6466) | 0.0000 |
| VN | gsm8k | 0.0581 | 0.0000 | — |
| VJ | all-dev | 0.0000 | — | — |
| VM compile | mbpp | 0.9770 | ≈ base (no asserts exist) | — |
| VM exec | mbpp | 0.0000 | — | — |

**Key data facts discovered:** stored mbpp prompts contain **zero** `assert` lines (n=304), so tool-execution verification has no foothold in this corpus; no response contains a fenced JSON block; gsm8k responses never emit `####`. VM-exec coverage is 0 by data, not by implementation.

## Frozen keep gate (prereg): accept-precision ≥ 0.90 AND coverage ≥ 5%

**Every family FAILS.** Best case (VF on Yi choice answers) reaches precision 0.6716 — still below the gate and only +2.5pp above the model's base rate. Format validity carries almost no correctness signal in this pool: the weak model almost always emits a well-formed answer; when it is wrong it is confidently wrong in the right format.

End-to-end confirmation: the P1-c verifier-gated cascade scored acc 0.2545 on the pivot holdout (vs v1 0.6475) — the verifier accepts so much that the policy degenerates to "almost always ship weak" (see `results/P1_CHEAP_SAMPLING.md`).

## Verdict

**P2: KILL for this corpus.** No deterministic verifier family available at $0 on stored RouterBench-0shot data reaches the precision gate. Consistent with the preregistered principle: prefer high-precision partial coverage over a broad pseudo-judge — here there is neither precision nor partial coverage. This is a **corpus limitation as much as a method failure**: a deployment where outputs must satisfy machine-checkable contracts (schemas, unit tests, compilers) would re-activate this family, and the adapters implemented here (`vf/vn/vj/vm_*` in the experiment script) are reusable as-is in that setting. Recorded as conditional, not dead.

## What was measured vs not

- Measured: 4 verifier families × 11 models' stored responses × 5 task-family groups, dev-fit selection + single holdout pass of the composed policy.
- Not measurable at $0: verifiers requiring execution environments with real test suites (the corpus's mbpp rows lack asserts), retrieval-grounded checks (no source docs in RouterBench), and numeric recomputation against ground truth (no stored reasoning chains).
