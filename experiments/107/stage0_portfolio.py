#!/usr/bin/env python3
"""Idea 107 Stage 0 — T010..T016, T020..T022, T030..T031, T040..T043 ($0, stored labels only).

Frozen gates are in results/107/PREREG.md (committed BEFORE this file existed).
Data: RouterBench-0shot TRAIN split only. Test split: membership count only (SEALED).
Outputs under results/107/.
"""
import itertools
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WR = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")
PK = os.path.expanduser("~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl")
NON = {"sample_id", "prompt", "eval_name", "oracle_model_to_route_to", "split"}
WEAK = "mistralai/mistral-7b-chat"
STRONG = "gpt-4-1106-preview"
REF_PAIR = (WEAK, "zero-one-ai/Yi-34B-Chat")
RNG = np.random.default_rng(107)

def main():
    wr = pd.read_parquet(WR)
    assert (wr.split == "test").sum() == 3_678  # SEALED membership count only
    split_by_prompt = dict(zip(wr.prompt, wr.split))

    raw = pd.read_pickle(PK)
    raw["split"] = raw.prompt.map(split_by_prompt)
    tr = raw[raw.split == "train"].copy()
    assert len(tr) == 29_193, f"train size {len(tr)} != 29193"

    model_cols = [c for c in tr.columns
                  if c not in NON and c not in (WEAK, STRONG) and "|" not in c]
    models = [WEAK, STRONG] + model_cols
    B = {m: tr[m].fillna(0).astype(int).to_numpy() for m in models}
    C = {m: float(tr[f"{m}|total_cost"].mean()) for m in models}
    N = len(tr)
    task = tr["eval_name"].to_numpy()
    families = sorted(set(task))

    # ---- T011 normalization: binarized correctness (0/1), stored per-row dollar cost.
    # Semantics: RouterBench 0shot correctness labels; NOT preference scores. Recorded.

    # ---- T013 complementarity matrix
    rows = []
    for a, b in itertools.combinations(models, 2):
        ya, yb = B[a], B[b]
        fa, fb = ya == 0, yb == 0
        both = int((fa & fb).sum())
        union = int((fa | fb).sum())
        uniq_a = int((fa & (yb == 1)).sum())   # b rescues a's failures
        uniq_b = int((fb & (ya == 1)).sum())
        extra_cost = C[b] - C[a]
        rows.append({
            "a": a, "b": b,
            "acc_a": round(float(ya.mean()), 4), "acc_b": round(float(yb.mean()), 4),
            "p_b_ok_given_a_fail": round(float(yb[fa].mean()), 4),
            "p_a_ok_given_b_fail": round(float(ya[fb].mean()), 4),
            "cofail_jaccard": round(both / union, 4),
            "uniq_rescue_b_over_a": uniq_a, "uniq_rescue_a_over_b": uniq_b,
            "uniq_rescue_pp_b": round(100 * uniq_a / N, 3),
            "uniq_rescue_pp_a": round(100 * uniq_b / N, 3),
            "extra_cost_b_vs_a": round(extra_cost, 7),
            "uniq_rescues_per_extra_dollar_b": round(uniq_a / max(extra_cost, 1e-12), 1),
        })
    comp = pd.DataFrame(rows)
    comp.to_csv("results/107/complementarity.csv", index=False)

    def oracle_quality(S):
        """mean_i max_{m in S} Q_im"""
        M = np.vstack([B[m] for m in S])
        return float(M.max(axis=0).mean())

    def oracle_cost(S):
        """expected per-row cost of the min-cost correct-selection oracle:
        for rows where any m in S is correct, pay the cheapest correct model; else
        pay the cheapest model in S (wrong everywhere)."""
        M = np.vstack([B[m] for m in S])           # K x N
        Cs = np.array([C[m] for m in S])[:, None]  # K x 1
        ok_cost = np.where(M == 1, Cs, np.inf).min(axis=0)
        fallback = Cs.min()
        return float(np.where(np.isfinite(ok_cost), ok_cost, fallback).mean())

    def all_called_cost(S):
        return float(sum(C[m] for m in S))

    # ---- T014 brute force subsets <=3
    single = sorted(models, key=lambda m: -oracle_quality([m]))
    best_single = single[0]
    best_single_q = oracle_quality([best_single])
    best_single_cost = C[best_single]
    cheapest = min(models, key=lambda m: C[m])
    full_oracle_q = oracle_quality(models)
    ref_q = oracle_quality(list(REF_PAIR))
    ref_cost = oracle_cost(list(REF_PAIR))

    bf_rows = []
    for k in (1, 2, 3):
        for S in itertools.combinations(models, k):
            bf_rows.append({"subset": "|".join(S), "size": k,
                            "oracle_quality": round(oracle_quality(S), 5),
                            "oracle_cost": round(oracle_cost(S), 7),
                            "all_called_cost": round(all_called_cost(S), 7)})
    bf = pd.DataFrame(bf_rows)
    bf.to_csv("results/107/portfolio_frontier.csv", index=False)

    # ---- T015 cost-aware greedy (OBJ-C: quality - lambda*min-cost-in-pool) + verification
    # lambda frozen: the quality-per-dollar slope between the best and cheapest single model
    accs = {m: float(B[m].mean()) for m in models}
    lam = (accs[best_single] - accs[cheapest]) / max(C[best_single] - C[cheapest], 1e-12)

    def min_call_cost(S):
        return min(C[m] for m in S)

    def obj_c(S):
        return oracle_quality(S) - lam * min_call_cost(S)

    greedy, log = [], []
    for step in range(3):
        best_gain, best_m = -1e18, None
        for m in models:
            if m in greedy:
                continue
            g = obj_c(greedy + [m]) - (obj_c(greedy) if greedy else 0.0)
            if g > best_gain:
                best_gain, best_m = g, m
        greedy.append(best_m)
        log.append({"step": step + 1, "added": best_m, "obj_c": round(obj_c(greedy), 5)})
    greedy_best3 = sorted(greedy[:3])
    bf_best_objc3 = sorted(max((list(s) for s in itertools.combinations(models, 3)), key=obj_c))
    greedy_matches_bf = greedy_best3 == bf_best_objc3

    # ---- selected portfolio: oracle-quality-optimal 3-subset subject to G1 cost gate.
    # Correction note: results/107/selection_correction_note.md — maximize attainable
    # quality subject to the size/cost constraint (the spec's objective), not cheapest
    # passing subset.
    cand3 = bf[bf["size"] == 3].copy()
    cand3["cost_vs_best_single"] = cand3["all_called_cost"] / best_single_cost
    eligible3 = cand3[(cand3["oracle_quality"] - best_single_q) * 100 >= 2.0]
    if len(eligible3):
        top_q = eligible3["oracle_quality"].max()
        sel = sorted(eligible3[eligible3["oracle_quality"] >= top_q - 1e-9]
                     .sort_values("all_called_cost").iloc[0]["subset"].split("|"))
    else:
        sel = bf_best_objc3
        # no 3-subset passes G1 cost gate on all-called cost; keep greedy set for diagnostics

    # marginal contributions (G2)
    def marginal(m, S):
        if not len(S):
            return 100.0 * accs[m], 0.0
        prev = np.vstack([B[x] for x in S]).max(axis=0)
        uniq_only_m = float(((B[m] == 1) & (prev == 0)).mean()) * 100
        cost_before, cost_after = oracle_cost(S), oracle_cost(S + [m])
        rel_cost = (cost_before - cost_after) / cost_before * 100
        return uniq_only_m, rel_cost

    marginals, S_acc = [], []
    for m in sel:
        u, r = marginal(m, S_acc)
        marginals.append({"model": m, "uniq_rescue_pp_after_prev": round(u, 3),
                          "cost_improvement_pct_after_prev": round(r, 2)})
        S_acc.append(m)

    # ---- T030/T031 realizability
    # (1) per-task best-model policy (task id legitimately known)
    task_df = pd.DataFrame({m: B[m] for m in models})
    task_df["task"] = task
    best_model_per_task = task_df.groupby("task").mean().idxmax(axis=1)
    proxy1_q = float(np.vstack([B[best_model_per_task[t]] for t in task]).mean())
    proxy1_cost = float(np.mean([C[best_model_per_task[t]] for t in task]))

    # (2) simple regularized linear router (per-model correctness scorer, argmax)
    from numpy.linalg import solve
    X = np.column_stack([
        np.ones(N),
        np.log1p(tr["prompt"].str.len()).to_numpy(),
        (pd.Categorical(task).codes[:, None] == np.arange(len(families))[None, :]).astype(float),
    ])
    idx = RNG.permutation(N)
    i_tr, i_ho = idx[: int(0.8 * N)], idx[int(0.8 * N):]

    def fit_router(models_subset):
        Ps, ms = [], list(models_subset)
        for m in ms:
            y = B[m][i_tr]
            # proper ridge least squares: w = (X'X + lam I)^-1 X'y ; score = clip(w.x, 0, 1)
            XtX = X[i_tr].T @ X[i_tr] + 10.0 * np.eye(X.shape[1])
            w = solve(XtX, X[i_tr].T @ y)
            Ps.append(np.clip(X[i_ho] @ w, 0.0, 1.0))
        P = np.vstack(Ps)
        chosen = P.argmax(axis=0)
        routed_q = float(np.array([B[ms[c]][j] for j, c in enumerate(chosen)]).mean())
        routed_cost = float(np.array([C[ms[c]] for c in chosen]).mean())
        return routed_q, routed_cost

    sel_hold = None
    if len(sel) >= 2:
        rq, rc = fit_router(sel)
        sel_hold = {"router": "regularized-linear per-model correctness argmax (80/20)",
                    "models": sel, "holdout_quality": round(rq, 4),
                    "holdout_cost_per_row": round(rc, 7)}

    # ---- gates
    portfolio_q = oracle_quality(sel)
    portfolio_cost = oracle_cost(sel)
    g1_q_gain_pp = 100 * (portfolio_q - best_single_q)
    g1_cost_ratio = all_called_cost(sel) / best_single_cost
    g1_cost_red_vs_ref = (100 * (1 - portfolio_cost / ref_cost)
                          if portfolio_q >= ref_q - 1e-9 else None)
    g1_pass = bool((g1_q_gain_pp >= 2.0 and g1_cost_ratio <= 2.0)
                   or (g1_cost_red_vs_ref is not None and g1_cost_red_vs_ref >= 15.0))

    g3 = {}
    if sel_hold:
        poracle_ho = np.vstack([B[m] for m in sel]).max(axis=0)
        bs_ho = float(poracle_ho[i_ho].mean())
        single_ho = float(B[best_single][i_ho].mean())
        oracle_gain_ho = bs_ho - single_ho
        captured = sel_hold["holdout_quality"] - single_ho
        frac = captured / oracle_gain_ho if oracle_gain_ho > 0 else 0.0
        cost_adv_ok = sel_hold["holdout_cost_per_row"] <= best_single_cost
        g3 = {"holdout_portfolio_oracle": round(bs_ho, 4),
              "holdout_best_single": round(single_ho, 4),
              "captured_fraction": round(float(frac), 4),
              "holdout_routed_cost": sel_hold["holdout_cost_per_row"],
              "cost_advantage_kept": bool(cost_adv_ok),
              "pass": bool(frac >= 0.35 and cost_adv_ok)}

    # ---- T040 bootstrap selection frequency (rows)
    sel_counts = {}
    for b in range(200):
        bs = RNG.choice(N, N, replace=True)
        Bb = {m: B[m][bs] for m in models}

        def q(S):
            return float(np.vstack([Bb[m] for m in S]).max(axis=0).mean())
        best = max(itertools.combinations(models, 3), key=q)
        key = "|".join(sorted(best))
        sel_counts[key] = sel_counts.get(key, 0) + 1
    top_boot = sorted(sel_counts.items(), key=lambda kv: -kv[1])[:5]

    # ---- T041 price stress (+-30%) and leave-one-model-out
    stress = {}
    for scale, name in ((0.7, "price_x0.7"), (1.3, "price_x1.3")):
        Cs = {m: C[m] * scale for m in models}

        def obj_s(S):
            return oracle_quality(S) - lam * min(Cs[m] for m in S)
        stress[name] = "|".join(sorted(
            max(itertools.combinations(models, 3), key=obj_s)))
    loms = {}
    for m in models:
        pool_wo = [x for x in models if x != m]
        loms[m] = "|".join(sorted(max(
            itertools.combinations(pool_wo, 3), key=oracle_quality)))

    # ---- T042 leave-one-task-family-out stability
    tfo_counts = {}
    for fam in families:
        mask = task != fam
        Bf = {m: B[m][mask] for m in models}

        def qf(S):
            return float(np.vstack([Bf[m] for m in S]).max(axis=0).mean())
        best = max(itertools.combinations(models, 3), key=qf)
        key = "|".join(sorted(best))
        tfo_counts[key] = tfo_counts.get(key, 0) + 1
    top_tfo = sorted(tfo_counts.items(), key=lambda kv: -kv[1])[:3]

    # ---- T043 provider/model unavailability fallback
    fallbacks = {m: {"quality": round(oracle_quality([x for x in sel if x != m]), 4),
                     "cost": round(oracle_cost([x for x in sel if x != m]), 7)}
                 for m in sel}

    out = {
        "n_train": N, "n_models": len(models), "models": models,
        "costs_per_call": {k: round(v, 7) for k, v in C.items()},
        "best_single_quality": {"model": best_single, "acc": round(best_single_q, 4),
                                "cost": round(best_single_cost, 7)},
        "cheapest_model": {"model": cheapest, "acc": round(accs[cheapest], 4),
                           "cost": round(C[cheapest], 7)},
        "full_pool_oracle_quality": round(full_oracle_q, 4),
        "ref_pair": {"models": list(REF_PAIR), "oracle_quality": round(ref_q, 4),
                     "oracle_cost": round(ref_cost, 7)},
        "selected_portfolio": sel,
        "portfolio_oracle_quality": round(portfolio_q, 4),
        "portfolio_oracle_cost": round(portfolio_cost, 7),
        "portfolio_all_called_cost": round(all_called_cost(sel), 7),
        "G1": {"q_gain_pp_vs_best_single": round(g1_q_gain_pp, 3),
               "cost_ratio_vs_best_single_allcalled": round(g1_cost_ratio, 3),
               "cost_reduction_vs_ref_pair_at_matched_q": (
                   round(g1_cost_red_vs_ref, 2) if g1_cost_red_vs_ref is not None else None),
               "pass": g1_pass},
        "G2": {"marginals": marginals,
               "pass": bool(all(m["uniq_rescue_pp_after_prev"] >= 0.5
                                or m["cost_improvement_pct_after_prev"] >= 5.0
                                for m in marginals[1:]))},
        "G3": {**g3} if g3 else {"pass": False, "note": "no realizable router tested"},
        "G4": {"bootstrap_top3_sets": top_boot,
               "selected_in_bootstrap_pct": round(
                   100 * sel_counts.get("|".join(sorted(sel)), 0) / 200, 1),
               "leave_one_task_family_out_top": top_tfo,
               "selected_in_tfo_of": f"{tfo_counts.get('|'.join(sorted(sel)), 0)}/{len(families)}",
               "price_stress_selections": stress,
               "leave_one_model_out_best3": loms},
        "greedy_vs_bruteforce": {"greedy_top3": greedy_best3,
                                 "bf_best3_by_objc": bf_best_objc3,
                                 "greedy_steps": log,
                                 "match": bool(greedy_matches_bf)},
        "realizability_task_policy": {"quality": round(proxy1_q, 4),
                                      "cost": round(proxy1_cost, 7)},
        "realizability_router": sel_hold,
        "fallback_if_one_model_down": fallbacks,
    }
    with open("results/107/stage0_results.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
