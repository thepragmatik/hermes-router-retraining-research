#!/usr/bin/env python3
"""Idea 108 Stage 0 — frozen pipeline (T010-T013, T020-T025, T030-T033).

Executes results/108/PREREG.md + results/108/PREREG_ERRATUM.md exactly.
$0 spend, deterministic, no network.
Outputs: results/108/shift_report.json, budget_curve.csv, stage0_gate.json.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loaders import WORKTREE, load_real_train, load_synthetic  # noqa: E402

RESULTS = os.path.join(WORKTREE, "results", "108")
EMB_CACHE = os.path.join(RESULTS, "emb_cache.npz")
BGE_SNAPSHOT = os.path.expanduser(
    "~/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/"
    "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a")

# ---- frozen constants (PREREG + ERRATUM) ----
SEED = 108
GAMMA = 50.0
DEV_FRAC = 0.70
BUDGETS = [0.005, 0.01, 0.02, 0.05, 0.10]
BUDGET_LABELS = ["0.5%", "1%", "2%", "5%", "10%"]
W_SYN_GRID = [0.05, 0.25, 1.0]
M_CLS_GRID = [1, 12]
KF = 5
MIN_CLASS = 10
PROP_SIM_PER_GROUP = 40
BOOT_SEEDS = list(range(10))
CI_RESAMPLES = 2000
LOW_BUDGETS = ("0.5%", "1%", "2%")
CORRECTION_FLAGS = ("D_label", "D_embed", "D_len")


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- embeddings
def get_embeddings(texts_real, texts_syn):
    if os.path.exists(EMB_CACHE):
        z = np.load(EMB_CACHE)
        if int(z["n_real"]) == len(texts_real) and int(z["n_syn"]) == len(texts_syn):
            return z["real"], z["syn"]
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(BGE_SNAPSHOT, device="cpu")
    log("embedding real train prompts...")
    er = m.encode(texts_real, batch_size=128, show_progress_bar=False,
                  normalize_embeddings=True).astype(np.float32)
    log("embedding synthetic questions...")
    es = m.encode(texts_syn, batch_size=128, show_progress_bar=False,
                  normalize_embeddings=True).astype(np.float32)
    np.savez(EMB_CACHE, real=er, syn=es, n_real=len(er), n_syn=len(es))
    return er, es


# ---------------------------------------------------------------- model utils
def fit_logreg(X, y, sample_weight=None):
    clf = LogisticRegression(C=1.0, max_iter=2000)
    clf.fit(X, y, sample_weight=sample_weight)
    return clf


def fit_warm(X, y, warm, max_iter=100, tol=1e-4):
    """Arm 3: bounded warm-start real update of the synthetic-initialized model."""
    clf = LogisticRegression(C=1.0, max_iter=max_iter, tol=tol, warm_start=True)
    clf.coef_ = warm.coef_.copy()
    clf.intercept_ = warm.intercept_.copy()
    clf.classes_ = warm.classes_.copy()
    clf.fit(X, y)
    return clf


def predict_p(clf, X):
    return clf.predict_proba(X)[:, list(clf.classes_).index(1)]


def policy_utility(p, weak_correct, strong_correct, cost_w, cost_s, thresh=0.5):
    """E2: route STRONG iff p(y=1 = need-strong) >= 0.5, else weak.
    Returns (U, quality, mean_cost)."""
    route_strong = p >= thresh
    r = np.where(route_strong, strong_correct, weak_correct)
    c = np.where(route_strong, cost_s, cost_w)
    return (float((r - GAMMA * c).mean()), float(r.mean()), float(c.mean()))


# ---------------------------------------------------------------- CV (arm 4)
def joint_sample_weight(n_real, n_syn, w_syn, m_cls, label_syn):
    return np.concatenate([
        np.ones(n_real),
        np.full(n_syn, w_syn) * np.where(label_syn == "need_strong", m_cls, 1.0),
    ])


def cv_joint(Xr, yr, Xs, ys, label_syn, m_cls_grid=M_CLS_GRID):
    """Frozen CV on budget real rows only (PREREG 3.4): KFold(5, shuffle=False),
    minimize out-of-fold log loss; ties -> smaller w_syn, then smaller m_cls."""
    best = (None, None, np.inf)
    kf = KFold(n_splits=KF, shuffle=False)
    for m_cls in m_cls_grid:
        sw_syn_base = np.where(label_syn == "need_strong", m_cls, 1.0).astype(np.float64)
        for w in W_SYN_GRID:
            losses = []
            for trn, val in kf.split(Xr):
                sw = np.concatenate([np.ones(len(trn)), w * sw_syn_base])
                try:
                    clf = fit_logreg(np.vstack([Xr[trn], Xs]),
                                     np.concatenate([yr[trn], ys]), sample_weight=sw)
                    pv = np.clip(predict_p(clf, Xr[val]), 1e-6, 1 - 1e-6)
                    yv = yr[val]
                    losses.append(float(-np.mean(
                        yv * np.log(pv) + (1 - yv) * np.log(1 - pv))))
                except Exception:
                    losses.append(np.inf)
            ll = float(np.mean(losses))
            if ll < best[2] - 1e-12:
                best = (w, m_cls, ll)
    if best[0] is None:
        best = (W_SYN_GRID[0], M_CLS_GRID[0], np.inf)
    return best[0], best[1], best[2]


def cv_loss_arm3(Xr, yr, Xs, ys):
    """E5.1: arm-3 (pretrain) dev-side CV log loss, same KFold as arm 4."""
    kf = KFold(n_splits=KF, shuffle=False)
    losses = []
    for trn, val in kf.split(Xr):
        try:
            warm = fit_logreg(Xs, ys)
            clf = fit_warm(Xr[trn], yr[trn], warm)
            pv = np.clip(predict_p(clf, Xr[val]), 1e-6, 1 - 1e-6)
            yv = yr[val]
            losses.append(float(-np.mean(yv * np.log(pv) + (1 - yv) * np.log(1 - pv))))
        except Exception:
            losses.append(np.inf)
    return float(np.mean(losses))


# ---------------------------------------------------------------- shift (T011)
def compute_shift(syn, tr, emb_real, emb_syn, y_all):
    d = {}
    p_syn = float((syn.label == "need_strong").mean())
    unt = tr.untied.to_numpy()
    p_real = float(y_all[unt].mean())
    d["D_label"] = {"p_syn_need_strong": p_syn, "p_real_y1": p_real,
                    "abs_delta": abs(p_syn - p_real),
                    "flag": bool(abs(p_syn - p_real) > 0.15)}
    sims = emb_syn @ emb_real.T
    nn = sims.max(axis=1)
    rng = np.random.default_rng(SEED)
    ref_idx = rng.permutation(emb_real.shape[0])[:2000]
    rest = rng.permutation(emb_real.shape[0])[2000:4000]
    ref = (emb_real[ref_idx] @ emb_real[rest].T).max(axis=1)
    ref_mean = float(ref.mean())
    d["D_embed"] = {"syn_mean_nn_cos": float(nn.mean()),
                    "syn_min_nn_cos": float(nn.min()),
                    "syn_max_nn_cos": float(nn.max()),
                    "real_reference_mean_nn_cos": ref_mean,
                    "flag": bool(float(nn.mean()) < ref_mean - 0.10)}
    qlen_syn = syn.question.str.len().astype(float)
    qlen_real = tr.prompt.str.len().astype(float)
    lr = float(np.log(qlen_syn.median() / qlen_real.median()))
    d["D_len"] = {"median_syn_chars": float(qlen_syn.median()),
                  "median_real_chars": float(qlen_real.median()),
                  "log_ratio": lr, "flag": bool(abs(lr) > 0.5)}
    d["D_pair"] = {"syn_weak_ok": float((syn.label == "weak_ok").mean()),
                   "syn_need_strong": p_syn,
                   "real_weak_correct": float(tr.weak_correct.mean()),
                   "real_strong_correct": float(tr.strong_correct.mean()),
                   "real_y1_rate_untied": p_real,
                   "note": "report only (PREREG 6)"}
    d["D_verifier"] = {"syn_verifier_types": syn.verifier.apply(
        lambda v: v["type"]).value_counts().to_dict(),
        "real_verifier_column": None,
        "note": "structural: real rows carry benchmark-graded outcomes, no "
                "verifier/key column; evidence tiers VI-4 vs VI-6 (PREREG 6)"}
    d["D_task"] = {"synthetic_eval_name": None,
                   "note": "task strata structurally missing for synthetic rows "
                           "(mined seed taxonomy) (PREREG 6)"}
    d["flags_for_correction"] = [k for k in CORRECTION_FLAGS if d[k]["flag"]]
    return d


# ---------------------------------------------------------------- simulators (T012)
def build_simulators(dev_untied, eval_name, y_all, emb_real):
    """Prop-Sim (clean labels, group under-sampling) and Flip-Sim (100% corruption),
    40 rows/group under the frozen permutation (PREREG 5)."""
    dev_name = eval_name[dev_untied]
    sim_rows = []
    counts = {}
    for i, g in enumerate(dev_name):
        if counts.get(g, 0) < PROP_SIM_PER_GROUP:
            counts[g] = counts.get(g, 0) + 1
            sim_rows.append(i)
    sim_rows = np.array(sim_rows)
    idx = dev_untied[sim_rows]
    prop = {"rows": idx, "y": y_all[idx].copy()}
    flip = {"rows": idx, "y": 1 - y_all[idx].copy()}
    return {"prop_sim": prop, "flip_sim": flip, "n_groups": len(counts)}


def gate2_eval(sim, X_real_fn, Xs_syn_or_simX, ys_sim, label_syn, eval_untied,
               y_all, wc_all, sc_all, cw_all, cs_all, real_idx):
    """B1/B2: weighted-joint (sim labels, m_cls=1, w_syn CV) + tiny real vs real-only."""
    Xr = X_real_fn(real_idx)
    yr = y_all[real_idx]
    Xs = Xs_syn_or_simX
    ys = ys_sim
    lab_syn = np.array(["need_strong"] * len(ys))  # m_cls fixed 1 -> label content unused
    w_sel, _, _ = cv_joint(Xr, yr, Xs, ys, lab_syn, m_cls_grid=[1])
    sw = joint_sample_weight(len(yr), len(ys), w_sel, 1, lab_syn)
    clf_j = fit_logreg(np.vstack([Xr, Xs]), np.concatenate([yr, ys]), sample_weight=sw)
    clf_r = fit_logreg(Xr, yr)
    Xe = X_real_fn(eval_untied)
    Uj = policy_utility(predict_p(clf_j, Xe), wc_all[eval_untied], sc_all[eval_untied],
                        cw_all[eval_untied], cs_all[eval_untied])[0]
    Ur = policy_utility(predict_p(clf_r, Xe), wc_all[eval_untied], sc_all[eval_untied],
                        cw_all[eval_untied], cs_all[eval_untied])[0]
    return {"U_fusion": Uj, "U_real_only": Ur, "dU": Uj - Ur, "w_syn_sel": w_sel}


# ---------------------------------------------------------------- main
def main():
    syn = load_synthetic()
    tr = load_real_train()
    log(f"loaded: syn={len(syn)} real={len(tr)}")

    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(tr))
    n_dev = int(round(DEV_FRAC * len(tr)))
    dev_idx, eval_idx = perm[:n_dev], perm[n_dev:]
    untied = tr.untied.to_numpy()
    dev_untied = dev_idx[untied[dev_idx]]
    eval_untied = eval_idx[untied[eval_idx]]
    log(f"dev={len(dev_idx)} eval={len(eval_idx)} dev_untied={len(dev_untied)} "
        f"eval_untied={len(eval_untied)}")

    emb_real, emb_syn = get_embeddings(tr.prompt.tolist(), syn.question.tolist())
    log("embeddings ready", emb_real.shape, emb_syn.shape)

    y_all = tr.y.to_numpy()
    wc_all = tr.weak_correct.to_numpy(np.float64)
    sc_all = tr.strong_correct.to_numpy(np.float64)
    cw_all = tr.cost_w.to_numpy(np.float64)
    cs_all = tr.cost_s.to_numpy(np.float64)
    eval_name = tr.eval_name.to_numpy()

    def X_real(idx):
        return emb_real[idx]

    Xs_syn = emb_syn
    ys_syn = syn.y_syn.to_numpy()
    label_syn = syn.label.to_numpy()

    # ---- shift diagnostics BEFORE fitting (PREREG 6) ----
    shift = compute_shift(syn, tr, emb_real, emb_syn, y_all)
    json.dump(shift, open(os.path.join(RESULTS, "shift_report.json"), "w"), indent=1)
    log("shift flags:", shift["flags_for_correction"])

    # ---- anchors ----
    we, st = wc_all[eval_untied], sc_all[eval_untied]
    cwe, cse = cw_all[eval_untied], cs_all[eval_untied]
    y1 = y_all[eval_untied]
    anchors = {
        "gamma": GAMMA, "n_eval": len(eval_untied),
        "eval_y1_rate": float(y1.mean()),
        "all_weak_U": float((we - GAMMA * cwe).mean()),
        "all_strong_U": float((st - GAMMA * cse).mean()),
        "oracle_U": float(np.where(y1 == 1, st - GAMMA * cse, we - GAMMA * cwe).mean()),
        "all_weak_quality": float(we.mean()),
        "all_strong_quality": float(st.mean()),
    }
    log("anchors:", json.dumps(anchors))

    # ---- T013 budget draws ----
    budget_rows = {}
    for b, lab in zip(BUDGETS, BUDGET_LABELS):
        k = int(round(b * len(tr)))
        idx = dev_untied[:k]
        n1 = int(y_all[idx].sum())
        n0 = len(idx) - n1
        budget_rows[lab] = {"budget_frac": b, "k": k, "idx": idx.tolist(),
                            "n_pos": n1, "n_neg": n0,
                            "valid": bool(n1 >= MIN_CLASS and n0 >= MIN_CLASS)}
        log(f"budget {lab}: k={k} pos={n1} neg={n0} valid={n1 >= MIN_CLASS and n0 >= MIN_CLASS}")
    # E5.4: if 0.5% invalid, 1% replaces it (all arms identically)
    if not budget_rows["0.5%"]["valid"] and budget_rows["1%"]["valid"]:
        budget_rows["0.5%"]["replaced_by"] = "1%"

    # ---- arm evaluation per budget ----
    rows = []
    syn_only_U = None
    for lab in BUDGET_LABELS:
        binfo = budget_rows[lab]
        if not binfo["valid"]:
            rows.append({"budget": lab, "valid": False,
                         "n_pos": binfo["n_pos"], "n_neg": binfo["n_neg"]})
            continue
        real_idx = np.array(binfo["idx"])
        Xr = X_real(real_idx)
        yr = y_all[real_idx]

        # arm 1: real-only
        clf_r = fit_logreg(Xr, yr)
        pr = predict_p(clf_r, X_real(eval_untied))
        U_r, q_r, c_r = policy_utility(pr, we, st, cwe, cse)

        # arm 2: synthetic-only NON-PROMOTABLE diagnostic
        clf_s = fit_logreg(Xs_syn, ys_syn)
        ps = predict_p(clf_s, X_real(eval_untied))
        U_s, _, _ = policy_utility(ps, we, st, cwe, cse)
        if syn_only_U is None:
            syn_only_U = U_s

        # arm 3: pretrain -> update
        warm = fit_logreg(Xs_syn, ys_syn)
        clf_p = fit_warm(Xr, yr, warm)
        pp = predict_p(clf_p, X_real(eval_untied))
        U_p, q_p, c_p = policy_utility(pp, we, st, cwe, cse)

        # arm 4: weighted joint (frozen CV)
        w_sel, m_sel, ll4 = cv_joint(Xr, yr, Xs_syn, ys_syn, label_syn)
        sw = joint_sample_weight(len(yr), len(ys_syn), w_sel, m_sel, label_syn)
        clf_j = fit_logreg(np.vstack([Xr, Xs_syn]),
                           np.concatenate([yr, ys_syn]), sample_weight=sw)
        pj = predict_p(clf_j, X_real(eval_untied))
        U_j, q_j, c_j = policy_utility(pj, we, st, cwe, cse)

        # E5.1: fusion for Gate 1 = argmin dev CV loss between arm 3 and arm 4
        ll3 = cv_loss_arm3(Xr, yr, Xs_syn, ys_syn)
        fusion_arm = "pretrain" if ll3 < ll4 - 1e-12 else "joint"
        U_f, q_f, c_f = (U_p, q_p, c_p) if fusion_arm == "pretrain" else (U_j, q_j, c_j)

        # arm 5: dr-direct shares the pooled direct model (E5.1); DR reported below
        rows.append({
            "budget": lab, "valid": True, "n_pos": binfo["n_pos"],
            "n_neg": binfo["n_neg"],
            "real_only_U": U_r, "pretrain_U": U_p, "joint_U": U_j,
            "fusion_arm": fusion_arm, "fusion_U": U_f,
            "dU_pretrain": U_p - U_r, "dU_joint": U_j - U_r, "dU_fusion": U_f - U_r,
            "syn_only_U_NONPROMOTABLE": U_s,
            "q_real": q_r, "q_pretrain": q_p, "q_joint": q_j, "q_fusion": q_f,
            "c_real": c_r, "c_pretrain": c_p, "c_joint": c_j, "c_fusion": c_f,
            "w_syn_sel": w_sel, "m_cls_sel": m_sel,
            "cv_ll_pretrain": ll3, "cv_ll_joint": ll4,
        })
        log(f"{lab}: U_r={U_r:.4f} U_p={U_p:.4f} U_j={U_j:.4f} fusion={fusion_arm} "
            f"U_f={U_f:.4f} U_s(NP)={U_s:.4f} w={w_sel} m={m_sel} ll3={ll3:.3f} ll4={ll4:.3f}")

    curve = pd.DataFrame(rows)
    curve.to_csv(os.path.join(RESULTS, "budget_curve.csv"), index=False)

    # ---- Gate 2 (B1/B2) with the smallest valid budget (E5.3) ----
    sims = build_simulators(dev_untied, eval_name, y_all, emb_real)
    sim_label = {"prop_sim": "need_strong", "flip_sim": "need_strong"}
    g2 = {}
    smallest_valid = next((lab for lab in BUDGET_LABELS if budget_rows[lab]["valid"]), None)
    for name, s in sims.items():
        if name not in ("prop_sim", "flip_sim"):
            continue
        Xs_sim = emb_real[s["rows"]]
        g2[name] = gate2_eval(s, X_real, Xs_sim, s["y"], sim_label[name],
                              eval_untied, y_all, wc_all, sc_all, cw_all, cs_all,
                              np.array(budget_rows[smallest_valid]["idx"]))
        g2[name]["sim_rows"] = len(s["rows"])
    # detector: |p_syn - p_real| larger for Flip-Sim than Prop-Sim
    p_real_dev = float(y_all[dev_untied].mean())
    p_prop = float(sims["prop_sim"]["y"].mean())
    p_flip = float(sims["flip_sim"]["y"].mean())
    detector = {
        "p_real_dev_y1": p_real_dev,
        "p_propsim_y1": p_prop, "p_flipsim_y1": p_flip,
        "divergence_prop": abs(p_prop - p_real_dev),
        "divergence_flip": abs(p_flip - p_real_dev),
        "flip_more_divergent": abs(p_flip - p_real_dev) > abs(p_prop - p_real_dev),
        "b2_fusion_not_beat_real": g2["flip_sim"]["dU"] <= 0,
        "b1_fusion_beats_real": g2["prop_sim"]["dU"] > 0,
        "w_syn_selected_propsim": g2["prop_sim"]["w_syn_sel"],
        "w_syn_selected_flipsim": g2["flip_sim"]["w_syn_sel"],
    }
    detector["gate2_pass"] = bool(detector["b1_fusion_beats_real"]
                                  and detector["b2_fusion_not_beat_real"]
                                  and detector["flip_more_divergent"])
    log("gate2:", json.dumps(detector, indent=1, default=str))

    # ---- DR feasibility report (non-gating; PREREG 13) ----
    dr_report = dr_feasibility(curve, budget_rows, X_real, Xs_syn, ys_syn, label_syn,
                               y_all, wc_all, sc_all, cw_all, cs_all, eval_untied)
    log("dr_report:", json.dumps(dr_report, indent=1, default=str))

    # ---- Gate 1 ----
    gate1 = gate1_eval(curve, budget_rows, X_real, Xs_syn, ys_syn, label_syn,
                       y_all, wc_all, sc_all, cw_all, cs_all, eval_untied, shift,
                       anchors)
    log("gate1:", json.dumps(gate1, indent=1, default=str))

    json.dump({"anchors": anchors, "budgets": {k: v for k, v in budget_rows.items()},
               "gate1": gate1, "gate2": detector, "dr_report": dr_report,
               "syn_only_U_NONPROMOTABLE": syn_only_U},
              open(os.path.join(RESULTS, "stage0_gate.json"), "w"),
              indent=1, default=str)
    log("stage0_gate.json written")


# ---------------------------------------------------------------- DR (PREREG 13)
def dr_feasibility(curve, budget_rows, X_real, Xs_syn, ys_syn, label_syn, y_all,
                   wc_all, sc_all, cw_all, cs_all, eval_untied):
    """Prop-Sim logging (Bernoulli 0.5, seed 108) on eval rows; DR value of each
    arm's policy with mu_hat from real-only vs syn-assisted nuisances; exact value
    from both potential outcomes. Feasibility report, NOT a gate."""
    rng = np.random.default_rng(SEED)
    n = len(eval_untied)
    a_log = (rng.random(n) < 0.5).astype(int)  # 1 = strong logged, 0 = weak
    e = 0.5
    out = {}
    r10 = curve[(curve.budget == "10%") & (curve.valid.astype(bool))]
    if not len(r10):
        return {"note": "10% budget invalid; DR feasibility skipped"}
    r10 = r10.iloc[0]
    real_idx = np.array(budget_rows["10%"]["idx"])
    Xr = X_real(real_idx)
    yr = y_all[real_idx]
    Xe = X_real(eval_untied)
    # mu_hat for weak/strong correctness: separate logistic nuisances
    def fit_mu(target_all, syn_rows=None, syn_target=None, syn_w=None):
        clf = fit_logreg(Xr, target_all[real_idx])
        if syn_rows is not None:
            X2 = np.vstack([Xr, syn_rows])
            y2 = np.concatenate([target_all[real_idx], syn_target])
            sw = np.concatenate([np.ones(len(real_idx)), syn_w])
            clf = fit_logreg(X2, y2, sample_weight=sw)
        return clf

    mu_w_real = fit_mu(wc_all)
    mu_s_real = fit_mu(sc_all)
    sw_syn_w = np.full(len(ys_syn), 1.0)  # weak_ok rows -> weak-correct target 1
    syn_w_target = (label_syn == "weak_ok").astype(float)
    mu_w_syn = fit_mu(wc_all, Xs_syn, syn_w_target, sw_syn_w)
    syn_s_target = (label_syn == "need_strong").astype(float)
    m_cls = 12.0
    sw_syn_s = np.where(label_syn == "need_strong", m_cls, 1.0)
    mu_s_syn = fit_mu(sc_all, Xs_syn, syn_s_target, sw_syn_s)

    for arm_name, p_vec in [("real_only", predict_p(fit_logreg(Xr, yr), Xe)),
                            ("fusion_joint", None)]:
        if p_vec is None:
            w_sel, m_sel, _ = cv_joint(Xr, yr, Xs_syn, ys_syn, label_syn)
            sw = joint_sample_weight(len(yr), len(ys_syn), w_sel, m_sel, label_syn)
            clf_j = fit_logreg(np.vstack([Xr, Xs_syn]),
                               np.concatenate([yr, ys_syn]), sample_weight=sw)
            p_vec = predict_p(clf_j, Xe)
        route_strong = (p_vec >= 0.5).astype(int)
        # mu_u(a,x) = mu_correct(a,x) - gamma*cost(a)
        mu_u0_r = predict_p(mu_w_real, Xe) - GAMMA * cw_all[eval_untied]
        mu_u1_r = predict_p(mu_s_real, Xe) - GAMMA * cs_all[eval_untied]
        mu_u0_s = predict_p(mu_w_syn, Xe) - GAMMA * cw_all[eval_untied]
        mu_u1_s = predict_p(mu_s_syn, Xe) - GAMMA * cs_all[eval_untied]
        r_obs = np.where(a_log == 1, sc_all[eval_untied] - GAMMA * cs_all[eval_untied],
                         wc_all[eval_untied] - GAMMA * cw_all[eval_untied])
        mu_obs_r = np.where(a_log == 1, mu_u1_r, mu_u0_r)
        mu_obs_s = np.where(a_log == 1, mu_u1_s, mu_u0_s)
        imp = route_strong == a_log
        vdr_r = float(np.mean(mu_u0_r * (1 - route_strong) + mu_u1_r * route_strong
                              + imp * (r_obs - mu_obs_r) / e))
        vdr_s = float(np.mean(mu_u0_s * (1 - route_strong) + mu_u1_s * route_strong
                              + imp * (r_obs - mu_obs_s) / e))
        v_true = float(np.mean(np.where(route_strong == 1,
                                        sc_all[eval_untied] - GAMMA * cs_all[eval_untied],
                                        wc_all[eval_untied] - GAMMA * cw_all[eval_untied])))
        out[arm_name] = {"V_DR_real_mu": vdr_r, "V_DR_syn_assisted_mu": vdr_s,
                         "V_true": v_true,
                         "abs_bias_real_mu": abs(vdr_r - v_true),
                         "abs_bias_syn_mu": abs(vdr_s - v_true)}
    return out


# ---------------------------------------------------------------- Gate 1
def gate1_eval(curve, budget_rows, X_real, Xs_syn, ys_syn, label_syn, y_all,
               wc_all, sc_all, cw_all, cs_all, eval_untied, shift, anchors):
    arms = ("pretrain", "joint")
    valid = curve[curve.valid.astype(bool)] if "valid" in curve.columns else curve
    valid = valid[valid.valid.astype(bool)] if "valid" in valid.columns else valid

    wins = {a: 0 for a in arms}
    wins_low = {a: 0 for a in arms}
    for _, r in valid.iterrows():
        for a in arms:
            du = r.get(f"dU_{a}")
            if du is not None and not pd.isna(du) and du > 0:
                wins[a] += 1
                if r["budget"] in LOW_BUDGETS:
                    wins_low[a] += 1

    # primary point: best dU among fusion arms at budgets <= 2%
    best = (-np.inf, None, None)
    for _, r in valid.iterrows():
        if r["budget"] not in LOW_BUDGETS:
            continue
        for a in arms:
            du = r.get(f"dU_{a}")
            if du is not None and not pd.isna(du) and du > best[0]:
                best = (du, a, r["budget"])
    primary = ({"budget": best[2], "arm": best[1], "dU": float(best[0])}
               if best[1] is not None else None)

    # (c) real-label saving at T = U(real-only@10%)
    target = None
    r10 = valid[valid.budget == "10%"]
    if len(r10):
        target = float(r10.real_only_U.iloc[0])
    saving = {"target_utility": target, "reached_at": None, "saving_frac": 0.0}
    if target is not None:
        for lab, frac in zip(BUDGET_LABELS, BUDGETS):
            row = valid[valid.budget == lab]
            if not len(row):
                continue
            fus = [row[f"{a}_U"].iloc[0] for a in ("pretrain", "joint")]
            fus = [u for u in fus if u is not None and not pd.isna(u)]
            if fus and max(fus) >= target and (1 - frac / 0.10) >= 0.25:
                saving = {"target_utility": target, "reached_at": lab,
                          "saving_frac": 1 - frac / 0.10}
                break

    matched = None
    if primary:
        r = valid[valid.budget == primary["budget"]].iloc[0]
        a = primary["arm"]
        matched = {
            "quality_gain_pp": 100.0 * (r[f"q_{a}"] - r["q_real"]),
            "cost_fusion": float(r[f"c_{a}"]), "cost_real": float(r["c_real"]),
            "crit_a_0.5pp_at_matched_cost": bool(
                (r[f"q_{a}"] - r["q_real"]) >= 0.005 and r[f"c_{a}"] <= r["c_real"]),
            "crit_b_3pct_cost_reduction_at_matched_quality": bool(
                r[f"c_{a}"] <= 0.97 * r["c_real"] and r[f"q_{a}"] >= r["q_real"]),
        }

    boot = None
    ci = None
    if primary:
        boot = bootstrap_and_ci(primary, curve, budget_rows, X_real, Xs_syn, ys_syn,
                                label_syn, y_all, wc_all, sc_all, cw_all, cs_all,
                                eval_untied)

    wins_best_arm = max(wins["pretrain"], wins["joint"])
    wins_low_best_arm = max(wins_low["pretrain"], wins_low["joint"])
    n_valid = len(valid)
    flags = shift["flags_for_correction"]
    return {
        "wins_per_arm": wins, "wins_low_per_arm": wins_low,
        "wins_best_arm": wins_best_arm, "wins_low_best_arm": wins_low_best_arm,
        "n_valid_budgets": int(n_valid),
        "primary_point": primary, "matched": matched,
        "saving": saving, "bootstrap": boot,
        "flags_for_correction": flags,
        "correction_applied": False,
    }


def bootstrap_and_ci(primary, curve, budget_rows, X_real, Xs_syn, ys_syn, label_syn,
                     y_all, wc_all, sc_all, cw_all, cs_all, eval_untied):
    """E5.6: models fit ONCE on the frozen real draw; eval rows resampled.
    10 seeds -> >=8/10 wins criterion; 2000 resamples seed 108 -> 95% percentile CI."""
    lab = primary["budget"]
    real_idx = np.array(budget_rows[lab]["idx"])
    Xr = X_real(real_idx)
    yr = y_all[real_idx]
    Xe = X_real(eval_untied)
    clf_r = fit_logreg(Xr, yr)
    pr = predict_p(clf_r, Xe)
    if primary["arm"] == "joint":
        w_sel, m_sel, _ = cv_joint(Xr, yr, Xs_syn, ys_syn, label_syn)
        sw = joint_sample_weight(len(yr), len(ys_syn), w_sel, m_sel, label_syn)
        clf_f = fit_logreg(np.vstack([Xr, Xs_syn]),
                           np.concatenate([yr, ys_syn]), sample_weight=sw)
    else:
        warm = fit_logreg(Xs_syn, ys_syn)
        clf_f = fit_warm(Xr, yr, warm)
    pf = predict_p(clf_f, Xe)
    we, st = wc_all[eval_untied], sc_all[eval_untied]
    cwe, cse = cw_all[eval_untied], cs_all[eval_untied]

    def du_on(pick):
        uf, _, _ = policy_utility(pf[pick], we[pick], st[pick], cwe[pick], cse[pick])
        ur, _, _ = policy_utility(pr[pick], we[pick], st[pick], cwe[pick], cse[pick])
        return uf - ur

    wins = 0
    for s in BOOT_SEEDS:
        rs = np.random.default_rng(s)
        pick = rs.integers(0, len(eval_untied), len(eval_untied))
        if du_on(pick) > 0:
            wins += 1
    rs = np.random.default_rng(SEED)
    n = len(eval_untied)
    dus = np.empty(CI_RESAMPLES)
    for i in range(CI_RESAMPLES):
        pick = rs.integers(0, n, n)
        dus[i] = du_on(pick)
    ci_low, ci_high = np.percentile(dus, [2.5, 97.5])
    return {"wins_of_10": wins, "ci95_low": float(ci_low),
            "ci95_high": float(ci_high),
            "dU_point": float(primary["dU"]),
            "seeds_ge_8": bool(wins >= 8),
            "ci_excludes_0": bool(ci_low > 0 or ci_high < 0)}


if __name__ == "__main__":
    main()
