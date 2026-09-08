# Idea 108 — R7a artifact provenance (extracted without branch switch)

**Extraction date:** 2026-09-09 (AEST). **Method:** `git show feat/generator-pivot-r0:<path>`
from worktree `/Users/rath/src/idea-worktrees/108-multifidelity-synthetic-real`
(branch `108-multifidelity-synthetic-real` checked out throughout; NO checkout of the
generator branch; NO new generation; $0 spend).

## Files

| Local file | Source path on `feat/generator-pivot-r0` | sha256 |
|---|---|---|
| `GENERATOR_PREREG.md` | `GENERATOR_PREREG.md` | `04e221975a7f6d7ff5ec332809c56e235deb8acf57b94eb6a5f4d2f0fa497218` |
| `V1_BASELINE_GAPS.md` | `results/V1_BASELINE_GAPS.md` | `a99f1c090dd5b01c9afe184916a2d55a7b4d2c044453436d5a4b1e12d33b123e` |
| `items_batch7_r7a.jsonl` | `evidence/gen_factory/items_batch7.jsonl` | `ebe088d2255d9857c5fddf6575f10b0fdddfb45a73799ab2aec1c3ef9387371c` |
| `labels_batch7_r7a.jsonl` | `evidence/gen_factory/labels_batch7.jsonl` | `57efb35d5586acc7fc102e478d43d6d8d04f50a7ce28cc5a592fc2265160a3ad` |
| `gen_rejects_batch7_r7a.jsonl` | `evidence/gen_factory/gen_rejects_batch7.jsonl` | `26bc89552799028c082feaf3cb8b6ce8ba8197d804d06fbe9ef5098f4db2a127` |
| `ledger_r7a_rows.jsonl` | `evidence/gen_factory/ledger.jsonl` filtered to `batch_id == r7_b1788903723_47290` | `fbf47628e7171a438bdcc1fb33ac22ccd5aa1be691281cb725eef660a738da84` |
| `ledger_report_gen_factory.json` | `evidence/gen_factory/ledger_report.json` | `229c68a6219aaf76bd4fb5f597868c388a664ec0116a899c1ffa4fe59da0b56c` |

## Synthetic source identity (frozen)

- Batch: `r7_b1788903723_47290`, rung **R7a — strict-gate-only** (R5-strict verifier-only
  K=3 majority key gate; Variant-A agreement arm removed; GEN_JSON_MODE=1; weak
  `z-ai/glm-5.3-flash`, strong `deepseek/deepseek-v4-flash`).
- Per GENERATOR_PREREG R7a outcome: wrong-key 0/11 (PASS), usable 24/26, both_fail 2/26,
  $/usable $0.000069, spend $0.00167, item yield 26/100 (informational FAIL; ladder closed).
- R7a strict is the ONLY synthetic source used in Stage 0 (FR-010); weaker historical
  rungs (R1–R6) are not pooled in.

## Fidelity tag (FR-001)

Every synthetic row loaded from `items_batch7_r7a.jsonl`/`labels_batch7_r7a.jsonl`
carries `fidelity = "synthetic_r7a"` at load time (see
`experiments/108/loaders.py::load_synthetic`). The string `synthetic_r7a` is the only
value the fusion loader accepts for these files; a missing/foreign tag raises
`ProvenanceError`. Synthetic rows can never enter `fidelity in {real_task_native,
real_randomized, benchmark}` frames through the loaders used by `experiments/108/`.

## Real rows

- `winrate_table.parquet` (sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6`,
  matches 103/105 preregs), TRAIN split only (29193 rows), fidelity tag
  `benchmark` (RouterBench-0shot frozen pair outcomes; not task-native accepted outcomes).
- TEST split SEALED: 3678 rows exist per split table; never loaded; the split-value_counts
  membership count is the only permitted touch.
- VAL split (3626) NOT used (historical validation exposed).
