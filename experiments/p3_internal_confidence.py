#!/usr/bin/env python3
"""Phase D — P3 answer-aware internal confidence ($0).

Preregistration: experiments/PREREG_P3.md (frozen, commit b10df12).
Protocol: experiments/PIVOT_PROTOCOL.md (train-only dev surface + deterministic
pivot holdout; validation reserved for finalists; test SEALED).

Signals (all runtime-visible at deployment, $0 from stored weak responses):
  R-shape  response length, ends-with-number, code fence, hedging, digit groups
  V-out    Phase C verifier outputs on the weak response (VF/VN/VM)
  P-conf   v1 cached P(strong) — baseline-only prompt-side signal
The true-internal family (logprobs/hidden states) is NOT feasible on this corpus
(prereg declares this); nothing here claims to test it.

Selection discipline: feature set AND C selected on dev-fit only (5-fold CV over
deterministic md5-bucket fold blocks, 3 salts); pivot holdout scored ONCE.
Run:
  python3 experiments/p3_internal_confidence.py > results/P3_raw.txt 2>&1
"""
import ast
import hashlib
import os
import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

WR = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")
PK = os.path.expanduser(
    "~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl")
PROBS = os.path.expanduser(
    "~/src/hermes-router-retraining-research/results/v1_train_probs.npy")
WEAK = "mistralai/mistral-7b-chat"
STRONG = "gpt-4-1106-preview"
BOOT_N, BOOT_SEED = 1000, 42
SALTS = (7, 13, 29)
C_GRID = (0.03, 0.3, 3.0)
SETS = ("R", "V", "R+V", "R+V+P")


# ---------------------------------------------------------------- data + seals
def md5_bucket(prompt, seed):
    h = hashlib.md5(f"{seed}:{prompt}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 10000


def load_train():
    wr = pd.read_parquet(WR)
    n_test = int((wr.split == "test").sum())
    assert n_test == 3678, f"sealed test membership changed: {n_test}"
    split_by_prompt = dict(zip(wr.prompt, wr.split))
    raw = pd.read_pickle(PK)
    raw["split"] = raw.prompt.map(split_by_prompt)
    tr = raw[raw.split == "train"].copy()   # test rows never carried forward
    assert len(tr) == 29193
    assert "test" not in set(tr["split"])
    return tr


def binarize(col):
    """Historical frozen convention: fillna(0).astype(int) truncation
    (partial-credit columns). np.nan_to_num equivalence is exact for this."""
    return np.nan_to_num(np.asarray(col, dtype=float), nan=0.0).astype(int)


def unwrap(txt):
    """Stored responses are python-repr list strings like \"['...']\"."""
    if not isinstance(txt, str):
        return None
    s = txt.strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            v = ast.literal_eval(s)
            if isinstance(v, list) and v and isinstance(v[0], str):
                return v[0]
        except (ValueError, SyntaxError):
            pass
    return s


# ------------------------------------------------------------------ extractors
CHOICE_PATTERNS = [
    re.compile(r"^\s*\(?([A-J])\)?\s*$"),
    re.compile(r"^([A-J])[\.\)\:]\b"),
    re.compile(r"answer\s+is[:\s]+\(?([A-J])\)?\b", re.I),
    re.compile(r"answer:\s*\(?([A-J])\)?\b", re.I),
    re.compile(r"^\(([A-J])\)\s*$", re.M),
    re.compile(r"\b([A-J])\s*is\s+the\s+answer", re.I),
]
GSM_PATTERNS = [
    re.compile(r"####\s*([-+]?[\d,]*\.?\d+)"),
    re.compile(r"answer\s+is[:\s]+\$?\s*([-+]?[\d,]*\.?\d+)", re.I),
    re.compile(r"(?:^|\n)[^\d\n]*\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*\.?\s*$"),
]
CODE_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.S)
HEDGE_RE = re.compile(r"sorry|cannot|unable|as an ai", re.I)


def family_of(eval_name):
    if eval_name.startswith("mmlu") or eval_name in ("arc-challenge",
                                                     "winogrande"):
        return "choice"
    if eval_name == "grade-school-math":
        return "gsm8k"
    if eval_name == "hellaswag":
        return "hellaswag"
    if eval_name == "mbpp":
        return "mbpp"
    return "open"


def extract_choice(txt):
    for pat in CHOICE_PATTERNS:
        m = pat.search(txt)
        if m:
            return m.group(1).upper()
    return None


def extract_gsm(txt):
    for pat in GSM_PATTERNS:
        m = pat.search(txt)
        if m:
            num = m.group(1).replace(",", "")
            try:
                return float(num)
            except ValueError:
                return None
    return None


def extract_answer(txt, fam):
    if fam == "choice":
        return extract_choice(txt)
    if fam == "gsm8k":
        return extract_gsm(txt)
    if fam == "mbpp":
        m = CODE_FENCE.search(txt)
        if m:
            return m.group(1)
        if re.search(r"^\s*def\s+\w+\s*\(", txt, re.M):
            return txt
        return None
    return txt.strip() if txt.strip() else None


# --------------------------------------------------------------- R-shape feats
def r_features(txt):
    t = unwrap(txt)
    if not isinstance(t, str) or not t.strip():
        return None
    low = t.lower()
    digs = re.findall(r"\d+", t)
    return np.array([
        np.log1p(len(t)),
        1.0 if re.search(r"\d\s*\.?\s*$", t.strip()) else 0.0,
        1.0 if "```" in t else 0.0,
        1.0 if HEDGE_RE.search(low) else 0.0,
        np.log1p(len(digs)),
        1.0 if len(t.strip()) <= 12 else 0.0,
    ], dtype=np.float64)


def build_features(tr):
    """LEAKAGE AUDIT (prereg): features use ONLY the weak model's stored
    response, eval_name-derived family, and v1 cached P(strong). Never
    correctness, never cost, never oracle routing, never other models."""
    resp = tr[f"{WEAK}|model_response"]
    fams = tr["eval_name"].map(family_of).to_numpy()
    rows = [r_features(t) for t in resp]
    ok_R = np.array([r is not None for r in rows], dtype=bool)
    miss = (~ok_R).astype(np.float64)
    R_def = np.zeros((len(rows), 6), dtype=np.float64)
    for i, r in enumerate(rows):
        if r is not None:
            R_def[i] = r

    ans = np.array([extract_answer(unwrap(t) or "", f) if isinstance(t, str)
                    else None for t, f in zip(resp, fams)], dtype=object)
    vf = np.array([a is not None for a in ans], dtype=np.float64)
    vn = np.array([float(isinstance(a, (int, float)) and np.isfinite(a)
                         and abs(a) < 1e12) if fam == "gsm8k" else 0.0
                   for a, fam in zip(ans, fams)], dtype=np.float64)
    vm = np.zeros(len(tr), dtype=np.float64)
    for i in np.where(fams == "mbpp")[0]:
        t = unwrap(resp.iloc[i]) or ""
        m = CODE_FENCE.search(t)
        code = m.group(1) if m else (t if re.search(r"^\s*def\s+\w+\s*\(",
                                                    t, re.M) else None)
        if code:
            try:
                compile(code, "<resp>", "exec")
                vm[i] = 1.0
            except SyntaxError:
                pass

    probs = np.load(PROBS)
    assert len(probs) == len(tr)
    P = probs.astype(np.float64)

    mats = {
        "R": np.column_stack([R_def, miss]),
        "V": np.column_stack([vf, vn, vm]),
        "R+V": np.column_stack([R_def, miss, vf, vn, vm]),
        "R+V+P": np.column_stack([R_def, miss, vf, vn, vm, P]),
    }
    return mats, fams, P


# ------------------------------------------------------------------ CV helpers
def fit_oof(X, risk, trn, tst, c_reg):
    pipe = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, C=c_reg, class_weight="balanced",
                           solver="lbfgs"))
    pipe.fit(X[trn], risk[trn])
    return pipe.predict_proba(X[tst])[:, 1]


def main():
    tr = load_train()
    n = len(tr)
    bucket = tr["prompt"].map(lambda p: md5_bucket(p, 42)).to_numpy()
    holdout = bucket < 1500
    dev = ~holdout
    print(f"SECTION 0: train {n} | dev-fit {int(dev.sum())} | "
          f"pivot-holdout {int(holdout.sum())} ({holdout.mean():.4f}) | "
          f"test rows loaded: 0 (sealed)")

    y_weak = binarize(tr[WEAK])
    y_strong = binarize(tr[STRONG])
    c_w = float(tr[f"{WEAK}|total_cost"].mean())
    c_s = float(tr[f"{STRONG}|total_cost"].mean())
    print(f"stored cost/call: weak ${c_w:.7f} strong ${c_s:.7f}")

    mats, fams, P = build_features(tr)
    risk = (1 - y_weak).astype(float)
    v1m = P >= 0.30
    v1_routed = np.where(v1m, y_strong, y_weak)
    v1_cost_row = c_w + v1m.astype(float) * c_s
    print("LEAKAGE AUDIT: features = [weak response text -> R-shape+V-out; "
          "v1 cached P(strong)]; correctness/cost/oracle/other-models never "
          "enter feature matrices (see build_features)")

    # ---------------- SECTION 1: dev-fit CV (feature set x C selection)
    print("\nSECTION 1: dev-fit 5-fold OOF (md5 fold blocks; 3 salts averaged)")
    cv = {}
    for set_name in SETS:
        X = mats[set_name]
        for c_reg in C_GRID:
            aucs, qa, qc, ca, cc = [], [], [], [], []
            for salt in SALTS:
                folds = tr["prompt"].map(
                    lambda p, s=salt: md5_bucket(p, s) % 5).to_numpy()
                oof = np.full(n, np.nan)
                for k in range(5):
                    trn, tst = dev & (folds != k), dev & (folds == k)
                    if trn.sum() < 100 or tst.sum() < 100:
                        continue
                    oof[tst] = fit_oof(X, risk, trn, tst, c_reg)
                m = dev & ~np.isnan(oof)
                aucs.append(roc_auc_score(risk[m], oof[m]))
                v1a = float(v1_routed[m].mean())
                v1c = float(v1_cost_row[m].mean())
                # q-arm diagnostic: fixed escalation share 0.25
                thr = np.quantile(oof[m], 0.75)
                esc = m & (oof >= thr)
                acc = ((y_weak[m & ~esc].sum() + y_strong[esc].sum())
                       / m.sum())
                qa.append(acc - v1a)
                qc.append((c_w + c_s * float(esc[m].mean())) - v1c)
                # c-arm: min cost s.t. acc >= v1
                best = None
                for q in np.linspace(0.0, 0.95, 40):
                    thr = np.quantile(oof[m], q)
                    esc = m & (oof >= thr)
                    a2 = ((y_weak[m & ~esc].sum() + y_strong[esc].sum())
                          / m.sum())
                    c2 = c_w + c_s * float(esc[m].mean())
                    if a2 >= v1a and (best is None or c2 < best):
                        best = c2
                if best is not None:
                    ca.append(best - v1c)
            cv[(set_name, c_reg)] = (
                float(np.mean(aucs)), float(np.mean(qa)), float(np.mean(qc)),
                float(np.mean(ca)) if ca else float("nan"))
            r = cv[(set_name, c_reg)]
            print(f"  {set_name:6s} C={c_reg:<5} AUROC {r[0]:.4f} | "
                  f"q-arm d_acc {r[1]:+.4f} d_cost {r[2]:+.7f} | "
                  f"c-arm d_cost {r[3]:+.7f}")

    def qkey(key):
        d_acc, d_cost = cv[key][1], cv[key][2]
        return (d_acc if d_cost <= 0 else -1.0, cv[key][0])

    best_set, best_C = max(cv, key=qkey)
    print(f"  SELECTED (dev-fit): set={best_set} C={best_C}")

    # ---------------- SECTION 2: frozen operating points (dev-fit OOF)
    print("\nSECTION 2: frozen operating points (dev-fit OOF, pooled salts)")
    parts = []
    for salt in SALTS:
        folds = tr["prompt"].map(
            lambda p, s=salt: md5_bucket(p, s) % 5).to_numpy()
        o = np.full(n, np.nan)
        for k in range(5):
            trn, tst = dev & (folds != k), dev & (folds == k)
            o[tst] = fit_oof(mats[best_set], risk, trn, tst, best_C)
        parts.append(o)
    oof = np.nanmean(np.vstack(parts), axis=0)
    m = dev & ~np.isnan(oof)
    v1_acc_d = float(v1_routed[dev].mean())
    fs_d = float(v1m[dev].mean())
    v1_cost_d = float(v1_cost_row[dev].mean())
    print(f"  v1 dev: acc {v1_acc_d:.4f} cost {v1_cost_d:.7f} fs {fs_d:.4f}")

    fix_dev = dev & ~v1m & (y_weak == 0) & (y_strong == 1)
    ceil_acc_d = float(np.where(fix_dev, 1.0, v1_routed)[dev].mean())
    fix_share_d = float(fix_dev[dev].mean())
    ceil_cost_d = v1_cost_d + c_s * fix_share_d
    print(f"  realizable oracle ceiling (dev): acc {ceil_acc_d:.4f} "
          f"({ceil_acc_d - v1_acc_d:+.4f} vs v1) cost {ceil_cost_d:.7f} "
          f"escalated_share {fix_share_d:.4f}")

    def arm_stats(esc_mask):
        acc = ((y_weak[m & ~esc_mask].sum() + y_strong[esc_mask].sum())
               / m.sum())
        cost = c_w + c_s * float(esc_mask[m].mean())
        return float(acc), float(cost), float(esc_mask[m].mean())

    o1_best_acc, o1_pack = -1.0, None
    o2_best_cost, o2_pack = np.inf, None
    for q in np.linspace(0.0, 0.99, 200):
        thr = np.quantile(oof[m], q)
        a2, c2, s2 = arm_stats(m & (oof >= thr))
        if c2 <= v1_cost_d and a2 > o1_best_acc:
            o1_best_acc, o1_pack = a2, (thr, a2, c2, s2)
        if a2 >= v1_acc_d and c2 < o2_best_cost:
            o2_best_cost, o2_pack = c2, (thr, a2, c2, s2)
    assert o1_pack is not None, "O1 infeasible: no tau meets cost<=v1"
    assert o2_pack is not None, "O2 infeasible: no tau meets acc>=v1"
    o1, o2 = o1_pack, o2_pack
    o3_thr = np.quantile(oof[m], 1 - fs_d)
    o3 = (o3_thr, *arm_stats(m & (oof >= o3_thr)))
    ctl = (None, *arm_stats(m & v1m))
    for nm, pt in (("O1_quality", o1), ("O2_cost", o2),
                   ("O3_cov_matched", o3), ("control_wf_v1", ctl)):
        print(f"  {nm:16s} thr={pt[0] if pt[0] is not None else 'v1@0.30':>9} "
              f"acc {pt[1]:.4f} cost {pt[2]:.7f} esc_share {pt[3]:.4f}")
    print(f"FROZEN: set={best_set} C={best_C} tau_q={o1[0]:.6f} "
          f"tau_c={o2[0]:.6f} tau_cov={o3[0]:.6f} "
          f"v1_acc_d={v1_acc_d:.6f} v1_cost_d={v1_cost_d:.7f}")

    # ---------------- SECTION 3: single holdout pass
    print("\nSECTION 3: PIVOT-HOLDOUT single-pass results")
    pipe = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, C=best_C, class_weight="balanced",
                           solver="lbfgs"))
    pipe.fit(mats[best_set][dev], risk[dev])
    ph = pipe.predict_proba(mats[best_set][holdout])[:, 1]

    acc_v1_h = float(v1_routed[holdout].mean())
    cost_v1_h = float(v1_cost_row[holdout].mean())
    fs_h = float(v1m[holdout].mean())
    fix_h = holdout & ~v1m & (y_weak == 0) & (y_strong == 1)
    ceil_acc_h = float(np.where(fix_h, 1.0, v1_routed)[holdout].mean())
    fix_share_h = float(fix_h[holdout].mean())
    ceil_cost_h = cost_v1_h + c_s * fix_share_h
    print(f"  v1 holdout: acc {acc_v1_h:.4f} cost {cost_v1_h:.7f} fs {fs_h:.4f}")
    print(f"  realizable ceiling (holdout): acc {ceil_acc_h:.4f} "
          f"({ceil_acc_h - acc_v1_h:+.4f}) cost {ceil_cost_h:.7f} "
          f"escalated_share {fix_share_h:.4f}")

    base_q = v1_routed[holdout].astype(float)
    base_c = v1_cost_row[holdout]

    def boot_ci(pol, base):
        rng = np.random.default_rng(BOOT_SEED)
        nh = int(holdout.sum())
        idx = rng.integers(0, nh, size=(BOOT_N, nh))
        d = pol[idx].mean(axis=1) - base[idx].mean(axis=1)
        return (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)))

    print(f"  {'arm':16s} {'acc':>7s} {'cost/row':>10s} {'esc_share':>9s} "
          f"{'d_acc [95%]':>22s} {'d_cost [95%]':>22s}")
    verdicts = {}
    for name, thr in (("O1_quality", o1[0]), ("O2_cost", o2[0]),
                      ("O3_cov_matched", o3[0])):
        esc_h = ph >= thr                      # holdout-length vector
        pr = np.where(esc_h, y_strong[holdout],
                      y_weak[holdout]).astype(float)
        pc = c_w + esc_h.astype(float) * c_s
        acc, cost = float(pr.mean()), float(pc.mean())
        lo, hi = boot_ci(pr, base_q)
        lo2, hi2 = boot_ci(pc, base_c)
        print(f"  {name:16s} {acc:7.4f} {cost:10.7f} "
              f"{float(esc_h.mean()):9.4f} {acc - acc_v1_h:+.4f} "
              f"[{lo:+.4f},{hi:+.4f}] {cost - cost_v1_h:+.7f} "
              f"[{lo2:+.7f},{hi2:+.7f}]")
        verdicts[name] = (acc, cost)
    esc_ctl = v1m[holdout]
    pr = np.where(esc_ctl, y_strong[holdout], y_weak[holdout]).astype(float)
    pc = c_w + esc_ctl.astype(float) * c_s
    acc_ctl_h, cost_ctl_h = float(pr.mean()), float(pc.mean())
    lo, hi = boot_ci(pr, base_q)
    lo2, hi2 = boot_ci(pc, base_c)
    print(f"  {'control_wf_v1':16s} {acc_ctl_h:7.4f} {cost_ctl_h:10.7f} "
          f"{float(esc_ctl.mean()):9.4f} {acc_ctl_h - acc_v1_h:+.4f} "
          f"[{lo:+.4f},{hi:+.4f}] {cost_ctl_h - cost_v1_h:+.7f} "
          f"[{lo2:+.7f},{hi2:+.7f}]")
    pr = np.where(fix_h, 1.0, v1_routed).astype(float)[holdout]
    pc = (v1_cost_row + fix_h.astype(float) * c_s)[holdout]
    lo, hi = boot_ci(pr, base_q)
    lo2, hi2 = boot_ci(pc, base_c)
    print(f"  {'REALIZ_CEIL':16s} {ceil_acc_h:7.4f} {ceil_cost_h:10.7f} "
          f"{float(fix_h.mean()):9.4f} {ceil_acc_h - acc_v1_h:+.4f} "
          f"[{lo:+.4f},{hi:+.4f}] {ceil_cost_h - cost_v1_h:+.7f} "
          f"[{lo2:+.7f},{hi2:+.7f}]")

    # ---------------- SECTION 4: frozen-gate verdicts
    print("\nSECTION 4: frozen-gate verdicts (holdout)")
    lift = ceil_acc_h - acc_v1_h
    for name, (acc, cost) in verdicts.items():
        d_acc, d_cost = acc - acc_v1_h, cost - cost_v1_h
        cap = d_acc / lift if lift > 0 else 0.0
        q_arm = cap >= 0.5 and d_cost <= 0
        c_arm = d_cost <= -0.05 * cost_v1_h and acc >= acc_v1_h
        beats_ctl = (acc > acc_ctl_h and cost <= cost_ctl_h) or \
                    (cost < cost_ctl_h and acc >= acc_ctl_h)
        print(f"  {name:16s} gate={'PASS' if (q_arm or c_arm) else 'FAIL'} "
              f"(capture {cap * 100:.1f}% of realizable lift; "
              f"beats_control={'YES' if beats_ctl else 'NO'})")

    # ---------------- SECTION 5: per-family OOF AUROC (adversarial rule)
    print("\nSECTION 5: per-family OOF AUROC (dev, selected set, pooled salts)")
    for gname in ("choice", "gsm8k", "hellaswag", "mbpp", "open"):
        sel = dev & (fams == gname) & ~np.isnan(oof)
        if sel.sum() < 200 or len(set(risk[sel])) < 2:
            print(f"  {gname:10s} n={int(sel.sum()):6d} AUROC n/a")
            continue
        print(f"  {gname:10s} n={int(sel.sum()):6d} "
              f"AUROC {roc_auc_score(risk[sel], oof[sel]):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
