"""Run the full idea-101 outcome-capture prereg test matrix.

Red-first: run this BEFORE implementing /outcome, the join tool, and the
schema bump; every test below must fail or error. Then implement, then all
green alongside the pre-existing suite.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry.decision_log import read_decisions  # noqa: E402
from telemetry.schema import (SCHEMA_VERSION, make_decision_event,  # noqa: E402
                              validate_decision)

from tests.test_101_service import (Service, _run_cli, enabled_config,  # noqa: E402,F401
                                    isolated_telemetry, service)

JOIN_TOOL = os.path.join(REPO, "experiments", "101", "join_outcomes.py")


def _post_raw(svc, path, payload):
    """POST and return (status_code, body_dict). Never raises on 4xx/5xx."""
    data = (json.dumps(payload).encode() if payload is not None
            else b"{definitely not json")
    req = urllib.request.Request(
        f"http://127.0.0.1:{svc.port}{path}", data=data,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.code, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _outcomes_path(tmp_path):
    return os.path.join(str(tmp_path / "telemetry"), "outcomes.jsonl")


def _dec_path(tmp_path):
    return os.path.join(str(tmp_path / "telemetry"), "decisions.jsonl")


# ---------------- POST /outcome ----------------

def test_outcome_happy_path(service, tmp_path):
    r = service.post("/route", {"prompt": "outcome happy synthetic prompt", "session_id": "s", "message_id": "m"})
    eid = r["event_id"]
    code, body = _post_raw(service, "/outcome",
                           {"event_id": eid, "outcome": "success",
                            "cost": 0.01, "latency_ms": 123, "note": "ok"})
    assert code == 202, (code, body)
    assert body["status"] == "logged"
    assert len(body["outcome_id"]) == 32
    rows = [json.loads(l) for l in open(_outcomes_path(tmp_path))]
    assert len(rows) == 1
    o = rows[0]
    assert o["event_id"] == eid
    assert o["outcome"] == "success"
    assert o["cost"] == 0.01 and o["latency_ms"] == 123
    assert o["schema_version"] == SCHEMA_VERSION
    assert "ts" in o and len(o["outcome_id"]) == 32


def test_outcome_unknown_event_id_404(service):
    code, body = _post_raw(service, "/outcome",
                           {"event_id": "a" * 32, "outcome": "success"})
    assert code == 404
    assert body == {"error": "unknown event_id"}


def test_outcome_ambiguous_prefix_409(service, tmp_path):
    service.post("/route", {"prompt": "prefix synthetic prompt A", "session_id": "s", "message_id": "m"})
    service.post("/route", {"prompt": "prefix synthetic prompt B", "session_id": "s", "message_id": "m2"})
    service.post("/route", {"prompt": "prefix synthetic prompt C", "session_id": "s", "message_id": "m3"})
    decs, _ = read_decisions(_dec_path(tmp_path))
    ids = [d["event_id"] for d in decs]
    shared = None
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            for k in range(2, 33):
                if ids[i][:k] == ids[j][:k]:
                    shared = ids[i][:k]
    if shared is None:
        pytest.skip("no naturally ambiguous prefix among fixture ids")
    code, body = _post_raw(service, "/outcome",
                           {"event_id": shared, "outcome": "success"})
    assert code == 409, (shared, code, body)
    assert body == {"error": "ambiguous event_id prefix"}


def test_outcome_ambiguous_prefix_deterministic(tmp_path):
    """Pre-seed a decisions ledger with two ids sharing a prefix; the
    disabled-config service (no model needed) must 409 on the shared prefix."""
    ddir = tmp_path / "telemetry"
    ddir.mkdir(parents=True, exist_ok=True)
    id1 = "ab" + "1" * 30
    id2 = "ab" + "2" * 30
    rows = [{"schema_version": SCHEMA_VERSION, "event_id": eid,
             "chosen_action": "weak", "prompt_hash": "0" * 12,
             "session_id_hash": None, "message_id_hash": None,
             "ts": "2026-09-09T00:00:00+00:00"} for eid in (id1, id2)]
    (ddir / "decisions.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: false\n  threshold: 0.30\n")
    svc = Service(cfg, str(ddir))
    try:
        assert svc.wait_ready()
        code, body = _post_raw(svc, "/outcome",
                               {"event_id": "ab", "outcome": "success"})
        assert code == 409, (code, body)
        assert body == {"error": "ambiguous event_id prefix"}
        # 3-char prefix resolves to exactly one -> 202
        code, body = _post_raw(svc, "/outcome",
                               {"event_id": "ab1", "outcome": "success"})
        assert code == 202, (code, body)
        assert body["event_id"] == id1
        # unknown prefix -> 404
        code, body = _post_raw(svc, "/outcome",
                               {"event_id": "ff", "outcome": "success"})
        assert code == 404 and body == {"error": "unknown event_id"}
    finally:
        svc.stop()


def test_outcome_prefix_of_one_is_202(service, tmp_path):
    eid = service.post("/route", {"prompt": "prefix one synthetic prompt", "session_id": "s", "message_id": "m"})["event_id"]
    code, body = _post_raw(service, "/outcome",
                           {"event_id": eid[:6], "outcome": "failure"})
    assert code == 202, (code, body)
    assert body["event_id"] == eid  # resolved to the full id


def test_outcome_bad_prefix_shape_400(service):
    for bad in ("", "xyz", "g" * 32, "a" * 31 + "z"):
        code, body = _post_raw(service, "/outcome",
                               {"event_id": bad, "outcome": "success"})
        assert code == 400, (bad, code, body)
        assert body == {"error": "invalid event_id"}


def test_outcome_malformed_and_invalid_shapes(service, tmp_path):
    eid = service.post("/route", {"prompt": "shape synthetic prompt", "session_id": "s", "message_id": "m"})["event_id"]
    cases = [
        (None, 400, {"error": "malformed json"}),          # non-JSON body
        ({"outcome": "success"}, 400, {"error": "invalid event_id"}),
        ({"event_id": "", "outcome": "success"}, 400,
         {"error": "invalid event_id"}),
        ({"event_id": 123, "outcome": "success"}, 400,
         {"error": "invalid event_id"}),
        ({"event_id": eid}, 400, {"error": "invalid outcome"}),
        ({"event_id": eid, "outcome": "win"}, 400,
         {"error": "invalid outcome"}),
        ({"event_id": eid, "outcome": "success", "cost": -1}, 400,
         {"error": "invalid cost"}),
        ({"event_id": eid, "outcome": "success", "cost": 0}, 400,
         {"error": "invalid cost"}),
        ({"event_id": eid, "outcome": "success", "cost": "x"}, 400,
         {"error": "invalid cost"}),
        ({"event_id": eid, "outcome": "success", "latency_ms": 0}, 400,
         {"error": "invalid latency_ms"}),
        ({"event_id": eid, "outcome": "success", "latency_ms": 1.5}, 400,
         {"error": "invalid latency_ms"}),
        ({"event_id": eid, "outcome": "success", "note": "x" * 201}, 400,
         {"error": "invalid note"}),
    ]
    for payload, code, body in cases:
        got_code, got_body = _post_raw(service, "/outcome", payload)
        assert got_code == code, (payload, got_body)
        assert got_body == body, (payload, got_body)
    assert not os.path.exists(_outcomes_path(tmp_path))


def test_outcome_duplicate_409_no_second_append(service, tmp_path):
    eid = service.post("/route", {"prompt": "dup synthetic prompt", "session_id": "s", "message_id": "m"})["event_id"]
    code, _ = _post_raw(service, "/outcome",
                        {"event_id": eid, "outcome": "success"})
    assert code == 202
    code2, body2 = _post_raw(service, "/outcome",
                             {"event_id": eid, "outcome": "success"})
    assert code2 == 409
    assert body2 == {"error": "duplicate outcome"}
    rows = [json.loads(l) for l in open(_outcomes_path(tmp_path))]
    assert len(rows) == 1
    # same event, different vocabulary value is NOT a duplicate
    code3, _ = _post_raw(service, "/outcome",
                         {"event_id": eid, "outcome": "failure"})
    assert code3 == 202
    assert len([json.loads(l) for l in open(_outcomes_path(tmp_path))]) == 2


def test_outcome_does_not_touch_decisions_and_needs_no_model(service, tmp_path):
    eid = service.post("/route", {"prompt": "outcome no-touch synthetic", "session_id": "s", "message_id": "m"})["event_id"]
    before = open(_dec_path(tmp_path), "rb").read()
    # disabled-config service: /route cannot run, but /outcome must still work
    cfg = tmp_path / "disabled.yaml"
    cfg.write_text("router:\n  enabled: false\n  threshold: 0.30\n")
    svc2 = Service(cfg, str(tmp_path / "telemetry"))
    try:
        assert svc2.wait_ready()
        code, body = _post_raw(svc2, "/outcome",
                               {"event_id": eid, "outcome": "aborted"})
        assert code == 202, (code, body)
    finally:
        svc2.stop()
    assert open(_dec_path(tmp_path), "rb").read() == before


def test_health_outcomes_counters_additive(service):
    h = service.get("/health")
    assert h["outcomes"] == {"logged": 0, "errors": 0}
    eid = service.post("/route", {"prompt": "health synthetic prompt", "session_id": "s", "message_id": "m"})["event_id"]
    _post_raw(service, "/outcome", {"event_id": eid, "outcome": "timeout"})
    h = service.get("/health")
    assert h["outcomes"] == {"logged": 1, "errors": 0}


# ---------------- edge_rejections per-shape counters ----------------

def _post_expect_400(svc, data):
    req = urllib.request.Request(
        f"http://127.0.0.1:{svc.port}/route", data=data,
        headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as ei:
        urllib.request.urlopen(req, timeout=60)
    assert ei.value.code == 400
    assert ei.value.read() == b'{"error": "empty or missing prompt"}'


def test_edge_rejection_counters_per_shape(service):
    for payload, shape in [
            ({}, "missing_prompt"),
            ({"prompt": ""}, "empty_prompt"),
            ({"prompt": "   \t "}, "whitespace_prompt"),
            ({"prompt": 42}, "non_string_prompt")]:
        _post_expect_400(service, json.dumps(payload).encode())
    h = service.get("/health")
    er = h["edge_rejections"]
    assert er["missing_prompt"] == 1 and er["empty_prompt"] == 1
    assert er["whitespace_prompt"] == 1 and er["non_string_prompt"] == 1
    assert er["malformed_json"] == 0


def test_edge_rejection_malformed_json_counter(service):
    _post_expect_400(service, b"{definitely not json")
    h = service.get("/health")
    assert h["edge_rejections"]["malformed_json"] == 1
    # /outcome 4xxs are request validity, NOT edge rejections
    eid = "a" * 32
    _post_raw(service, "/outcome", {"event_id": eid, "outcome": "success"})
    assert service.get("/health")["edge_rejections"]["malformed_json"] == 1


# ---------------- missing_ids_logged ----------------

def test_missing_ids_logged_pinned_at_zero_with_enforcement(service, tmp_path):
    """ERRATUM 1: /route requires both ids, so no logged decision can carry a
    null id hash — the invariant counter must stay pinned at 0."""
    service.post("/route", {"prompt": "enforced ids prompt",
                            "session_id": "s", "message_id": "m"})
    assert service.get("/health")["missing_ids_logged"] == 0
    # every logged row carries both hashes (null ids impossible by construction)
    recs, quar = read_decisions(_dec_path(tmp_path))
    assert quar == [] and recs
    assert all(r["session_id_hash"] and r["message_id_hash"] for r in recs)


# ---------------- decision schema bump 1.0.0 -> 1.1.0 ----------------

def test_new_events_lack_prompt_id_and_version_bumped(tmp_path):
    assert SCHEMA_VERSION == "1.1.0"
    tdir = str(tmp_path / "t")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.30\n")
    p = _run_cli("schema bump synthetic prompt", cfg, tdir)
    assert p.returncode == 0
    recs, quar = read_decisions(os.path.join(tdir, "decisions.jsonl"))
    assert quar == [] and len(recs) == 1
    assert "prompt_id" not in recs[0]
    assert recs[0]["schema_version"] == "1.1.0"


def test_legacy_row_with_prompt_id_still_validates():
    legacy = make_decision_event("legacy synthetic", confidence=0.5,
                                 chosen_action="weak")
    legacy["schema_version"] = "1.0.0"
    legacy["prompt_id"] = 0
    assert validate_decision(legacy) == legacy  # legacy rows accepted


def test_nonzero_prompt_id_rejected():
    d = make_decision_event("x", confidence=0.5, chosen_action="weak")
    assert "prompt_id" not in d
    d["prompt_id"] = 1  # only the legacy constant 0 is acceptable
    with pytest.raises(Exception):
        validate_decision(d)


def test_cli_response_still_carries_legacy_prompt_id(tmp_path):
    tdir = str(tmp_path / "t")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("router:\n  enabled: true\n  threshold: 0.30\n")
    p = _run_cli("response compat synthetic prompt", cfg, tdir)
    out = json.loads(p.stdout.strip().splitlines()[-1])
    assert out["prompt_id"] == 0  # response shape unchanged (CLI layer)


# ---------------- join tool ----------------

def _write_ledgers(tmp_path, decisions, outcomes):
    ddir = tmp_path / "t"
    ddir.mkdir(parents=True, exist_ok=True)
    (ddir / "decisions.jsonl").write_text(
        "".join(json.dumps(d, sort_keys=True) + "\n" for d in decisions))
    (ddir / "outcomes.jsonl").write_text(
        "".join(json.dumps(o, sort_keys=True) + "\n" for o in outcomes))


def _fixture_decisions():
    decs = []
    for i, (act, sid, mid) in enumerate([
            ("weak", None, None), ("strong", "s1", "m1"),
            ("weak", "s2", None), ("strong", None, "m3")]):
        decs.append(make_decision_event(f"fixture prompt {i}", confidence=0.5,
                                        chosen_action=act,
                                        session_id=sid, message_id=mid))
    return decs


def test_join_tool_self_test():
    p = subprocess.run([sys.executable, JOIN_TOOL, "--self-test"],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr


def test_join_tool_summary_on_fixtures(tmp_path):
    decs = _fixture_decisions()
    outs = []
    for i, d in enumerate(decs[:3]):
        outs.append({"schema_version": SCHEMA_VERSION,
                     "outcome_id": f"{i:032d}", "event_id": d["event_id"],
                     "outcome": ["success", "failure", "timeout"][i],
                     "cost": [0.01, None, 0.02][i],
                     "ts": f"2026-09-09T00:00:0{i}+00:00",
                     "joined_session_id_hash": d["session_id_hash"],
                     "joined_message_id_hash": d["message_id_hash"]})
    _write_ledgers(tmp_path, decs, outs)
    tdir = str(tmp_path / "t")
    p = subprocess.run([sys.executable, JOIN_TOOL,
                        "--decisions", os.path.join(tdir, "decisions.jsonl"),
                        "--outcomes", os.path.join(tdir, "outcomes.jsonl")],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    s = p.stdout
    assert "n_decisions: 4" in s and "n_outcomes: 3" in s
    assert "joined_outcomes: 3" in s
    assert "join_rate: 1.0" in s
    assert "orphan_outcomes: 0" in s
    assert "success" in s and "failure" in s and "timeout" in s
    # id hygiene: 2 of 4 decisions have null session_id_hash (0.50 > 0.20)
    assert "null_session_id_hash_frac: 0.50" in s
    assert "null_message_id_hash_frac: 0.50" in s
    assert "WARNING" in s


def test_join_tool_no_warning_below_threshold(tmp_path):
    decs = [make_decision_event("f1", confidence=0.5, chosen_action="weak",
                                session_id="a", message_id="b"),
            make_decision_event("f2", confidence=0.5, chosen_action="strong",
                                session_id="c", message_id="d")]
    outs = [{"schema_version": SCHEMA_VERSION, "outcome_id": "9" * 32,
             "event_id": decs[0]["event_id"], "outcome": "success",
             "ts": "2026-09-09T00:00:00+00:00",
             "joined_session_id_hash": decs[0]["session_id_hash"],
             "joined_message_id_hash": decs[0]["message_id_hash"]}]
    _write_ledgers(tmp_path, decs, outs)
    tdir = str(tmp_path / "t")
    p = subprocess.run([sys.executable, JOIN_TOOL,
                        "--decisions", os.path.join(tdir, "decisions.jsonl"),
                        "--outcomes", os.path.join(tdir, "outcomes.jsonl")],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "WARNING" not in p.stdout
    assert "join_rate: 1.0" in p.stdout


def test_join_tool_orphan_counted(tmp_path):
    decs = _fixture_decisions()[:1]
    ghost_eid = "b" * 32
    outs = [{"schema_version": SCHEMA_VERSION, "outcome_id": "8" * 32,
             "event_id": ghost_eid, "outcome": "failure",
             "ts": "2026-09-09T00:00:00+00:00",
             "joined_session_id_hash": None, "joined_message_id_hash": None}]
    _write_ledgers(tmp_path, decs, outs)
    tdir = str(tmp_path / "t")
    p = subprocess.run([sys.executable, JOIN_TOOL,
                        "--decisions", os.path.join(tdir, "decisions.jsonl"),
                        "--outcomes", os.path.join(tdir, "outcomes.jsonl")],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "orphan_outcomes: 1" in p.stdout
    assert "join_rate: 0.0" in p.stdout


# ---------------- /route id enforcement (ERRATUM 1) ----------------

_ID400 = {"error": "session_id and message_id are required"}


def _post_route_raw(svc, payload):
    return _post_raw(svc, "/route", payload)


def test_route_requires_both_ids(service, tmp_path):
    before = open(_dec_path(tmp_path), "rb").read() if \
        os.path.exists(_dec_path(tmp_path)) else b""
    h0 = service.get("/health")
    cases = [
        {"prompt": "no ids at all"},                                   # both missing
        {"prompt": "only session", "session_id": "s"},                 # message missing
        {"prompt": "only message", "message_id": "m"},                 # session missing
        {"prompt": "empty sid", "session_id": "", "message_id": "m"},  # empty session
        {"prompt": "empty mid", "session_id": "s", "message_id": ""},  # empty message
        {"prompt": "ws sid", "session_id": "  \t ", "message_id": "m"},
        {"prompt": "ws mid", "session_id": "s", "message_id": "   "},
        {"prompt": "null sid", "session_id": None, "message_id": "m"},
        {"prompt": "nonstr sid", "session_id": 123, "message_id": "m"},
        {"prompt": "nonstr mid", "session_id": "s", "message_id": 4.5},
    ]
    for payload in cases:
        code, body = _post_route_raw(service, payload)
        assert code == 400, (payload, code, body)
        assert body == _ID400, (payload, body)
    # NO ledger write on any of them
    after = open(_dec_path(tmp_path), "rb").read() if \
        os.path.exists(_dec_path(tmp_path)) else b""
    assert after == before
    # Counters (both-missing increments BOTH; independent checks):
    # sid bad in: both-missing(1), only-message(3), empty sid(4), ws sid(6),
    #             null sid(8), nonstr sid(9)          -> 6
    # mid bad in: both-missing(1), only-session(2), empty mid(5), ws mid(7),
    #             nonstr mid(10)                      -> 5
    er = service.get("/health")["edge_rejections"]
    assert er["missing_session_id"] == 6
    assert er["missing_message_id"] == 5
    # prompt-edge counters untouched by id enforcement
    assert er["empty_prompt"] == 0 and er["missing_prompt"] == 0
    # a fully valid call still routes and logs (protected paths reachable)
    out = service.post("/route", {"prompt": "valid after id 400s",
                                  "session_id": "s", "message_id": "m"})
    assert out["decision"] in ("weak", "strong")
    recs, quar = read_decisions(_dec_path(tmp_path))
    assert quar == [] and len(recs) == 1
