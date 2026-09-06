#!/usr/bin/env python3
"""Phase C — P1 adaptive cheap sampling + P2 deterministic verifiers ($0).

Preregistration: experiments/PREREG_P1_P2.md (frozen, commit d8af031).
Protocol: experiments/PIVOT_PROTOCOL.md (train-only dev surface + deterministic
pivot holdout; validation reserved for finalists; test SEALED).

Policies (all on stored 0-shot labels; one response per model per row):
  P1-a oracle heterogeneous pair (weak->Yi->strong; ceiling diagnostic only)
  P1-b disagreement-triggered escalation (weak+Yi, runtime-visible)
  P1-c verifier-gated pair (weak; Yi if weak fails VF; else strong)
Verifiers (near-free, family-aware):
  VF  answer-format/extraction check (per canonical family pattern)
  VN  numeric sanity on the extracted GSM8K number
  VJ  fenced-JSON validity (coverage probe)
  VM  mbpp structural compile (+ exec-against-prompt-asserts in a subprocess
      when the prompt carries asserts)

Selection discipline: every rule/threshold below is fixed by the prereg or
selected on DEV-FIT only; the pivot holdout is scored exactly once per policy
at the end (SECTION 5). Run:
  python3 experiments/p1_p2_sampling_verifiers.py > results/P1_P2_raw.txt
"""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

WR = os.path.expanduser("~/transfer-bundle/analysis/winrate_table.parquet")
PK = os.path.expanduser(
    "~/transfer-bundle/datasets/routerbench/routerbench_0shot.pkl")
WEAK = "mistralai/mistral-7b-chat"
STRONG = "gpt-4-1106-preview"
MID = "zero-one-ai/Yi-34B-Chat"
NON = {"sample_id", "prompt", "eval_name", "oracle_model_to_route_to", "split"}
BOOT_N = 1000
BOOT_SEED = 42


# ---------------------------------------------------------------- data + seals
def md5_bucket(prompt, seed=42):
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


def unwrap(txt):
    """Stored responses are python-repr list strings like "['...']"."""
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
    re.compile(r"^\s*\(?([A-J])\)?\s*$"),            # bare "A" / "A)" / "(A)"
    re.compile(r"^([A-J])[\.\)\:]\b"),               # leading "A." / "A)"
    re.compile(r"answer\s+is[:\s]+\(?([A-J])\)?\b", re.I),
    re.compile(r"answer:\s*\(?([A-J])\)?\b", re.I),
    re.compile(r"^\(([A-J])\)\s*$", re.M),
    re.compile(r"\b([A-J])\s*is\s+the\s+answer", re.I),
]
GSM_PATTERNS = [
    re.compile(r"####\s*([-+]?[\d,]*\.?\d+)"),
    re.compile(r"answer\s+is[:\s]+\$?\s*([-+]?[\d,]*\.?\d+)", re.I),
    re.compile(r"(?:^|\n)[^\d\n]*\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*\.?\s*$"),  # trailing number
]
CODE_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.S)
FENCE_JSON = re.compile(r"```json\s*(.*?)```", re.S)


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
    """Returns extracted answer or None (None => VF fails)."""
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
    return txt.strip() if txt.strip() else None   # hellaswag/open: non-empty


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def agree_rule(ans_weak, ans_yi, full_weak, full_yi):
    """Frozen canonical rule: answer-string equality when both extract,
    else normalized full-text equality."""
    if ans_weak is not None and ans_yi is not None:
        return norm(str(ans_weak)) == norm(str(ans_yi))
    return norm(full_weak) == norm(full_yi)


# ------------------------------------------------------------------- verifiers
def vf(resp, fam):
    """VF: family-aware answer-format/extraction check. True=accept.
    Accepts a scalar response string or a Series (vectorized)."""
    if hasattr(resp, "map"):
        return np.array([vf(t, f) for t, f in zip(resp, np.full(len(resp), fam))],
                        dtype=bool)
    t = unwrap(resp)
    if not t:
        return False
    return extract_answer(t, fam) is not None


def vn(ans_gsm):
    """VN: numeric sanity on an extracted GSM8K number."""
    if ans_gsm is None:
        return False
    try:
        x = float(ans_gsm)
        return np.isfinite(x) and abs(x) < 1e12
    except (TypeError, ValueError):
        return False


def vj(resp):
    t = unwrap(resp) or ""
    m = FENCE_JSON.search(t)
    if not m:
        return None   # abstain: no json block at all (coverage measured)
    try:
        json.loads(m.group(1))
        return True
    except json.JSONDecodeError:
        return False


def vm_structural(resp):
    t = unwrap(resp) or ""
    m = CODE_FENCE.search(t)
    code = m.group(1) if m else (t if re.search(r"^\s*def\s+\w+\s*\(", t, re.M)
                                 else None)
    if not code:
        return None
    try:
        compile(code, "<resp>", "exec")
        return True
    except SyntaxError:
        return False


def vm_exec(resp, prompt):
    """Run the response code against the prompt's own asserts in a subprocess.
    None => cannot judge (no asserts / no code)."""
    t = unwrap(resp) or ""
    m = CODE_FENCE.search(t)
    code = m.group(1) if m else (t if re.search(r"^\s*def\s+\w+\s*\(", t, re.M)
                                 else None)
    if not code:
        return None
    asserts = "\n".join(l for l in prompt.splitlines()
                        if l.strip().startswith("assert "))
    if not asserts:
        return None
    payload = code + "\n\n" + asserts + "\nprint('VM_EXEC_OK')\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(payload)
        path = f.name
    try:
        r = subprocess.run([sys.executable, "-I", "-S", path],
                           capture_output=True, text=True, timeout=5)
        return r.returncode == 0 and "VM_EXEC_OK" in r.stdout
    except subprocess.TimeoutExpired:
        return False
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------- metrics
def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - hw, c + hw)


def op_point(mask_strong, weak, mid, strong, c_weak, c_mid, c_strong):
    """mask_strong: rows routed to strong. Pair policies: rows not strong get
    the pair's sequential service (weak always; mid only if weak failed)."""
    routed = np.where(mask_strong, strong,
                      np.where(weak == 1, weak, np.where(mid == 1, mid, 0)))
    acc = float(routed.mean())
    cost = (float(mask_strong.mean()) * c_strong
            + float((~mask_strong).mean()) * (c_weak + c_mid))
    return acc, cost


def bootstrap_pair(policy_vals, v1_vals, seed=BOOT_SEED, n=BOOT_N):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(policy_vals), size=(n, len(policy_vals)))
    diffs = policy_vals[idx].mean(axis=1) - v1_vals[idx].mean(axis=1)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main():
    tr = load_train()
    fam = tr["eval_name"].map(family_of)
    bucket = tr.prompt.map(md5_bucket)
    holdout = (bucket < 1500).to_numpy()
    dev = ~holdout
    print(f"SECTION 0: train {len(tr)} | dev-fit {int(dev.sum())} | "
          f"pivot-holdout {int(holdout.sum())} ({holdout.mean():.4f}) | "
          f"test rows loaded: 0 (sealed)")

    B = {m: tr[m].fillna(0).astype(int).to_numpy() for m in
         (WEAK, STRONG, MID)}
    weak, mid, strong = B[WEAK], B[MID], B[STRONG]
    costs = {m: float(tr[f"{m}|total_cost"].mean())
             for m in (WEAK, STRONG, MID)}
    c_w, c_s, c_m = costs[WEAK], costs[STRONG], costs[MID]
    print(f"stored cost/call: weak ${c_w:.7f} mid(Yi) ${c_m:.7f} "
          f"strong ${c_s:.7f}")

    # ---------------- SECTION 1: verifier table (per family, weak + mid)
    print("\nSECTION 1: verifier diagnostics by family (rows: dev-fit only)")
    resp_w = tr[f"{WEAK}|model_response"]
    resp_m = tr[f"{MID}|model_response"]
    fams = fam.to_numpy()
    for label, model, resp in (("weak", weak, resp_w), ("mid", mid, resp_m)):
        for vfam in sorted(set(fams)):
            sel = dev & (fams == vfam)
            n = int(sel.sum())
            if n < 50:
                continue
            acc = np.asarray(vf(resp[sel], vfam))
            ok = np.asarray(model[sel] == 1)
            cov = float(np.mean(acc))
            prec = float(ok[acc].mean()) if acc.any() else float("nan")
            fr = float(ok[~acc].mean()) if (~acc).any() else float("nan")
            print(f"  VF {label:4s} {vfam:10s} n={n:6d} coverage={cov:.4f} "
                  f"accept_precision={prec:.4f} false_reject={fr:.4f}")

    # VN/VJ/VM on dev-fit (weak model)
    g = dev & (fams == "gsm8k")
    gsm_ext = np.array([extract_gsm(unwrap(t) or "") if isinstance(t, str)
                        else None for t in resp_w[g]], dtype=object)
    vn_acc = np.array([vn(a) for a in gsm_ext])
    print(f"  VN weak gsm8k n={int(g.sum())} coverage={vn_acc.mean():.4f} "
          f"precision={np.mean(weak[g][vn_acc]):.4f} "
          f"(VF-only precision={np.mean(weak[g][np.array([a is not None for a in gsm_ext])]):.4f})")
    vj_out = np.array([vj(t) for t in resp_w[dev]], dtype=object)
    vj_cov = float(np.mean([v is not None for v in vj_out]))
    print(f"  VJ weak all-dev: json-block coverage={vj_cov:.4f} "
          f"(expected <2%; abstain={np.mean([v is None for v in vj_out]):.4f})")
    mbp = dev & (fams == "mbpp")
    n_mbp = int(mbp.sum())
    n_assert = int(sum(1 for p in tr["prompt"][mbp]
                       if any(l.strip().startswith("assert ")
                              for l in p.splitlines())))
    print(f"  VM weak mbpp n={n_mbp} prompts-with-asserts={n_assert} "
          f"structural_compile_pass={np.mean([vm_structural(t) for t in resp_w[mbp]]):.4f}")
    vm_exec_acc, vm_exec_rows = [], 0
    for t, p, ok in zip(resp_w[mbp], tr["prompt"][mbp], weak[mbp]):
        r = vm_exec(t, p)
        if r is not None:
            vm_exec_rows += 1
            vm_exec_acc.append((r, ok))
    if vm_exec_rows:
        ea = np.array(vm_exec_acc)
        print(f"  VM-exec weak mbpp judged={vm_exec_rows} "
              f"coverage={vm_exec_rows / n_mbp:.4f} "
              f"precision={ea[:, 0].astype(float).mean():.4f} "
              f"pass->correct={ea[ea[:, 0]][:, 1].mean() if ea[:, 0].any() else float('nan'):.4f}")

    # ---------------- SECTION 2: P1 measures (dev-fit)
    print("\nSECTION 2: P1 pair measures (dev-fit)")
    ans_w = np.array([extract_answer(unwrap(t) or "", f) if isinstance(t, str)
                      else None for t, f in zip(resp_w, fams)], dtype=object)
    ans_m = np.array([extract_answer(unwrap(t) or "", f) if isinstance(t, str)
                      else None for t, f in zip(resp_m, fams)], dtype=object)
    full_w = np.array([unwrap(t) or "" for t in resp_w], dtype=object)
    full_m = np.array([unwrap(t) or "" for t in resp_m], dtype=object)
    ag = np.array([agree_rule(a, b, x, y) for a, b, x, y in
                   zip(ans_w, ans_m, full_w, full_m)])
    wfail = weak == 0
    d = dev
    p_rep = float(mid[d & wfail].mean())
    p_cofail_agree = float((wfail & ag)[d].mean())
    ag_n = int(ag[d].sum())
    p_ok_agree = float(weak[d & ag].mean())
    lo, hi = wilson(p_ok_agree, ag_n)
    print(f"  P(mid repairs | weak fails) = {p_rep:.4f}")
    print(f"  P(co-failure AND agreement) = {p_cofail_agree:.4f}")
    print(f"  agreement->correctness calibration: P(weak ok | agree) = "
          f"{p_ok_agree:.4f}  Wilson95 [{lo:.4f},{hi:.4f}]  n_agree={ag_n}")
    print(f"  disagreement rate (dev) = {1 - ag[d].mean():.4f}")

    # ---------------- SECTION 3: dev-fit operating points
    print("\nSECTION 3: dev-fit operating points (selection surface)")

    def run_surface(mask):
        rows = []
        w_acc, s_acc = float(weak[mask].mean()), float(strong[mask].mean())
        gap = s_acc - w_acc
        rows.append(("always_weak", w_acc, c_w, 0.0))
        rows.append(("always_strong", s_acc, c_s, 1.0))
        rows.append(("v1@0.30", None, None, None))   # placeholder, filled later
        # P1-a oracle pair (ceiling): weak first; mid iff weak failed; strong iff both failed
        acc_a = float(np.where(weak[mask] == 1, weak[mask],
                       np.where(mid[mask] == 1, mid[mask], strong[mask])).mean())
        strong_share_a = float((~((weak[mask] == 1) | ((weak[mask] == 0) & (mid[mask] == 1)))).mean())
        # exact sequential cost: E[cost] = c_w + c_m*P(weak fail) + c_s*P(both fail)
        p_wf = float(wfail[mask].mean())
        p_bf = float((wfail & (mid == 0))[mask].mean())
        cost_a = c_w + c_m * p_wf + c_s * p_bf
        rows.append(("P1a_oracle_pair(ceiling)", acc_a, cost_a, strong_share_a))
        # P1-b disagreement escalation
        m_b = (~ag) & mask
        acc_b = float(np.where(m_b, strong, weak)[mask].mean())
        # cost: weak+mid always; strong iff disagree
        cost_b = c_w + c_m + c_s * float(((~ag) & mask).sum() / mask.sum())
        rows.append(("P1b_disagree_escalate", acc_b, cost_b, float(m_b.mean())))
        # P1-c verifier-gated pair (runtime rule, frozen in prereg):
        # call weak -> if VF passes, SHIP weak's answer -> else call mid ->
        # if VF passes, ship mid -> else escalate strong.
        vf_w = np.array([vf(t, f) for t, f in zip(resp_w, fams)])
        vf_m = np.array([vf(t, f) for t, f in zip(resp_m, fams)])
        ship_weak = vf_w & mask
        call_mid = (~vf_w) & mask
        ship_mid = call_mid & vf_m
        call_strong = call_mid & (~vf_m)
        # quality: ship_weak rows get weak's stored outcome; ship_mid get mid's;
        # strong get strong's
        acc_c = float((weak[ship_weak].sum() + mid[ship_mid].sum()
                       + strong[call_strong].sum()) / mask.sum())
        cost_c = (c_w * float(mask.mean()) + c_m * float(call_mid.mean())
                  + c_s * float(call_strong.mean()))
        rows.append(("P1c_verifier_gated_pair", acc_c, cost_c,
                     float(call_strong.mean())))
        return rows, gap, w_acc, s_acc

    # v1 train-side probs (cached across runs; computed from frozen artifacts)
    cache = os.path.expanduser(
        "~/src/hermes-router-retraining-research/results/v1_train_probs.npy")
    if os.path.exists(cache):
        probs = np.load(cache)
        assert len(probs) == len(tr)
    else:
        sys.path.insert(0, os.path.expanduser(
            "~/src/hermes-router-retraining-research/router_v1"))
        import route as v1route
        import torch
        enc, head = v1route._load()
        bs = 512
        ps = []
        for i in range(0, len(tr), bs):
            emb = enc.encode(list(tr["prompt"].iloc[i:i + bs]),
                             normalize_embeddings=True).astype(np.float32)
            x = torch.from_numpy(emb)
            with torch.no_grad():
                s1 = head.score(x, torch.ones(len(x), dtype=torch.long))
                s0 = head.score(x, torch.zeros(len(x), dtype=torch.long))
            ps.append(torch.sigmoid(s1 - s0).numpy())
        probs = np.concatenate(ps)
        np.save(cache, probs)
    v1_mask = probs >= 0.30

    # dev-fit table first (selection surface); holdout printed only in SECTION 5
    rows_d, gap_d, w_d, s_d = run_surface(dev)
    v1_routed = np.where(v1_mask, strong, weak)
    acc_v1_d = float(v1_routed[dev].mean())
    fs_d = float(v1_mask[dev].mean())
    cost_v1_d = c_s * fs_d + c_w * (1 - fs_d)
    fs_v1_d = fs_d
    print(f"  {'policy':28s} {'acc':>7s} {'cost/row':>10s} {'frac_strong':>11s} "
          f"{'PGR':>7s}")
    for name, acc, cost, fs in rows_d:
        if name == "v1@0.30":
            acc, cost, fs = acc_v1_d, cost_v1_d, fs_v1_d
        pgr = (acc - w_d) / gap_d
        print(f"  {name:28s} {acc:7.4f} {cost:10.7f} {fs:11.4f} {pgr:7.4f}")
    dev_points = {name: (acc, cost, fs) for name, acc, cost, fs in rows_d
                  if name != "v1@0.30"}
    dev_points["v1@0.30"] = (acc_v1_d, cost_v1_d, fs_v1_d)

    # ---------------- SECTION 4: frozen operating points for holdout scoring
    print("\nSECTION 4: FROZEN for single holdout scoring (per prereg):")
    print("  policies: always_weak, always_strong, v1@0.30, P1a(ceiling), "
          "P1b, P1c; gates: P1 keep = quality up at <=matched cost OR cost "
          "-5% at >=matched quality vs v1 (holdout); P2 keep = dev accept-"
          "precision >=0.90 AND coverage >=5%, and P1c must beat P1b.")

    # ---------------- SECTION 5: single holdout pass
    print("\nSECTION 5: PIVOT-HOLDOUT single-pass results")
    rows_h, gap_h, w_h, s_h = run_surface(holdout)
    acc_v1_h = float(v1_routed[holdout].mean())
    fs_h = float(v1_mask[holdout].mean())
    cost_v1_h = c_s * fs_h + c_w * (1 - fs_h)
    fs_v1_h = fs_h
    print(f"  {'policy':28s} {'acc':>7s} {'cost/row':>10s} {'frac_strong':>11s} "
          f"{'PGR':>7s}  {'d_acc_vs_v1 [95%]':>24s}")
    results = {}
    per_row_acc = {
        "always_weak": weak, "always_strong": strong,
        "v1@0.30": v1_routed,
        "P1a_oracle_pair(ceiling)": np.where(
            weak == 1, weak, np.where(mid == 1, mid, strong)),
        "P1b_disagree_escalate": np.where(~ag, strong, weak),
    }
    vf_w_all = np.array([vf(t, f) for t, f in zip(resp_w, fams)])
    vf_m_all = np.array([vf(t, f) for t, f in zip(resp_m, fams)])
    ship_weak = vf_w_all & holdout
    call_mid = (~vf_w_all) & holdout
    ship_mid = call_mid & vf_m_all
    call_strong = call_mid & (~vf_m_all)
    routed_c = np.zeros(len(tr), dtype=int)
    routed_c[ship_weak] = weak[ship_weak]
    routed_c[ship_mid] = mid[ship_mid]
    routed_c[call_strong] = strong[call_strong]
    per_row_acc["P1c_verifier_gated_pair"] = routed_c

    for name, acc, cost, fs in rows_h:
        if name == "v1@0.30":
            acc, cost, fs = acc_v1_h, cost_v1_h, fs_v1_h
        pgr = (acc - w_h) / gap_h
        pr = per_row_acc[name][holdout].astype(float)
        lo, hi = bootstrap_pair(pr, per_row_acc["v1@0.30"][holdout].astype(float))
        print(f"  {name:28s} {acc:7.4f} {cost:10.7f} {fs:11.4f} {pgr:7.4f}  "
              f"{acc - acc_v1_h:+.4f} [{lo:+.4f},{hi:+.4f}]")
        results[name] = (acc, cost, fs, pgr)

    # cost bootstrap vs v1
    print("\n  paired cost deltas vs v1 (holdout, per-row service cost):")
    seq = {
        "P1a_oracle_pair(ceiling)": (
            np.ones(len(tr)) * c_w + wfail * c_m
            + (wfail & (mid == 0)) * c_s),
        "P1b_disagree_escalate": np.ones(len(tr)) * (c_w + c_m)
        + (~ag) * c_s,
        "P1c_verifier_gated_pair": (np.ones(len(tr)) * c_w
                                    + (~vf_w_all) * c_m
                                    + ((~vf_w_all) & (~vf_m_all)) * c_s),
        "v1@0.30": np.where(v1_mask, c_s, c_w),
    }
    for name in ("P1a_oracle_pair(ceiling)", "P1b_disagree_escalate",
                 "P1c_verifier_gated_pair"):
        pc = seq[name][holdout]
        v1c = seq["v1@0.30"][holdout]
        lo, hi = bootstrap_pair(pc, v1c)
        print(f"  {name:28s} d_cost {pc.mean() - v1c.mean():+.7f} "
              f"[{lo:+.7f},{hi:+.7f}]")

    # ---------------- SECTION 6: gate verdicts
    print("\nSECTION 6: frozen-gate verdicts (holdout)")
    v1_acc, v1_cost = results["v1@0.30"][0], results["v1@0.30"][1]
    for name in ("P1b_disagree_escalate", "P1c_verifier_gated_pair",
                 "P1a_oracle_pair(ceiling)"):
        acc, cost, fs, pgr = results[name]
        q_up = acc > v1_acc and cost <= v1_cost
        c_down = cost <= 0.95 * v1_cost and acc >= v1_acc
        print(f"  {name:28s} keep_gate={'PASS' if (q_up or c_down) else 'FAIL'}"
              f"  (d_acc {acc - v1_acc:+.4f}, d_cost {cost - v1_cost:+.7f},"
              f" {(1 - cost / v1_cost) * 100:+.1f}% cost vs v1)")
    b_b = results["P1b_disagree_escalate"][0]
    b_c = results["P1c_verifier_gated_pair"][0]
    print(f"  P1c beats P1b (quality): {'YES' if b_c > b_b else 'NO'} "
          f"({b_c:.4f} vs {b_b:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
