"""Append-only outcome writer + reading (T032, part 1).

OutcomeEvent rows join to decisions by event_id with exactly-one semantics;
reconciliation lives in join.py. Same storage discipline as decision_log.
"""
import json
import os
import threading

from telemetry.schema import validate_outcome

DEFAULT_LOG_DIR = os.path.join("evidence", "telemetry")
OUTCOMES_FILENAME = "outcomes.jsonl"


class OutcomeWriter:
    """Append-only outcome-event writer with visible error counters."""

    def __init__(self, log_dir=None, enabled=True):
        self.log_dir = os.path.abspath(log_dir or DEFAULT_LOG_DIR)
        self.path = os.path.join(self.log_dir, OUTCOMES_FILENAME)
        self.enabled = enabled
        self._lock = threading.Lock()
        self.counters = {"logged": 0, "errors": 0, "last_error": None}
        self._fh = None

    def log_outcome(self, record):
        """Validate + append one outcome record. Best-effort, never raises."""
        if not self.enabled:
            return False
        try:
            validate_outcome(record)
            line = json.dumps(record, sort_keys=True, separators=(",", ":"))
            with self._lock:
                fh = self._open()
                fh.write(line + "\n")
                fh.flush()
                self.counters["logged"] += 1
            return True
        except Exception as e:  # noqa: BLE001
            with self._lock:
                self.counters["errors"] += 1
                self.counters["last_error"] = f"{type(e).__name__}: {e}"
            return False

    def health(self):
        with self._lock:
            return dict(self.counters)

    def _open(self):
        if self._fh is None:
            os.makedirs(self.log_dir, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        return self._fh

    def close(self):
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.close()
                finally:
                    self._fh = None


def read_outcomes(path, quarantine=None):
    """Read outcomes JSONL with the same corruption recovery as decisions."""
    valid, bad = [], []
    if not os.path.exists(path):
        return valid, bad
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            rec = json.loads(raw)
            validate_outcome(rec)
            valid.append(rec)
        except Exception as e:  # noqa: BLE001
            bad.append({"line_no": i, "error": f"{type(e).__name__}: {e}",
                        "raw": raw[:400]})
    if quarantine is not None:
        quarantine.extend(bad)
    return valid, bad
