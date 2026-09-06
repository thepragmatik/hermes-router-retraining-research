# PREREG — P4 trust-stack composition by incremental ablation

**Frozen before any holdout scoring.** Date: 2026-09-06. Spend authorized: $0 (stored
RouterBench-0shot responses only; no API calls). Sealed test split: never loaded.
Validation split: untouched. Pivot holdout: single pass at the end, on frozen arms only.

## 0. Evidence state entering P4 (all committed)

| layer | phase | verdict |
|---|---|---|
| v1 prompt-side router @0.30 | A0/B1 | baseline, all prior gates beaten by it |
| deterministic verifiers (VF/VN/VJ/VM) | P2 | KILLED (best precision 0.67 < 0.90 gate) |
| disagreement → mid-tier escalate | P1b | KILLED (+22.1% cost, −0.8pp acc) |
| verifier-gated pair | P1c | KILLED (acc 0.2545) |
| answer-aware trigger over v1 | P3 | KILLED (all three frozen arms) |
| weak-first oracle ceiling | P1a | +6.7pp / −39.8% (diagnostic, unreachable by v1-anchored triggers) |

**Preregistered revised build order (mission §P4 allows this when P1–P3 evidence
supports it):** the frozen default order (verifier → sampling → confidence) is
already contradicted by P1–P3 kills. Since every P1–P3 dynamic layer died *as an
add-on over v1*, the only honest composition test is whether they pay **as a
stack on the weak-first architecture** — the one architecture with real headroom
(+6.7pp oracle). Build order:

- **L0 = v1 @0.30** (control; the bar).
- **L1 = weak-first re-serialization of v1's partition** (structural control:
  provably equals v1; guards against implementation drift).
- **L2 = L1 + disagreement trigger** (P1b policy, transplanted from v1-anchor to
  weak-first base; mid-tier = Yi-34B-Chat).
- **L3 = L2 + deterministic verifier gate** (VF/VN only — VJ/VM had zero viable
  coverage in P2; VF/VN accept if they parse a confident answer, i.e. act as
  cheap sanity filters, NOT as quality approvers).
- **L4 = L3 + answer-aware confidence (R+V+P probe @ P3's frozen dev-fit
  operating point)**: probes the weak-first cascade's trigger decision rather
  than v1's route decision — the one P3 use the kill does not preclude.

Each layer's marginal effect is measured exactly once, in this order, on
dev-fit. A layer is **retained** only if its marginal delta is not significantly
negative on quality AND not significantly positive on cost (paired bootstrap,
dev-fit). Layers failing retention are removed and the next layer composes on
the surviving stack.

## 1. Dev-fit selection protocol (no holdout exposure)

- Data: dev-fit frame (train minus pivot holdout, n=24,835). Bootstrap: 1,000
  resamples, seed 42, paired by row for deltas.
- Layer composition is deterministic given stored responses (no fitting beyond
  what P1–P3 already froze). The only selection is retain/remove per layer.
- v1 probabilities come from the frozen cache `results/v1_train_probs.npy`
  (BGE-small → MF head, verified exact in P3).

## 2. Frozen qualification gates (single holdout pass)

Surviving stack must beat v1 @0.30 on the pivot holdout under **at least one**
frozen arm (α = 0.05, two-sided paired bootstrap on 4,358 holdout rows):

- **Q1 (quality):** d_acc ≥ +0.020 with d_cost ≤ +0.0002/row.
- **Q2 (cost):** d_cost ≤ −0.0002/row (≥ ~8% cheaper) with d_acc ≥ −0.002.

Additionally, per mission §P4 "for every layer report": marginal quality delta,
marginal cost delta, frontier-call delta (= strong calls), cases uniquely
fixed / newly broken (error-overlap ledger), failure overlap with retained
layers. Latency delta is reported qualitatively (extra cheap call vs frontier
call); no wall-clock data exists in this corpus.

## 3. Outcomes (pre-declared)

- If the surviving stack fails both Q1 and Q2 (or no layer survives): **P4
  outcome = "v1 alone is the stack"** — the composition step yields no paying
  dynamic layer on this corpus, and the mission proceeds to P5 with v1 as the
  only qualified routing layer.
- If Q1 or Q2 passes: P4 outcome = PARTIAL STACK candidate; carry the stack to
  P5 (mid-tier economics) before any promotion talk.
- No retuning after holdout: a failed gate kills the stack as-built (mission
  §14); no threshold moves.

## 4. Integrity clauses

- Binarization convention frozen: `fillna(0).astype(int)` truncation.
- Holdout mask: `/tmp/pivot_holdout_mask.npy` (seed-42 md5 bucket <1500/10000).
- Any crash before holdout results are produced voids that run; harness bugs are
  fixed dev-side and the single complete run is the pass.
- All layer operating points are imported verbatim from P1–P3 frozen code;
  no threshold is re-fit in P4.
