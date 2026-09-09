import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry import fixtures, join as join_mod, report as report_mod  # noqa: E402
from telemetry.decision_log import DecisionLogger, read_decisions  # noqa: E402
from telemetry.outcome_log import OutcomeWriter, read_outcomes  # noqa: E402
from telemetry.schema import (SchemaValidationError, make_decision_event,  # noqa: E402
                              make_outcome_event, sha12, validate_decision,
                              validate_outcome)


# ---------- schema validation (T010-adjacent invariants, A7) ----------

def test_decision_roundtrip(tmp_path):
    d = make_decision_event("hello world", confidence=0.55, chosen_action="weak")
    validate_decision(d)


def test_missing_required_field_fails(tmp_path):
    d = make_decision_event("x", confidence=0.5, chosen_action="weak")
    del d["policy_id"]
    with pytest.raises(SchemaValidationError):
        validate_decision(d)


def test_schema_version_drift_fails():
    d = make_decision_event("x", confidence=0.5, chosen_action="weak")
    d["schema_version"] = "0.9.0"
    with pytest.raises(SchemaValidationError):
        validate_decision(d)


def test_randomized_event_without_propensity_fails():
    d = make_decision_event("x", confidence=0.5, chosen_action="weak",
                            exploration_mode="randomized_sentinel")
    with pytest.raises(SchemaValidationError):
        validate_decision(d)  # FR-005: missing propensity on randomized event is forbidden


def test_zero_propensity_sampled_action_fails():
    d = make_decision_event("x", confidence=0.5, chosen_action="strong",
                            exploration_mode="randomized_sentinel",
                            chosen_propensity=0.0)
    with pytest.raises(SchemaValidationError):
        validate_decision(d)


def test_probability_sum_drift_fails():
    d = make_decision_event("x", confidence=0.5, chosen_action="strong",
                            exploration_mode="randomized_sentinel",
                            chosen_propensity=0.9, action_probabilities={"weak": 0.2, "strong": 0.9})
    with pytest.raises(SchemaValidationError):
        validate_decision(d)


def test_prompt_hash_is_sha12_and_stable():
    assert sha12("abc") == sha12("abc")
    assert sha12("abc") != sha12("abd")
    assert len(sha12("abc")) == 12


def test_duplicate_prompts_share_prompt_hash():
    a = make_decision_event("same prompt", confidence=0.5, chosen_action="weak")
    b = make_decision_event("same prompt", confidence=0.5, chosen_action="weak")
    assert a["prompt_hash"] == b["prompt_hash"]
    assert a["event_id"] != b["event_id"]


# ---------- logger best-effort contract (A11-adjacent) ----------

def test_logger_io_failure_never_raises(tmp_path):
    # log_dir is a FILE, not a directory -> open() raises OSError inside
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir")
    lg = DecisionLogger(log_dir=str(blocker))
    d = make_decision_event("x", confidence=0.5, chosen_action="weak")
    assert lg.log_decision(d) is False
    assert lg.health()["errors"] == 1
    assert lg.health()["logged"] == 0


def test_logger_disabled(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path), enabled=False)
    d = make_decision_event("x", confidence=0.5, chosen_action="weak")
    assert lg.log_decision(d) is False
    assert lg.health()["logged"] == 0
    assert not os.path.exists(lg.path)


def test_logger_append_roundtrip(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    for i in range(3):
        d = make_decision_event(f"p{i}", confidence=0.5, chosen_action="weak")
        assert lg.log_decision(d) is True
    recs, quar = read_decisions(lg.path)
    assert len(recs) == 3 and quar == []
    lg.close()


def test_trailing_partial_line_discarded(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    d = make_decision_event("ok", confidence=0.5, chosen_action="weak")
    lg.log_decision(d)
    lg.close()
    with open(lg.path, "a") as f:
        f.write('{"schema_version": "1.0.0", "event_id": "part')  # crash mid-write
    recs, quar = read_decisions(lg.path)
    assert len(recs) == 1
    assert quar and "partial" in quar[0]["error"]


def test_corrupt_row_quarantined_not_accepted(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    lg.log_decision(make_decision_event("good", confidence=0.5, chosen_action="weak"))
    lg.close()
    with open(lg.path, "a") as f:
        f.write(json.dumps({"schema_version": "1.0.0", "bogus": True}) + "\n")
    recs, quar = read_decisions(lg.path)
    assert len(recs) == 1 and len(quar) == 1
    assert "missing required" in quar[0]["error"] or "missing" in quar[0]["error"]


def test_restart_appends_without_clobber(tmp_path, capsys):
    # A12: new process appends to the same JSONL; prior rows survive.
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from telemetry.decision_log import DecisionLogger\n"
        "from telemetry.schema import make_decision_event\n"
        "lg = DecisionLogger(log_dir=%r)\n"
        "lg.log_decision(make_decision_event('restart-prompt', confidence=0.5, chosen_action='weak'))\n"
        "lg.close()\n"
    ) % (REPO, str(tmp_path))
    for _ in range(2):
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)
    recs, _ = read_decisions(lg.path if False else str(tmp_path / "decisions.jsonl"))
    assert len(recs) == 2
    assert len({r["event_id"] for r in recs}) == 2


# ---------- edge fixtures (T033, A1-A4) ----------

def test_duplicate_outcomes_collapse():
    d = fixtures.base_decision()
    outs = fixtures.duplicate_outcomes(d)
    ji, rows = join_mod.reconcile([d], outs)
    # Two live finals with no supersedes link = ambiguous by frozen semantics;
    # surfaced, never silently joined.
    assert ji[d["event_id"]]["status"] == "ambiguous"


def test_true_double_append_of_same_row_joined():
    """Same outcome content, later ts, explicit supersedes link: collapses to
    one join (the newest final), the referenced earlier row is dead."""
    d = fixtures.base_decision()
    o1 = fixtures.make_outcome_event(d["event_id"], 1.0, finality="final",
                                     metadata={"source": "fixture", "fixture": "dup"})
    o2 = fixtures.make_outcome_event(d["event_id"], 1.0, finality="final",
                                     supersedes_outcome_id=o1["outcome_id"],
                                     metadata={"source": "fixture", "fixture": "dup"})
    ji, _ = join_mod.reconcile([d], [o1, o2])
    assert ji[d["event_id"]]["status"] == "joined"
    assert ji[d["event_id"]]["outcome"]["outcome_id"] == o2["outcome_id"]


def test_late_outcome_resolves_to_final():
    d = fixtures.base_decision()
    outs = fixtures.late_outcomes(d)
    ji, rows = join_mod.reconcile([d], outs)
    assert ji[d["event_id"]]["status"] == "joined"
    assert ji[d["event_id"]]["outcome"]["finality"] == "final"
    assert ji[d["event_id"]]["outcome"]["outcome_value"] == 1.0


def test_provisional_superseded_by_final():
    d = fixtures.base_decision()
    outs = fixtures.provisional_then_final(d)
    ji, _ = join_mod.reconcile([d], outs)
    assert ji[d["event_id"]]["status"] == "joined"
    assert ji[d["event_id"]]["outcome"]["outcome_value"] == 1.0


def test_contradictory_finals_flagged_ambiguous():
    d = fixtures.base_decision()
    outs = fixtures.contradictory_outcomes(d)
    ji, rows = join_mod.reconcile([d], outs)
    assert ji[d["event_id"]]["status"] == "ambiguous"
    assert any(r["status"] == "ambiguous" for r in rows)


def test_superseded_chain_resolves_newest_final():
    d = fixtures.base_decision()
    outs = fixtures.superseded_chain(d)
    ji, _ = join_mod.reconcile([d], outs)
    assert ji[d["event_id"]]["status"] == "joined"
    assert ji[d["event_id"]]["outcome"]["outcome_value"] == 1.0


def test_unjoined_decision_and_orphan_outcome():
    d = fixtures.base_decision()
    ji, rows = join_mod.reconcile([d], [])
    assert ji[d["event_id"]]["status"] == "unjoined"
    o = make_outcome_event("nonexistent-event", 1.0)
    ji2, _ = join_mod.reconcile([d], [o])
    assert ji2["nonexistent-event"]["status"] == "orphan"


def test_outcome_metadata_whitelist_enforced():
    with pytest.raises(SchemaValidationError):
        validate_outcome(make_outcome_event("e", 1.0, metadata={"free_text": "user said things"}))
    with pytest.raises(SchemaValidationError):
        validate_outcome(make_outcome_event("e", 1.0, metadata={"note": "text-bearing key"}))


# ---------- T034: raw-prompt leakage + repo grep PII over fixture logs ----------

def test_no_prompt_text_in_decision_ledger(tmp_path):
    """A5: prompts (with distinctive markers) must never appear in any ledger."""
    lg = DecisionLogger(log_dir=str(tmp_path))
    ow = OutcomeWriter(log_dir=str(tmp_path))
    secret_prompt = "PII-MARKER-alpha secret user text 12345"
    d = make_decision_event(secret_prompt, confidence=0.5, chosen_action="weak")
    assert lg.log_decision(d) is True
    # metadata is controlled vocabulary only — no free text enters outcomes
    o = make_outcome_event(d["event_id"], 1.0, metadata={"source": "fixture", "fixture": "pii"})
    assert ow.log_outcome(o) is True
    lg.close()
    ow.close()
    for fname in ("decisions.jsonl", "outcomes.jsonl"):
        raw = (tmp_path / fname).read_text()
        assert "PII-MARKER-alpha" not in raw
        assert "secret user text" not in raw
        assert "12345" not in raw.replace('"prompt_hash"', "")  # no text echo anywhere


def test_session_message_hashes_not_raw(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    d = make_decision_event("x", confidence=0.5, chosen_action="weak",
                            session_id="raw-session-PII-MARKER",
                            message_id="raw-message-PII-MARKER")
    lg.log_decision(d)
    lg.close()
    raw = (tmp_path / "decisions.jsonl").read_text()
    assert "raw-session-PII-MARKER" not in raw
    assert "raw-message-PII-MARKER" not in raw
    recs, _ = read_decisions(lg.path)
    assert recs[0]["session_id_hash"] == sha12("raw-session-PII-MARKER")
    assert recs[0]["message_id_hash"] == sha12("raw-message-PII-MARKER")


def test_report_prompt_text_scan_zero_hits(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    d = make_decision_event("PII-MARKER-gamma body", confidence=0.5, chosen_action="weak")
    lg.log_decision(d)
    lg.close()
    rep = report_mod.build_quality_report(str(tmp_path))
    assert rep["prompt_text_hits"] == []


def test_report_prompt_text_scan_flags_actual_leak(tmp_path):
    """If a prompt-TEXT key ever landed in a ledger, the scan must flag it."""
    lg = DecisionLogger(log_dir=str(tmp_path))
    lg.log_decision(make_decision_event("ok", confidence=0.5, chosen_action="weak"))
    lg.close()
    with open(lg.path, "a") as f:
        f.write(json.dumps({"leak": True, "prompt": "PII-MARKER-delta"}) + "\n")
    rep = report_mod.build_quality_report(str(tmp_path))
    assert rep["prompt_text_hits"], "scan missed an actual prompt-text key"


# ---------- T035: quality report dimensions ----------

def test_quality_report_unique_ids_and_provenance(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    d1 = make_decision_event("alpha", confidence=0.5, chosen_action="weak")
    d2 = make_decision_event("bravo", confidence=0.5, chosen_action="weak")
    lg.log_decision(d1)
    lg.log_decision(d2)
    # same event appended twice via DIRECT file append (bypasses logger
    # validation) -> duplicate id counted; drift row -> quarantined
    lg.close()
    dup = dict(d1)
    with open(lg.path, "a") as f:
        f.write(json.dumps(dup, sort_keys=True) + "\n")
        f.write(json.dumps({"schema_version": "1.0.0"}) + "\n")
    ow = OutcomeWriter(log_dir=str(tmp_path))
    ow.log_outcome(make_outcome_event(d1["event_id"], 1.0))
    ow.close()
    rep = report_mod.build_quality_report(str(tmp_path))
    assert rep["total_decisions"] == 3
    assert rep["unique_event_ids"] == 2
    assert rep["duplicate_ids"] == 1
    assert rep["missing_provenance"] == 0  # drift row is quarantined, not valid
    assert rep["schema_drift_quarantined"]["decisions"] == 1
    assert rep["joined"] == 1
    assert rep["join_success_rate"] == pytest.approx(1 / 3)


def test_join_stats_shape():
    st = join_mod.join_stats([{"event_id": "a", "status": "joined"},
                              {"event_id": "b", "status": "unjoined"}])
    assert st == {"total_decisions": 2, "joined": 1, "unjoined": 1,
                  "ambiguous": 0, "orphans": 0}
