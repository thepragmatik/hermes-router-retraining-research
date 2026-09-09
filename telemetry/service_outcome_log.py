"""Append-only service-outcome writer for POST /outcome (101 outcome capture).

Frozen in results/101/OUTCOME_CAPTURE_PREREG.md. Distinct from the
LIVE_PREREG synthetic OutcomeEvent writer (telemetry/outcome_log.py): this
module writes the service-facing outcome rows appended by POST /outcome.

Storage: append-only JSONL at evidence/telemetry/outcomes.jsonl (local-only,
gitignored via the existing evidence/telemetry/*.jsonl rule). One row per
line; a process-wide lock serializes appends; a single write() + flush() +
os.fsync() per line so an OS-level crash cannot leave a torn row beyond the
usual trailing-partial-line recovery read_decisions-style readers already
apply. Read path tolerates a trailing partial line (crash-safety rationale:
fsync makes the last COMPLETE line durable; a torn tail is discarded on read,
never silently parsed).
"""
import json
import os
import threading

from telemetry.schema import SCHEMA_VERSION, utc_now_iso, new_event_id

DEFAULT_LOG_DIR = os.path.join("evidence", "telemetry")
SERVICE_OUTCOMES_FILENAME = "outcomes.jsonl"

OUTCOME_VOCABULARY = ("success", "failure", "timeout", "aborted")

_HEX_RE = None  # compiled lazily


def _hex_ok(s):
    global _HEX_RE
    if _HEX_RE is None:
        import re
        _HEX_RE = re.compile(r"^[0-9a-f]+$")
    return bool(_HEX_RE.match(s))


class OutcomeRequestError(ValueError):
    """Raised for request-validity problems; carries the frozen HTTP code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def validate_outcome_request(payload):
    """Validate a POST /outcome payload against the frozen contract.

    Returns (event_id, outcome, cost, latency_ms, note). Raises
    OutcomeRequestError with the frozen (code, message) on any violation.
    Validation precedes any state change: nothing is touched on failure.
    """
    if not isinstance(payload, dict):
        raise OutcomeRequestError(400, "malformed json")
    eid = payload.get("event_id")
    if not isinstance(eid, str) or not eid:
        raise OutcomeRequestError(400, "invalid event_id")
    eid = eid.strip().lower()
    if not eid or not _hex_ok(eid):
        raise OutcomeRequestError(400, "invalid event_id")
    if len(eid) > 32:
        raise OutcomeRequestError(400, "invalid event_id")
    outcome = payload.get("outcome")
    if outcome not in OUTCOME_VOCABULARY:
        raise OutcomeRequestError(400, "invalid outcome")
    cost = payload.get("cost")
    if cost is not None:
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) \
                or not cost > 0:
            raise OutcomeRequestError(400, "invalid cost")
    latency = payload.get("latency_ms")
    if latency is not None:
        if isinstance(latency, bool) or not isinstance(latency, int) \
                or latency <= 0:
            raise OutcomeRequestError(400, "invalid latency_ms")
    note = payload.get("note")
    if note is not None:
        if not isinstance(note, str) or len(note) > 200:
            raise OutcomeRequestError(400, "invalid note")
    return eid, outcome, cost, latency, note


def load_decisions_index(decisions_path):
    """Read decision events (both schema versions tolerated; corrupt lines
    skipped) -> {event_id: record}. Read-only."""
    index = {}
    if not os.path.exists(decisions_path):
        return index
    with open(decisions_path, "r", encoding="utf-8") as f:
        for raw in f.read().splitlines():
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                continue  # torn trailing line / corrupt row: skip, don't crash
            eid = rec.get("event_id")
            if isinstance(eid, str):
                index[eid] = rec
    return index


class ServiceOutcomeWriter:
    """Append-only writer with counters + duplicate detection."""

    def __init__(self, log_dir=None, enabled=True):
        self.log_dir = os.path.abspath(log_dir or DEFAULT_LOG_DIR)
        self.path = os.path.join(self.log_dir, SERVICE_OUTCOMES_FILENAME)
        self.enabled = enabled
        self._lock = threading.Lock()
        self.counters = {"logged": 0, "errors": 0, "last_error": None}
        self._fh = None

    def _open(self):
        if self._fh is None:
            os.makedirs(self.log_dir, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        return self._fh

    def load_existing_pairs(self):
        """(event_id, outcome) pairs already recorded (for duplicate 409)."""
        pairs = set()
        if not os.path.exists(self.path):
            return pairs
        with open(self.path, "r", encoding="utf-8") as f:
            for raw in f.read().splitlines():
                if not raw.strip():
                    continue
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    pairs.add((rec.get("event_id"), rec.get("outcome")))
        return pairs

    def append(self, *, event_id, outcome, cost=None, latency_ms=None,
               note=None, joined_session_id_hash=None,
               joined_message_id_hash=None):
        """Build + append one service-outcome row. Returns the row dict on
        success, None on write failure (errors counter incremented)."""
        row = {
            "schema_version": SCHEMA_VERSION,
            "outcome_id": new_event_id(),
            "event_id": event_id,
            "outcome": outcome,
            "ts": utc_now_iso(),
            "joined_session_id_hash": joined_session_id_hash,
            "joined_message_id_hash": joined_message_id_hash,
        }
        if cost is not None:
            row["cost"] = cost
        if latency_ms is not None:
            row["latency_ms"] = latency_ms
        if note is not None:
            row["note"] = note
        if not self.enabled:
            return None
        try:
            line = json.dumps(row, sort_keys=True, separators=(",", ":"))
            with self._lock:
                fh = self._open()
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())  # durable single line before 202
                self.counters["logged"] += 1
            return row
        except Exception as e:  # noqa: BLE001 — 5xx path, never crash thread
            with self._lock:
                self.counters["errors"] += 1
                self.counters["last_error"] = f"{type(e).__name__}: {e}"
            return None

    def health(self):
        with self._lock:
            return {"logged": self.counters["logged"],
                    "errors": self.counters["errors"]}

    def close(self):
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.close()
                finally:
                    self._fh = None
