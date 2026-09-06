import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "router_v1_cli.py"


def run_cli(prompt, tmp_config=None):
    env = dict(os.environ)
    if tmp_config is not None:
        env["ROUTER_CONFIG"] = str(tmp_config)
    p = subprocess.run(
        [sys.executable, str(CLI), "--prompt", prompt],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def test_disabled_by_default_when_config_missing(tmp_path):
    # No config file anywhere -> must fail CLOSED, not route.
    out = run_cli("hello world", tmp_config=tmp_path / "nope.yaml")
    assert out["decision"] == "disabled"


def test_disabled_when_flag_false(tmp_path):
    cfg = tmp_path / "router_config.yaml"
    cfg.write_text("router:\n  enabled: false\n  threshold: 0.30\n")
    out = run_cli("hello world", tmp_config=cfg)
    assert out["decision"] == "disabled"


def test_threshold_drift_exits_nonzero(tmp_path):
    cfg = tmp_path / "router_config.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.50\n")
    env = dict(os.environ)
    env["ROUTER_CONFIG"] = str(cfg)
    p = subprocess.run([sys.executable, str(CLI), "--prompt", "hi"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert p.returncode == 2, p.stdout


def test_enabled_produces_known_decisions(tmp_path):
    cfg = tmp_path / "router_config.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.30\n")
    out = run_cli("What is the capital of France?", tmp_config=cfg)
    assert out["decision"] in ("weak", "strong")
    assert 0.0 <= out["confidence"] <= 1.0
    assert out["mode"] == "shadow"
    assert out["engine"]["name"] == "v1_mf_router"
    assert out["engine"]["version"] == "router-v1-frozen"
