# Router V1 — provenance and freeze record

**Frozen:** 2026-09-06, tag `router-v1-frozen` (mission repo `hermes-router-retraining-research`).

## What this is

Router V1 = the R5 matrix-factorization router that PASSED its preregistered gate
(TEST APGR **0.6528** >= gate 0.55, single test eval, $0 spend). It is imported here as
the **read-only Tier-0 reference baseline** for the stackable-routing pivot mission
(canonical mission §P0 requires reproducing "historical router v1").

## Artifacts

| File | sha256 |
|---|---|
| `mf_router.pt` | `db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7` |
| `route.py` | `b9fa430d300e3a1693f6bedfad51926a20a5192ebd46a4dfd07d6a877a8aeb46` |

Byte-identity with the source bundle verified at copy time
(`~/transfer-bundle` @ git `fdddc4915bc48664232072cd46b98a2ccd66cf97`).

## Architecture

- Encoder: `BAAI/bge-small-en-v1.5` (384-dim, normalized), via sentence-transformers
  (local HF cache; recorded versions at import: torch 2.8.0, sentence-transformers 5.1.2).
- Head: MF `W1: 384->128`, `v_m` embedding {0=weak,1=strong}, `w2` scalar head;
  `P(strong wins) = sigmoid(score_strong - score_weak)`; route strong iff p >= 0.30.
- Decision rule copied verbatim from `~/transfer-bundle/analysis/train_mf_router.py`
  / `eval_apgr.py`.

## Training provenance

- Data: `~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl`, TRAIN split
  only (frozen-hash split). RouterBench test split SEALED — never accessed.
- Labels: in-distribution win-rate (`analysis/build_winrate.py` /
  `derive_labels.py` in the source bundle).
- Training script: `~/transfer-bundle/analysis/train_mf_router.py` (bundle commit
  `fdddc491…`). Checkpoint is a plain `state_dict` for the `MF` class in `route.py`.

## Frozen operating point (threshold 0.30, pinned 2026-09-04)

Source: `~/transfer-bundle/analysis/deployment_threshold.md` (val-only sweep, n=3626).

- val routed accuracy **0.6395** (weak 0.2289 / strong 0.6448)
- frac_strong **0.7686**; PGR **0.9874**; mean routed cost 0.001442 vs always-strong
  0.003263 (**55.81% projected savings**)
- v1 historical TEST APGR 0.6528 (single eval, already spent; never re-evaluate on test)

## Usage rules for this mission

- `router_v1/` is **read-only**. Experiments may import `route.route()` and read the
  checkpoint. They may never modify files in this directory.
- Any retrain (e.g. a new cheap-tier pool) is a NEW preregistered experiment producing
  a NEW tagged artifact; do not overwrite this one. The prior judge-label v2 retrain
  FAILED its G-PRIMARY gate and was reverted — do not repeat it unchanged.
- Tests guard drift: `tests/test_router_v1_tag.py` fails if `mf_router.pt` hashes
  differ from the recorded value.

## Status

ON-RADAR, version-tagged. Not a deployment artifact: no runtime seam, stale model
pair (mistral-7b vs gpt-4-1106) pending the P0 model-pool audit verdict.
