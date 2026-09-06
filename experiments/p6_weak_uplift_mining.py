#!/usr/bin/env python3
"""Phase G — P6 failure-focused cheap-tier uplift: MINING stage ($0).

Preregistration: experiments/PREREG_P6.md (frozen before scoring).
Scope decision (prereg-disclosed): the MISSION runs on stored responses with a
$0 budget and no SPEND_GO authorization; P6's training stage (LoRA/QLoRA on
mined pairs) is therefore out of scope for this mission. This script executes
the mining/clustering stage and evaluates the *economic ceiling* the mined
data could buy: how many v1-weak failures are (a) recurring clusters and
(b) actually repaired by the strong model (i.e., real training signal), vs the
structural stratum where BOTH models fail (no signal — P3 finding).

Deliverable: results/P6_WEAK_UPLIFT.md.
Run: python3 experiments/p6_weak_uplift_mining.py > results/P6_raw.txt 2>&1
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from p3_internal_confidence import (  # noqa: E402
    WEAK, STRONG, load_train, binarize, md5_bucket, unwrap,
)
from p1_p2_sampling_verifiers import (  # noqa: E402
    MID, extract_answer, agree_rule,
)

SENT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 22M params, cached


def main():
    tr = load_train()
    n = len(tr)
    bucket = tr["prompt"].map(lambda p: md5_bucket(p, 42)).to_numpy()
    holdout = bucket < 1500
    dev = ~holdout
    print(f"SECTION 0: train {n} | dev-fit {int(dev.sum())} | "
          f"pivot-holdout {int(holdout.sum())} | test rows loaded: 0 (sealed)")

    y_weak = binarize(tr[WEAK])
    y_mid = binarize(tr[MID])
    y_strong = binarize(tr[STRONG])

    # ---- v1 partition (unchanged trust stack reference) ----
    v1m = np.load(
        os.path.join(os.path.dirname(__file__), "..", "results",
                     "v1_train_probs.npy")) >= 0.30
    assert len(v1m) == n and 0.1 < v1m.mean() < 0.95

    # v1-weak rows are ~v1m (v1m = route-strong mask). Split v1-weak
    # failures by signal availability (train-safe, no semantics)
    vw_fail = ~v1m & (y_weak == 0)
    stratum = np.where(v1m, "v1-strong",
                       np.where(vw_fail,
                                np.where(y_strong == 1,
                                         "weak-fail-strong-ok", "both-fail"),
                                "weak-ok"))
    c = Counter(stratum[dev])
    print("SECTION 1: v1-weak failure strata (dev-fit)")
    for k in ("weak-fail-strong-ok", "both-fail"):
        print(f"  {k:22s} {c.get(k, 0):6d}  ({c.get(k, 0)/dev.sum():.4f} of dev)")
    n_vw_fail = c.get("weak-fail-strong-ok", 0) + c.get("both-fail", 0)
    print(f"  both-fail share of v1-weak failures (dev): "
          f"{c.get('both-fail',0)/max(1, n_vw_fail):.4f}")

    # ---- mining: which failed weak rows have real repair signal? ----
    mine = stratum == "weak-fail-strong-ok"          # strong repairs available
    print(f"\nSECTION 2: mined pairs weak-fail -> strong-repair: "
          f"{int((mine & dev).sum())} dev / {int((mine & holdout).sum())} holdout")

    # repetition analysis on TRAIN-SAFE signal: same prompt family + same
    # normalized prompt template -> recurring failure patterns
    fam = tr["eval_name"].to_numpy()
    rep = Counter(zip(fam[mine & dev], tr["prompt"].map(
        lambda p: re.sub(r"\d+", "#", p)[:120])[mine & dev]))
    recurring = {k for k, v in rep.items() if v >= 2}
    n_rec = sum(v for k, v in rep.items() if v >= 2)
    print(f"  recurring failure patterns (same template, >=2 occurrences): "
          f"{len(recurring)} patterns covering {n_rec} dev rows "
          f"({n_rec/max(1,int((mine & dev).sum())):.4f} of mined pairs)")

    # ---- economic ceiling of mining (unchanged v1 stack) ----
    # If ALL mined dev pairs were repaired into the weak model (perfect
    # uplift), v1-weak failures would drop by the mined count; quality gain
    # equals weak->strong correctness transfer on those rows.
    c_w = float(tr[f"{WEAK}|total_cost"].mean())
    c_m = float(tr[f"{MID}|total_cost"].mean())
    c_s = float(tr[f"{STRONG}|total_cost"].mean())
    print(f"stored cost/call: weak ${c_w:.7f} mid ${c_m:.7f} strong ${c_s:.7f}")

    dev_i = np.where(dev)[0]
    acc_v1_dev = float((np.where(v1m, y_strong, y_weak)[dev]).mean())
    cost_v1_dev = float((c_w + v1m[dev] * c_s).mean())
    # perfect narrow uplift: weak now correct on mined rows (strong's answers
    # there are correct by construction of the stratum); those rows are
    # v1-weak by construction, so v1's routed accuracy rises 1-for-1
    n_mined = int((mine & dev).sum())
    acc_up = acc_v1_dev + n_mined / dev.sum()
    # escalation savings ceiling: escalations justified ONLY by weak failures
    # that remain (both-fail stratum keeps strong escalation as before)
    print(f"\nSECTION 3: perfect narrow-uplift ceiling (dev, unchanged v1 stack)")
    print(f"  v1 baseline: acc {acc_v1_dev:.4f} cost {cost_v1_dev:.7f}")
    print(f"  all {n_mined} mined pairs repaired: acc {acc_up:.4f} "
          f"(+{n_mined/dev.sum():+.4f})")

    # escalation reduction: rows where the ONLY reason to escalate was weak
    # failure that mining removes -> none for v1 (v1 escalates via its own
    # trigger, not weak failure), so savings = 0 for v1; the saving exists
    # only for weak-first stacks (all dead per P4)
    print("  escalation-savings ceiling under v1: $0.0000000 (v1's trigger is "
          "independent of weak failures; savings would accrue only to "
          "weak-first stacks, which P4 killed)")

    # ---- semantic clustering of mined failures (P6 requires semantics for
    # ANALYSIS, not routing) ----
    print("\nSECTION 4: semantic clustering of mined failures "
          "(analysis only, never routing)")
    from sentence_transformers import SentenceTransformer
    st = SentenceTransformer(SENT_MODEL, device="cpu")
    prompts = tr["prompt"][mine & dev].tolist()
    emb = st.encode(prompts, batch_size=256, show_progress_bar=False,
                    normalize_embeddings=True)
    labels = tr["eval_name"][mine & dev].to_numpy()
    # family centroids -> is the mined mass concentrated (curriculum-friendly)
    fams = sorted(set(labels))
    centroid = {f: emb[labels == f].mean(axis=0) for f in fams}
    for f in centroid:
        centroid[f] /= np.linalg.norm(centroid[f]) + 1e-12
    # concentration: share of mined rows within cosine 0.55 of own-family
    # centroid AND that family holding >=20 mined rows (clusterable mass)
    near = np.array([float(emb[i] @ centroid[labels[i]]) >= 0.55
                     for i in range(len(labels))])
    big = {f for f in fams if (labels == f).sum() >= 20}
    in_big_near = near & np.isin(labels, list(big))
    print(f"  mined rows in clusterable families (>=20 rows): "
          f"{int(np.isin(labels, list(big)).sum())}/{len(labels)}")
    print(f"  rows near own-family centroid (cos>=0.55): {int(near.sum())} "
          f"({near.mean():.4f})")
    print(f"  clusterable curriculum mass (both): {int(in_big_near.sum())} "
          f"({in_big_near.sum()/len(labels):.4f} of mined)")

    # top families by mined mass (for the curriculum table)
    fam_counts = Counter(labels)
    print("  top-10 mined failure families:")
    for f, k in fam_counts.most_common(10):
        print(f"    {f:55s} {k:5d}  centroid_cos_ge_0.55 "
              f"{float((near & (labels == f)).sum())/k:.3f}")

    verdict = {
        "mined_pairs_dev": int((mine & dev).sum()),
        "recurring_templates": len(recurring),
        "clusterable_mass_share": round(float(in_big_near.mean()), 4),
        "perfect_uplift_acc_gain": round(float((mine & dev).sum() / dev.sum()), 4),
        "v1_escalation_savings": 0.0,
        "weak_first_savings_note": "weak-first stacks killed in P4",
    }
    os.makedirs("results", exist_ok=True)
    with open("results/p6_mining_summary.json", "w") as f:
        json.dump(verdict, f, indent=2)
    print(f"\nVERDICT-SUMMARY: {json.dumps(verdict)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
