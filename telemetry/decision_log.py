"""Append-only decision logging for idea 101 (T031).

Best-effort by contract (constitution IV / plan Stage-1): a logging failure
MUST NOT break the routing call — it increments a visible error counter and
returns quietly. Storage: append-only JSONL, one record per line (frozen in
results/101/LIVE_PREREG.md section 1). A process-wide lock serializes
appends; single write() per line for atomicity on local filesystems.
"""
import json
import os
import threading
import time

from telemetry.schema import (SCHEMA_VERSION, SchemaValidationError,
                              new_event_id, validate_decision, utc_now_iso)

DEFAULT_LOG_DIR = os.path.join("evidence", "telemetry")
DECISIONS_FILENAME = "decisions.jsonl"


class LogWriteError(Exception):
    pass


class DecisionLogger:
    """Append-only decision-event writer with a visible error counter."""

    def __init__(self, log_dir=None, enabled=True):
        self.log_dir = os.path.abspath(log_dir or DEFAULT_LOG_DIR)
        self.path = os.path.join(self.log_dir, DECISIONS_FILENAME)
        self.enabled = enabled
        self._lock = threading.Lock()
        # Visible health counters (must be observable via health endpoint / report)
        self.counters = {"logged": 0, "errors": 0, "last_error": None}
        self._fh = None

    def _open(self):
        if self._fh is None:
            os.makedirs(self.log_dir, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        return self._fh

    def log_decision(self, record):
        """Validate + append one decision record. Best-effort: returns True on
        success, False on failure (error counter incremented, never raises
        out of the routing path)."""
        if not self.enabled:
            return False
        try:
            validate_decision(record)
            line = json.dumps(record, sort_keys=True, separators=(",", ":"))
            with self._lock:
                t0 = time.perf_counter()
                fh = self._open()
                fh.write(line + "\n")
                fh.flush()
                self.counters["logged"] += 1
                self.counters["last_log_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
            return True
        except Exception as e:  # noqa: BLE001 — best-effort by contract
            with self._lock:
                self.counters["errors"] += 1
                self.counters["last_error"] = f"{type(e).__name__}: {e}"
            return False

    def health(self):
        """Snapshot of visible counters for /health and tests (A11)."""
        with self._lock:
            return dict(self.counters)

    def close(self):
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.close()
                finally:
                    self._fh = None


class TeeDecisionLogger:
    """Fan a decision record out to multiple loggers (parity tests use this
    to prove CLI and service produce identical records)."""


def read_decisions(path, quarantine=None):
    """Read a decisions JSONL, discarding a trailing partial line and
    quarantining schema-invalid rows (corruption recovery, A7/A12).

    Returns (valid_records, quarantine_list). quarantine entries are
    {"line_no": n, "error": str, "raw": <line truncated to 400 chars>}.
    """
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
            validate_decision(rec)
            valid.append(rec)
        except Exception as e:  # noqa: BLE001 — quarantine, don't crash the reader
            if i == len(lines) and not _is_parseable(raw):
                bad.append({"line_no": i, "error": "trailing partial line discarded",
                            "raw": raw[:400]})
            else:
                bad.append({"line_no": i, "error": f"{type(e).__name__}: {e}",
                            "raw": raw[:400]})
    if quarantine is not None:
        quarantine.extend(bad)
    return valid, bad


def _is_parseable(raw):
    try:
        json.loads(raw)
        return True
    except Exception:
        return False


def new_id():
    """Re-export for callers that need an id without importing schema."""
    return new_event_id()


SCHEMA_V = SCHEMA_VERSION
