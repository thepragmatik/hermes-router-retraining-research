#!/usr/bin/env python3
"""Phase B2/P0 — model-pool audit from stored RouterBench labels ($0 spend).

Question (canonical mission §P0): is the historical weak tier still the right
foundation, or is model choice a bigger lever than routing sophistication?

For every stored non-control model, on the frozen TRAIN split only (29,193 rows):
  - aggregate binarized accuracy;
  - rescue rate on weak-model failures;
  - unique successes vs the historical weak model;
  - co-failure Jaccard vs the historical weak model;
  - mean stored cost per call (RouterBench-recorded dollars).
Plus: the disagreement-escalation naive cascade operating point and the
complementarity-per-cost ranking that drives the P0 selection rule.

Data sources (read-only):
  ~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl  (scores, costs)
  ~/transfer-bundle/analysis/winrate_table.parquet              (frozen hash split)
Test rows: only a membership count is taken from the split table; they are never
loaded, inspected, or scored (SEALED).

Run: python3 experiments/p0_model_pool_audit.py > results/P0_MODEL_POOL_raw.txt
"""
import itertools
import os

import numpy as np
import pandas as pd

WR = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")
PK = os.path.expanduser(
    "~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl")
NON = {"sample_id", "prompt", "eval_name", "oracle_model_to_route_to", "split"}
WEAK = "mistralai/mistral-7b-chat"
STRONG = "gpt-4-1106-preview"


def main():
    wr = pd.read_parquet(WR)
    assert (wr.split == "test").sum() == 3_678  # exists and stays untouched
    split_by_prompt = dict(zip(wr.prompt, wr.split))

    raw = pd.read_pickle(PK)
    raw["split"] = raw.prompt.map(split_by_prompt)
    tr = raw[raw.split == "train"].copy()
    assert len(tr) == 29193, f"train size {len(tr)} != 29193"

    model_cols = [c for c in tr.columns
                  if c not in NON and c not in (WEAK, STRONG) and "|" not in c]
    weak = tr[WEAK].fillna(0).astype(int).to_numpy()
    strong = tr[STRONG].fillna(0).astype(int).to_numpy()
    weak_fail = weak == 0
    w_acc, s_acc = float(weak.mean()), float(strong.mean())
    cost = {WEAK: float(tr[f"{WEAK}|total_cost"].mean()),
            STRONG: float(tr[f"{STRONG}|total_cost"].mean())}

    print(f"train rows {len(tr)} | weak acc {w_acc:.4f} (${cost[WEAK]:.6f}/call) "
          f"| strong acc {s_acc:.4f} (${cost[STRONG]:.6f}/call)")
    print(f"P(strong ok | weak fail) = {strong[weak_fail].mean():.4f} "
          f"(upper bound on any single-tier rescue)")

    rows = []
    for m in model_cols:
        acc = tr[m].fillna(0).astype(int).to_numpy()
        mc = float(tr[f"{m}|total_cost"].mean())
        both_wrong = int(((acc == 0) & weak_fail).sum())
        acc_only_wrong = int(((acc == 0) & (weak == 1)).sum())
        union = both_wrong + acc_only_wrong + int(((acc == 1) & weak_fail).sum())
        uniq = int(((acc == 1) & weak_fail).sum())
        rows.append({
            "model": m,
            "train_acc": round(float(acc.mean()), 4),
            "rescue_rate_on_weak_fail": round(float(acc[weak_fail].mean()), 4),
            "unique_successes_vs_weak": uniq,
            "cofail_jaccard_vs_weak": round(both_wrong / union, 4),
            "mean_cost_per_call": round(mc, 7),
            "cost_x_weak": round(mc / cost[WEAK], 2),
            "unique_rescues_per_extra_dollar": round(
                uniq / max(mc - cost[WEAK], 1e-12), 1),
        })
    out = pd.DataFrame(rows).sort_values(
        ["rescue_rate_on_weak_fail", "train_acc"], ascending=False)
    print()
    print(out.to_string(index=False))
    out.to_csv("results/p0_model_pool_screen.csv", index=False)

    # ---- pairwise co-failure Jaccard across the pool (error-overlap evidence)
    B = {WEAK: weak, STRONG: strong}
    B.update({m: tr[m].fillna(0).astype(int).to_numpy() for m in model_cols})
    print("\npairwise co-failure Jaccard (top complements to the weak model):")
    jvals = []
    for a, b in itertools.combinations(model_cols, 2):
        wa, wb = B[a] == 0, B[b] == 0
        jvals.append(((wa & wb).sum() / (wa | wb).sum(), a, b))
    for j, a, b in sorted(jvals)[:5]:
        print(f"  {a} + {b}: {j:.4f}")

    # ---- naive heterogeneous cascade operating point (no learned layer):
    # answer with weak AND Yi; disagreement -> escalate to strong.
    yi = B["zero-one-ai/Yi-34B-Chat"]
    c_yi = float(tr["zero-one-ai/Yi-34B-Chat|total_cost"].mean())
    agree = weak == yi
    routed = np.where(agree, weak, strong)
    acc_dis = float(routed.mean())
    frac_strong = float(1 - agree.mean())
    cost_dis = ((1 - frac_strong) * (cost[WEAK] + c_yi)
                + frac_strong * cost[STRONG])
    pgr = (acc_dis - w_acc) / (s_acc - w_acc)
    print(f"\nnaive cascade (weak+Yi disagree->strong): acc {acc_dis:.4f} "
          f"frac_strong {frac_strong:.4f} cost/row ${cost_dis:.6f} "
          f"PGR {pgr:.4f} savings {(1 - cost_dis / cost[STRONG]) * 100:.1f}%")

    # ---- frontier rows for results/frontier.csv (train-side stored-label sims)
    print("\nfrontier rows (train, stored-label simulation):")
    for name, acc_v, cost_v, note in [
        ("always_weak", w_acc, cost[WEAK], ""),
        ("always_strong_simulated", s_acc, cost[STRONG], ""),
        ("cascade_disagree_weak+Yi", acc_dis, cost_dis,
         "no learned layer"),
        ("router_v1_tagged", 0.6395, 0.001442,
         "val-side operating point from B1 (tag router-v1-frozen, thr 0.30)"),
    ]:
        print(f"{name},{acc_v:.4f},{cost_v:.7f},0,0,0,0,,,{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
