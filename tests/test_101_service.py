"""Phase-3 tests: parity, robustness, kill switch, concurrency (T040-T043).

Port discipline: every test service binds 127.0.0.1 on an OS-assigned free
port asserted >= 8766. The production launchd service on 8765 is never
contacted or bound.
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry.decision_log import read_decisions  # noqa: E402
from telemetry.report import build_quality_report  # noqa: E402

CLI = os.path.join(REPO, "router_v1_cli.py")
SERVICE = os.path.join(REPO, "router_shadow.py")

PROMPTS = [
    "synthetic service prompt one",
    "synthetic service prompt two",
    "synthetic service prompt three",
]


@pytest.fixture(autouse=True)
def isolated_telemetry(tmp_path, monkeypatch):
    """Own ledger dir per test; env set before anything uses it."""
    monkeypatch.setenv("ROUTER_TELEMETRY_DIR", str(tmp_path / "telemetry"))
    monkeypatch.delenv("ROUTER_TELEMETRY_DISABLE", raising=False)
    monkeypatch.delenv("ROUTER_SESSION_ID", raising=False)
    monkeypatch.delenv("ROUTER_MESSAGE_ID", raising=False)
    yield
    from telemetry import wiring
    wiring.reset_logger()


def _free_port():
    while True:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        if port >= 8766:
            return port


class Service:
    def __init__(self, config_path, telemetry_dir, tmpdir=None):
        self.port = _free_port()
        assert self.port >= 8766
        # stderr to a FILE (not PIPE): warmup prints progress; a filled pipe
        # would deadlock the child. Keeps crash output inspectable.
        self.err_path = os.path.join(
            str(tmpdir or "/tmp"), f"router_shadow_test_{self.port}.err")
        self._err_fh = open(self.err_path, "w")
        self.proc = subprocess.Popen(
            [sys.executable, SERVICE, "--port", str(self.port)],
            env=dict(os.environ, ROUTER_CONFIG=str(config_path),
                     ROUTER_TELEMETRY_DIR=telemetry_dir),
            stdout=subprocess.DEVNULL, stderr=self._err_fh)

    def stderr_text(self):
        try:
            self._err_fh.flush()
        except Exception:
            pass
        with open(self.err_path) as f:
            return f.read()

    def wait_ready(self, timeout=300):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.get("/health")
                return True
            except Exception:
                if self.proc.poll() is not None:
                    raise RuntimeError(
                        f"service died: {self.stderr_text()[-800:]}")
                time.sleep(0.2)
        return False

    def _url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def get(self, path, timeout=30):
        with urllib.request.urlopen(self._url(path), timeout=timeout) as r:
            return json.loads(r.read())

    def post(self, path, payload, timeout=120):
        req = urllib.request.Request(
            self._url(path), data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self._err_fh.close()


@pytest.fixture()
def service(tmp_path, enabled_config):
    svc = Service(enabled_config, str(tmp_path / "telemetry"), tmpdir=str(tmp_path))
    assert svc.wait_ready(), "service did not become healthy"
    yield svc
    svc.stop()


@pytest.fixture()
def enabled_config(tmp_path):
    cfg = tmp_path / "router_config.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.30\n")
    return cfg


def _run_cli(prompt, config_path, telemetry_dir, extra_args=(), env_extra=None,
             timeout=180):
    env = dict(os.environ, ROUTER_CONFIG=str(config_path),
               ROUTER_TELEMETRY_DIR=telemetry_dir)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, CLI, "--prompt", prompt, *extra_args],
                          capture_output=True, text=True, env=env, timeout=timeout)


# ---------- T042: service traffic actually logs + parity (A14) ----------

def test_service_route_logs_decision(service, tmp_path):
    out = service.post("/route", {"prompt": PROMPTS[0]})
    assert out["decision"] in ("weak", "strong")
    assert 0.0 <= out["confidence"] <= 1.0
    assert out["mode"] == "shadow"
    assert out["engine"]["version"] == "router-v1-frozen"
    assert len(out["event_id"]) == 32  # uuid4 hex — G1 identity, not prompt_id 0
    recs, quar = read_decisions(os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl"))
    assert quar == []
    assert len(recs) == 1
    r = recs[0]
    assert r["event_id"] == out["event_id"]
    assert r["prompt_hash"] and len(r["prompt_hash"]) == 12
    assert r["router_version"] == "router-v1-frozen"
    assert r["policy_id"] == "v1-threshold-0.30"
    assert r["chosen_action"] == out["decision"]


def test_health_exposes_telemetry_counters(service):
    h = service.get("/health")
    assert h["status"] == "ok"
    assert h["telemetry"]["logged"] >= 0
    assert "errors" in h["telemetry"]


def test_cli_service_parity(service, tmp_path, enabled_config):
    """A14: same prompt through both paths -> same decision/confidence/
    threshold; both ledger records carry identical provenance fields."""
    tdir = str(tmp_path / "telemetry")
    p = _run_cli(PROMPTS[0], enabled_config, tdir)
    assert p.returncode == 0, p.stderr[-800:]
    cli_out = json.loads(p.stdout.strip().splitlines()[-1])
    svc_out = service.post("/route", {"prompt": PROMPTS[0]})
    # same decision for the same prompt (frozen deterministic router)
    assert cli_out["decision"] == svc_out["decision"]
    assert abs(cli_out["confidence"] - svc_out["confidence"]) < 1e-9
    assert cli_out["threshold"] == svc_out["threshold"] == 0.30
    assert cli_out["engine"] == svc_out["engine"]
    # both recorded in the shared ledger with the full provenance set
    recs, quar = read_decisions(os.path.join(tdir, "decisions.jsonl"))
    assert quar == [] and len(recs) == 2
    by_id = {r["event_id"]: r for r in recs}
    assert cli_out["event_id"] in by_id and svc_out["event_id"] in by_id
    for r in recs:
        assert r["router_id"] == "router_v1"
        assert r["router_version"] == "router-v1-frozen"
        assert r["representation_version"] == "bge-small-en-v1.5"
        assert r["price_snapshot_id"] == "historical-frozen-2026-09"
        assert set(r["model_provider_revision"]) == {"weak", "strong"}
    # response shape kept backwards compatible (T041)
    for o in (cli_out, svc_out):
        assert "decision" in o and "confidence" in o and "threshold" in o
        assert "mode" in o and "engine" in o and "ts" in o


def test_duplicate_prompt_stable_hash_distinct_ids(service, tmp_path):
    a = service.post("/route", {"prompt": PROMPTS[1]})
    b = service.post("/route", {"prompt": PROMPTS[1]})
    assert a["event_id"] != b["event_id"]
    recs, _ = read_decisions(os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl"))
    assert recs[0]["prompt_hash"] == recs[1]["prompt_hash"]


def test_caller_session_message_hashes_logged_not_raw(service, tmp_path):
    out = service.post("/route", {"prompt": PROMPTS[2],
                                  "session_id": "RAW-SESSION-VALUE-xyz",
                                  "message_id": "RAW-MESSAGE-VALUE-xyz",
                                  "traffic_stratum": "test_stratum"})
    recs, _ = read_decisions(os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl"))
    r = [x for x in recs if x["event_id"] == out["event_id"]][0]
    assert r["session_id_hash"] and r["message_id_hash"]
    assert len(r["session_id_hash"]) == 12
    assert r["traffic_stratum"] == "test_stratum"
    raw = open(os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl")).read()
    assert "RAW-SESSION-VALUE-xyz" not in raw
    assert "RAW-MESSAGE-VALUE-xyz" not in raw


# ---------- T043: kill switch / threshold / config / I/O failure / restart / concurrency ----------

def test_kill_switch_disables_without_logging(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: false\n  threshold: 0.30\n")
    tdir = str(tmp_path / "telemetry")
    p = _run_cli("hello", cfg, tdir)
    assert p.returncode == 0
    out = json.loads(p.stdout.strip().splitlines()[-1])
    assert out["decision"] == "disabled"
    # disabled path: no decision event (no route happened)
    assert not os.path.exists(os.path.join(tdir, "decisions.jsonl"))


def test_missing_config_fails_closed(tmp_path):
    tdir = str(tmp_path / "telemetry")
    p = _run_cli("hello", tmp_path / "nope.yaml", tdir)
    assert p.returncode == 0
    assert json.loads(p.stdout.strip().splitlines()[-1])["decision"] == "disabled"


def test_threshold_drift_cli_exit2(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.50\n")
    tdir = str(tmp_path / "telemetry")
    p = _run_cli("hello", cfg, tdir)
    assert p.returncode == 2
    assert not os.path.exists(os.path.join(tdir, "decisions.jsonl"))


def test_threshold_drift_http_500(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.50\n")
    svc = Service(cfg, str(tmp_path / "telemetry"))
    try:
        assert svc.wait_ready()
        with pytest.raises(urllib.error.HTTPError) as ei:
            svc.post("/route", {"prompt": "hello"})
        assert ei.value.code == 500
        h = svc.get("/health")
        # drift path: no decision events logged
        assert h["telemetry"]["logged"] == 0
    finally:
        svc.stop()


def test_logging_io_failure_route_survives(tmp_path, enabled_config):
    """A11: read-only telemetry dir -> route succeeds, error counter visible."""
    tdir = tmp_path / "telemetry"
    tdir.mkdir()
    os.chmod(tdir, 0o555)  # read-only
    try:
        p = _run_cli("hello world", enabled_config, str(tdir))
        assert p.returncode == 0, p.stderr[-500:]
        out = json.loads(p.stdout.strip().splitlines()[-1])
        assert out["decision"] in ("weak", "strong")
        assert "event_id" not in out  # logging failed; route unaffected
    finally:
        os.chmod(tdir, 0o755)


def test_logging_io_failure_http_route_survives(tmp_path, enabled_config):
    tdir = tmp_path / "telemetry"
    tdir.mkdir()
    os.chmod(tdir, 0o555)
    try:
        svc = Service(enabled_config, str(tdir))
        try:
            assert svc.wait_ready()
            out = svc.post("/route", {"prompt": "hello world"})
            assert out["decision"] in ("weak", "strong")
            assert "event_id" not in out
            h = svc.get("/health")
            assert h["telemetry"]["errors"] >= 1  # visible error counter (A11)
        finally:
            svc.stop()
    finally:
        os.chmod(tdir, 0o755)


def test_service_restart_appends_without_clobber(tmp_path, enabled_config):
    tdir = str(tmp_path / "telemetry")
    for _ in range(2):  # start, route, stop, start again
        svc = Service(enabled_config, tdir)
        assert svc.wait_ready()
        svc.post("/route", {"prompt": "restart synthetic prompt"})
        svc.stop()
    recs, quar = read_decisions(os.path.join(tdir, "decisions.jsonl"))
    assert quar == []
    assert len(recs) == 2
    assert len({r["event_id"] for r in recs}) == 2


def test_concurrent_requests_all_logged_exactly_once(service, tmp_path):
    n = 12
    with ThreadPoolExecutor(max_workers=6) as ex:
        outs = list(ex.map(lambda i: service.post(
            "/route", {"prompt": f"concurrent synthetic prompt {i}"}), range(n)))
    assert all("event_id" in o for o in outs)
    assert len({o["event_id"] for o in outs}) == n
    recs, quar = read_decisions(os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl"))
    assert quar == []
    assert len(recs) == n
    assert len({r["event_id"] for r in recs}) == n


# ---------- T044-edge: empty/missing/whitespace/non-string prompt 400 ----------
# Contract frozen in results/101/EDGE_REJECTION_PREREG.md (prereg commit
# precedes this code). 400 = NO model call, NO ledger write.

def _post_raw(svc, payload, timeout=120):
    """POST returning (status, body_dict); does not raise on 4xx/5xx."""
    req = urllib.request.Request(
        svc._url("/route"), data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _ledger_rows(tdir):
    from telemetry.decision_log import read_decisions
    path = os.path.join(tdir, "decisions.jsonl")
    if not os.path.exists(path):
        return [], []
    return read_decisions(path)


@pytest.mark.parametrize("payload", [
    {"prompt": ""},          # empty
    {},                      # missing prompt field
    {"prompt": "   "},       # whitespace-only
    {"prompt": 123},         # non-string int
    {"prompt": None},        # null
])
def test_invalid_prompt_400_no_side_effects(service, tmp_path, payload):
    tdir = str(tmp_path / "telemetry")
    code, body = _post_raw(service, payload)
    assert code == 400
    assert body == {"error": "empty or missing prompt"}
    recs, quar = _ledger_rows(tdir)
    assert recs == [] and quar == []
    # service stays healthy and unchanged after the 400s
    h = service.get("/health")
    assert h["status"] == "ok"
    assert set(h) == {"status", "enabled", "engine", "telemetry"}
    assert h["telemetry"]["logged"] == 0
    assert h["telemetry"]["errors"] == 0


def test_valid_prompt_after_400s_unchanged(service, tmp_path):
    for bad in ({}, {"prompt": ""}, {"prompt": None}):
        code, _ = _post_raw(service, bad)
        assert code == 400
    out = service.post("/route", {"prompt": PROMPTS[0]})
    assert out["decision"] in ("weak", "strong")
    assert out["mode"] == "shadow" and "event_id" in out
    recs, _ = _ledger_rows(str(tmp_path / "telemetry"))
    assert len(recs) == 1


def test_invalid_prompt_does_not_shadow_threshold_drift_500(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.50\n")
    svc = Service(cfg, str(tmp_path / "telemetry"))
    try:
        assert svc.wait_ready()
        code, body = _post_raw(svc, {"prompt": ""})
        # frozen (erratum): validation precedes the threshold check, so the
        # empty prompt's 400 wins; the drift 500 stays reachable for valid
        # prompts (test_threshold_drift_http_500).
        assert code == 400
        assert body == {"error": "empty or missing prompt"}
        code, body = _post_raw(svc, {"prompt": "valid synthetic prompt"})
        assert code == 500
        assert body == {"error": "threshold drift"}
    finally:
        svc.stop()


def test_invalid_prompt_does_not_shadow_kill_switch(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: false\n  threshold: 0.30\n")
    svc = Service(cfg, str(tmp_path / "telemetry"))
    try:
        assert svc.wait_ready()
        code, body = _post_raw(svc, {"prompt": "   "})
        # frozen: input validation precedes service-state checks
        assert code == 400
        assert body == {"error": "empty or missing prompt"}
    finally:
        svc.stop()


def test_malformed_json_body_now_400(tmp_path, enabled_config):
    svc = Service(enabled_config, str(tmp_path / "telemetry"))
    try:
        assert svc.wait_ready()
        req = urllib.request.Request(
            svc._url("/route"), data=b"{not json",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                code, body = r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            code, body = e.code, json.loads(e.read())
        assert code == 400 and body == {"error": "empty or missing prompt"}
    finally:
        svc.stop()


# ---------- env-based disable (logging off switch) ----------

def test_telemetry_env_disable(tmp_path, enabled_config):
    tdir = str(tmp_path / "telemetry")
    p = _run_cli("hello", enabled_config, tdir,
                 env_extra={"ROUTER_TELEMETRY_DISABLE": "1"})
    assert p.returncode == 0
    out = json.loads(p.stdout.strip().splitlines()[-1])
    assert out["decision"] in ("weak", "strong")
    assert "event_id" not in out
    assert not os.path.exists(os.path.join(tdir, "decisions.jsonl"))
