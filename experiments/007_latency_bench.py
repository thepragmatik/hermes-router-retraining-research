"""Latency of the router under the three wiring choices + disabled baseline.
Zero API spend. Uses a TEMP enabled config via ROUTER_CONFIG — the real
router_config.yaml is never modified. Writes evidence/ab/latency_bench.json."""
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
OUT = REPO / "evidence/ab"

tmp_cfg = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
tmp_cfg.write("router:\n  enabled: true\n  threshold: 0.30\n")
tmp_cfg.close()
os.environ["ROUTER_CONFIG"] = tmp_cfg.name

import pandas as pd                     # noqa: E402
from router_v1.route import route       # noqa: E402
import router_shadow                    # noqa: E402  (Handler only; no server start)

df = pd.read_parquet(Path.home() / "transfer-bundle/analysis/mf_val_frame.parquet")
prompts = list(df["prompt"].head(100))
out = {}

route(prompts[0])  # warm model load
lat = []
for p in prompts:
    t0 = time.perf_counter()
    route(p)
    lat.append(time.perf_counter() - t0)
out["in_process"] = {"n": len(lat), "p50_s": round(statistics.median(lat), 4),
                     "p95_s": round(sorted(lat)[int(0.95 * len(lat))], 4)}

cli = []
for p in prompts[:5]:
    t0 = time.perf_counter()
    subprocess.run(["python3", str(REPO / "router_v1_cli.py"), "--prompt", p],
                   capture_output=True, text=True, check=True)
    cli.append(time.perf_counter() - t0)
out["cli_enabled"] = {"n": len(cli), "mean_s": round(statistics.mean(cli), 3)}

os.environ["ROUTER_CONFIG"] = "/nonexistent"  # disabled path: no model import
cli_dis = []
for p in prompts[:5]:
    t0 = time.perf_counter()
    subprocess.run(["python3", str(REPO / "router_v1_cli.py"), "--prompt", p],
                   capture_output=True, text=True, check=True)
    cli_dis.append(time.perf_counter() - t0)
out["cli_disabled"] = {"n": 5, "mean_s": round(statistics.mean(cli_dis), 3)}

os.environ["ROUTER_CONFIG"] = tmp_cfg.name
srv = ThreadingHTTPServer(("127.0.0.1", 8766), router_shadow.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
try:
    def post(prompt):
        req = urllib.request.Request(
            "http://127.0.0.1:8766/route",
            data=json.dumps({"prompt": prompt}).encode(),
            headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=60) as r:
            json.loads(r.read())
        return time.perf_counter() - t0

    post(prompts[0])  # warm first-call model load inside the service
    http_lat = [post(p) for p in prompts[:20]]
    out["http_service"] = {"n": len(http_lat),
                           "p50_s": round(statistics.median(http_lat), 4),
                           "p95_s": round(sorted(http_lat)[int(0.95 * len(http_lat))], 4)}
finally:
    srv.shutdown()
    os.unlink(tmp_cfg.name)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "latency_bench.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
