"""Shadow smoke: verify the frozen V1 operating point through the CLI's
import path (router_v1.route.route). Expect routed acc 0.6395, frac_strong
0.7686 (n=3626), tolerance +/-0.02 (deployment_threshold.md, 2026-09-04)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from router_v1.route import route  # noqa: E402

VAL = Path.home() / "transfer-bundle/analysis/mf_val_frame.parquet"
df = pd.read_parquet(VAL)
assert len(df) == 3626, f"expected 3626 val rows, got {len(df)}"

pred_strong = []
for p in df["prompt"]:
    d, _c = route(p)
    pred_strong.append(d == "strong")

pred_strong = np.array(pred_strong)
weak_correct = (df["weak_correct"].fillna(0).astype(int) == 1).to_numpy()
strong_correct = (df["strong_correct"].fillna(0).astype(int) == 1).to_numpy()
routed_acc = float(np.where(pred_strong, strong_correct, weak_correct).mean())
fs = float(pred_strong.mean())
print(json.dumps({"n": len(df), "routed_acc": round(routed_acc, 4), "frac_strong": round(fs, 4)}))
assert abs(routed_acc - 0.6395) < 0.02, "routed acc drifted"
assert abs(fs - 0.7686) < 0.02, "frac_strong drifted"
print("SHADOW_SMOKE: PASS")
