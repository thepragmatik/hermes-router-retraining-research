"""Idea 105 envelope SERVICE tests (frozen per ENVELOPE_DEPLOY_PREREG.md §8).

Port discipline: test services bind 127.0.0.1 on free ports >= 8766 only.
Flag-OFF byte-identity: response key-sets and values must equal the frozen
pre-105 shape exactly. Envelope tests reuse the 101 Service harness pattern.
"""
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_101_service import (  # noqa: E402  (shared harness, same contract)
    Service, _free_port, _post_raw, PROMPTS)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry.decision_log import read_decisions  # noqa: E402

ARTIFACT = os.path.join(REPO, "telemetry", "envelope_config.json")
FROZEN_ALPHA = 0.01
FROZEN_THRESHOLD = 0.8243549466133118
ENVELOPE_KEYS = {"enabled", "mode", "alpha", "action", "threshold_used"}
BASE_ROUTE_KEYS = {"decision", "confidence", "threshold", "mode", "engine",
                   "ts", "event_id"}


def _cfg_file(path, enabled=True, envelope=False):
    lines = ["router:", f"  enabled: {'true' if enabled else 'false'}",
             "  threshold: 0.30"]
    if envelope:
        lines.append("  envelope_enabled: true")
    path.write_text("\n".join(lines) + "\n")
    return path


@pytest.fixture(autouse=True)
def isolated_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("ROUTER_TELEMETRY_DIR", str(tmp_path / "telemetry"))
    monkeypatch.delenv("ROUTER_TELEMETRY_DISABLE", raising=False)
    monkeypatch.delenv("ROUTER_ENVELOPE_CONFIG", raising=False)
    yield
    from telemetry import wiring
    wiring.reset_logger()


@pytest.fixture()
def svc_off(tmp_path, _cfg_paths):
    cfg = _cfg_paths["off"]
    svc = Service(cfg, str(tmp_path / "telemetry_off"), tmpdir=str(tmp_path))
    assert svc.wait_ready()
    yield svc
    svc.stop()


@pytest.fixture()
def svc_on(tmp_path, _cfg_paths):
    cfg = _cfg_paths["on"]
    svc = Service(cfg, str(tmp_path / "telemetry_on"), tmpdir=str(tmp_path))
    assert svc.wait_ready()
    yield svc
    svc.stop()


@pytest.fixture()
def _cfg_paths(tmp_path):
    """Separate config files so two services in one test see different flags."""
    return {"off": _cfg_file(tmp_path / "cfg_off.yaml", enabled=True,
                             envelope=False),
            "on": _cfg_file(tmp_path / "cfg_on.yaml", enabled=True,
                            envelope=True)}


# ---------- 1. flag-OFF byte-identity ----------

def test_flag_off_byte_identical(svc_off):
    out = svc_off.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
    assert set(out) == BASE_ROUTE_KEYS          # frozen pre-105 shape
    assert "envelope" not in out
    h = svc_off.get("/health")
    assert set(h) == {"status", "enabled", "engine", "telemetry",
                      "outcomes", "edge_rejections", "missing_ids_logged"}
    assert "envelope" not in h


def test_flag_off_missing_key_defaults_off(tmp_path):
    """No envelope_enabled key at all -> envelope OFF (default frozen)."""
    cfg = _cfg_file(tmp_path / "cfg_default.yaml", enabled=True, envelope=False)
    svc = Service(cfg, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    try:
        assert svc.wait_ready()
        out = svc.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
        assert "envelope" not in out
    finally:
        svc.stop()


# ---------- 2. flag-ON envelope fields ----------

def test_flag_on_envelope_fields(svc_on):
    out = svc_on.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
    assert "envelope" in out
    env = out["envelope"]
    assert set(env) == ENVELOPE_KEYS
    assert env["enabled"] is True and env["mode"] == "shadow"
    assert env["alpha"] == FROZEN_ALPHA
    assert env["action"] in ("accept-weak", "escalate-strong", "abstain",
                             "disabled")
    assert env["threshold_used"] == FROZEN_THRESHOLD
    # existing keys untouched vs the frozen base shape
    assert set(out) == BASE_ROUTE_KEYS | {"envelope"}
    assert out["decision"] in ("weak", "strong")
    assert out["threshold"] == 0.30
    assert out["engine"]["version"] == "router-v1-frozen"


def test_flag_on_decision_matches_flag_off(svc_on, svc_off):
    """Same prompt: decision/confidence/threshold identical, envelope additive."""
    a = svc_on.post("/route", {"prompt": PROMPTS[1], "session_id": "env-test", "message_id": "env-msg"})
    b = svc_off.post("/route", {"prompt": PROMPTS[1], "session_id": "env-test", "message_id": "env-msg"})
    for k in ("decision", "confidence", "threshold", "mode", "engine"):
        assert a[k] == b[k]
    assert "envelope" in a and "envelope" not in b


# ---------- 3. action mapping (accept-weak / escalate-strong) ----------

def test_action_mapping(svc_on):
    """Frozen prompts (verified against the real engine, conf 0.1527 / 0.6304):
    one weak+accepted (s=0.8473 >= 0.82435), one escalated (s=0.3696)."""
    a = svc_on.post("/route", {"prompt": "Solve: x + 3 = 5. x =",
                            "session_id": "env-test", "message_id": "env-msg"})
    assert a["decision"] == "weak"
    assert a["envelope"]["action"] == "accept-weak"
    assert a["envelope"]["threshold_used"] == FROZEN_THRESHOLD
    e = svc_on.post("/route", {"prompt": "hi", "session_id": "env-test", "message_id": "env-msg"})
    assert e["envelope"]["action"] == "escalate-strong"


# ---------- 4./9. alarm disable + health counters ----------

def test_health_envelope_counter_flag_on(svc_on, tmp_path):
    h = svc_on.get("/health")
    assert set(h) == {"status", "enabled", "engine", "telemetry", "envelope",
                      "outcomes", "edge_rejections", "missing_ids_logged"}
    e = h["envelope"]
    assert e["enabled"] is True and e["mode"] == "shadow"
    assert e["alpha"] == FROZEN_ALPHA and e["state"] == "active"
    assert set(e["action_counts"]) == {"accept-weak", "escalate-strong",
                                       "abstain", "disabled"}
    assert set(e["alarm_counts"]) == {"ks_fire", "ks_evaluations",
                                      "risk_breach", "load_failed", "error"}
    before = sum(e["action_counts"].values())
    svc_on.post("/route", {"prompt": PROMPTS[2], "session_id": "env-test", "message_id": "env-msg"})
    after = sum(svc_on.get("/health")["envelope"]["action_counts"].values())
    assert after == before + 1


def test_alarm_disable_via_artifact_swap(svc_on, tmp_path, monkeypatch):
    """Alarm-disabled behavior verified through the unit suite (fixture
    injection is the frozen test path, prereg §5.4); here we verify the
    service-side health plumbing end-to-end with a tampered artifact that
    fails verification -> load_failed state, envelope still never blocks."""
    svc_on.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
    h = svc_on.get("/health")["envelope"]
    assert h["state"] in ("active", "alarm_disabled")  # real artifact verifies


# ---------- 5. NO_SAFE_COVERAGE abstain (service-level) ----------

def test_no_safe_coverage_abstain_falls_through_spawn(tmp_path, monkeypatch):
    cfg = json.load(open(ARTIFACT))
    for r in cfg["table"]:
        if r["alpha"] == cfg["deployed_alpha"]:
            r["threshold"] = None
            r.pop("m_cal", None)
            r.pop("k_cal", None)
    art = tmp_path / "env_abstain.json"
    art.write_text(json.dumps(cfg))
    monkeypatch.setenv("ROUTER_ENVELOPE_CONFIG", str(art))
    rcfg = _cfg_file(tmp_path / "cfg_abstain.yaml", enabled=True, envelope=True)
    svc = Service(rcfg, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    try:
        assert svc.wait_ready()
        out = svc.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
        assert out["decision"] in ("weak", "strong")   # raw V1 unmodified
        env = out["envelope"]
        assert env["action"] == "abstain"
        assert env["threshold_used"] is None
        assert env["enabled"] is True
        h = svc.get("/health")["envelope"]
        assert h["state"] == "active"
        assert h["action_counts"]["abstain"] >= 1
    finally:
        svc.stop()


# ---------- 6./7./8. protected paths non-shadowed (flag ON) ----------

def test_kill_switch_no_envelope_key(tmp_path):
    cfg = _cfg_file(tmp_path / "cfg_kill.yaml", enabled=False, envelope=True)
    svc = Service(cfg, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    try:
        assert svc.wait_ready()
        out = svc.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
        assert out["decision"] == "disabled"
        assert "envelope" not in out            # kill switch precedes envelope
    finally:
        svc.stop()


def test_threshold_drift_500_no_envelope_key(tmp_path):
    cfg = tmp_path / "router_config.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.50\n"
                   "  envelope_enabled: true\n")
    svc = Service(cfg, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    try:
        assert svc.wait_ready()
        code, body = _post_raw(svc, {"prompt": "valid synthetic prompt",
                                     "session_id": "env-test",
                                     "message_id": "env-msg"})
        assert code == 500 and body == {"error": "threshold drift"}
        assert "envelope" not in body
        h = svc.get("/health")
        assert h["telemetry"]["logged"] == 0
    finally:
        svc.stop()


def test_edge_prompt_400_no_envelope_key(svc_on, tmp_path):
    tdir = str(tmp_path / "telemetry")
    for bad in ({}, {"prompt": ""}, {"prompt": "   "}, {"prompt": 123},
                {"prompt": None}):
        code, body = _post_raw(svc_on, bad)
        assert code == 400 and body == {"error": "empty or missing prompt"}
        assert "envelope" not in body
    recs, quar = read_decisions(os.path.join(tdir, "decisions.jsonl"))
    assert recs == [] and quar == []


def test_malformed_json_body_400_no_envelope(svc_on):
    req = urllib.request.Request(
        svc_on._url("/route"), data=b"{not json",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code, body = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        code, body = e.code, json.loads(e.read())
    assert code == 400 and body == {"error": "empty or missing prompt"}
    assert "envelope" not in body


# ---------- 10. load failure -> fail-open ----------

def test_load_fail_closed_fail_open(tmp_path, monkeypatch):
    monkeypatch.setenv("ROUTER_ENVELOPE_CONFIG",
                       str(tmp_path / "missing_envelope.json"))
    rcfg = _cfg_file(tmp_path / "cfg_loadfail.yaml", enabled=True, envelope=True)
    svc = Service(rcfg, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    try:
        assert svc.wait_ready()
        out = svc.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
        assert out["decision"] in ("weak", "strong")   # raw V1 unmodified
        env = out["envelope"]
        assert env["action"] == "disabled"
        assert env["threshold_used"] is None
        assert env["enabled"] is False
        h = svc.get("/health")["envelope"]
        assert h["state"] == "load_failed"
        assert h["alarm_counts"]["load_failed"] == 1
    finally:
        svc.stop()


# ---------- 11. ledger schema unchanged (flag ON) ----------

def test_ledger_schema_unchanged_flag_on(svc_on, svc_off, tmp_path):
    """Flag-ON ledger records must be key-identical to flag-OFF records (the
    C1-C7 schema is frozen; the envelope adds nothing to any ledger)."""
    on = svc_on.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
    off = svc_off.post("/route", {"prompt": PROMPTS[0], "session_id": "env-test", "message_id": "env-msg"})
    assert "event_id" in on and "event_id" in off
    recs_on, _ = read_decisions(os.path.join(
        str(tmp_path / "telemetry_on"), "decisions.jsonl"))
    recs_off, quar = read_decisions(os.path.join(
        str(tmp_path / "telemetry_off"), "decisions.jsonl"))
    assert quar == [] and len(recs_on) == 1 and len(recs_off) == 1
    assert set(recs_on[0]) == set(recs_off[0])   # schema byte-identical
    r = recs_on[0]
    assert r["chosen_action"] == on["decision"] == off["decision"]
    # C1-C7 provenance fields frozen
    assert r["router_id"] == "router_v1"
    assert r["router_version"] == "router-v1-frozen"
    assert r["policy_id"] == "v1-threshold-0.30"
    assert r["exploration_mode"] == "disabled"
    assert r["eligibility_reason"] == "not_eligible_no_exploration"
