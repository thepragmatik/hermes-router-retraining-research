"""Telemetry schemas for idea 101 (frozen in results/101/LIVE_PREREG.md).

Both ledgers are schema_version "1.1.0" as of the outcome-capture schema bump (results/101/OUTCOME_CAPTURE_PREREG.md). Raw prompt text never enters any
record: the only content-derived field is `prompt_hash` = sha256(text)[:12].
"""
import hashlib
import re
import uuid
from datetime import datetime, timezone

SCHEMA_VERSION = "1.1.0"

DECISION_REQUIRED = (
    "schema_version", "event_id", "ts", "session_id_hash", "message_id_hash",
    "prompt_hash", "traffic_stratum", "router_id", "router_version",
    "representation_version", "policy_id", "policy_config_hash", "action_set",
    "chosen_action", "chosen_propensity", "action_probabilities", "scores",
    "model_provider_revision", "price_snapshot_id", "exploration_mode",
    "eligibility_reason",
)

OUTCOME_REQUIRED = (
    "schema_version", "outcome_id", "event_id", "outcome_ts", "outcome_type",
    "outcome_value", "outcome_scale", "provenance_class", "evaluator_id",
    "evaluator_version", "finality", "metadata",
)

PROVENANCE_CLASSES = (
    "task_native", "human_acceptance", "randomized_model_outcome",
    "benchmark", "judge", "synthetic", "unknown",
)

FINALITY_VALUES = ("provisional", "final", "superseded")

EXPLORATION_MODES = ("disabled", "shadow_dual", "randomized_sentinel")

HASH_LEN = 12  # truncated sha256 hex, per V1_BASELINE_GAPS fix direction

_HEX12_RE = re.compile(r"^[0-9a-f]{12}$")

PRICE_SNAPSHOT_ID = "historical-frozen-2026-09"
POLICY_ID = "v1-threshold-0.30"
ROUTER_ID = "router_v1"
ROUTER_VERSION = "router-v1-frozen"
REPRESENTATION_VERSION = "bge-small-en-v1.5"
ACTION_SET = ["weak", "strong"]

# Metadata whitelist for OutcomeEvent (plan: treat outcome metadata as
# potentially sensitive; whitelist fields). Controlled vocabulary only —
# no free text ("note" removed after T034 review: any text-bearing key is a
# PII surface; the fixtures module uses {"source","fixture"} vocabulary).
OUTCOME_METADATA_KEYS = ("source", "fixture")


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_event_id():
    return uuid.uuid4().hex


def sha12(text):
    """sha256 hex digest truncated to 12 chars — the content hash."""
    if not isinstance(text, str):
        text = str(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:HASH_LEN]


def is_hash12(s):
    return isinstance(s, str) and bool(_HEX12_RE.match(s))


class SchemaValidationError(ValueError):
    """Raised when a record violates the frozen schema (fail loud, T034/A7)."""


ACCEPTED_SCHEMA_VERSIONS = ("1.0.0", "1.1.0")


def _check_known(rec, required, kind):
    missing = [k for k in required if k not in rec]
    if missing:
        raise SchemaValidationError(
            f"{kind} missing required fields: {missing}")
    if rec.get("schema_version") not in ACCEPTED_SCHEMA_VERSIONS:
        raise SchemaValidationError(
            f"{kind} schema_version {rec.get('schema_version')!r} not in "
            f"{ACCEPTED_SCHEMA_VERSIONS} (drift must be quarantined, not accepted)")
    # Cleanup A (OUTCOME_CAPTURE_PREREG): prompt_id dropped from NEW events in
    # 1.1.0; legacy 1.0.0 rows carry the constant 0 and remain valid. Any other
    # value is corruption, never a real identity.
    if "prompt_id" in rec and rec["prompt_id"] != 0:
        raise SchemaValidationError(
            f"decision prompt_id must be the legacy constant 0 (deprecated; "
            f"identity = event_id), got {rec['prompt_id']!r}")


def validate_decision(rec):
    """Validate a decision record; raises SchemaValidationError (fail loud)."""
    _check_known(rec, DECISION_REQUIRED, "decision")
    if not is_hash12(rec["prompt_hash"]):
        raise SchemaValidationError(
            f"decision prompt_hash must be 12-hex sha256[:12], got {rec['prompt_hash']!r}")
    for k in ("session_id_hash", "message_id_hash"):
        v = rec[k]
        if v is not None and not is_hash12(v):
            raise SchemaValidationError(f"decision {k} must be null or 12-hex, got {v!r}")
    if rec["chosen_action"] not in ACTION_SET:
        raise SchemaValidationError(
            f"chosen_action {rec['chosen_action']!r} not in {ACTION_SET}")
    if list(rec["action_set"]) != ACTION_SET:
        raise SchemaValidationError(f"action_set drift: {rec['action_set']!r}")
    prop = rec["chosen_propensity"]
    if prop is not None:
        if not isinstance(prop, (int, float)) or not (0.0 < float(prop) <= 1.0):
            raise SchemaValidationError(
                f"chosen_propensity must be null (deterministic) or in (0,1], got {prop!r}")
    probs = rec["action_probabilities"]
    if probs is not None:
        if not isinstance(probs, dict) or sorted(probs) != sorted(ACTION_SET):
            raise SchemaValidationError(f"action_probabilities drift: {probs!r}")
        total = sum(float(v) for v in probs.values())
        if abs(total - 1.0) > 1e-6:
            raise SchemaValidationError(
                f"action_probabilities must sum to 1 (got {total!r})")
        if float(probs[rec["chosen_action"]]) <= 0:
            raise SchemaValidationError(
                "sampled action has zero probability in stored distribution")
    if rec["exploration_mode"] not in EXPLORATION_MODES:
        raise SchemaValidationError(
            f"exploration_mode {rec['exploration_mode']!r} not in {EXPLORATION_MODES}")
    if rec["exploration_mode"] in ("shadow_dual", "randomized_sentinel"):
        if prop is None or not (0.0 < float(prop) <= 1.0):
            raise SchemaValidationError(
                f"randomized event (mode {rec['exploration_mode']}) must carry a "
                "propensity in (0,1] — missing propensity is forbidden (FR-005)")
    return rec


def validate_outcome(rec):
    _check_known(rec, OUTCOME_REQUIRED, "outcome")
    if rec["provenance_class"] not in PROVENANCE_CLASSES:
        raise SchemaValidationError(
            f"provenance_class {rec['provenance_class']!r} not in "
            f"{PROVENANCE_CLASSES} (fidelity classes are closed)")
    if rec["finality"] not in FINALITY_VALUES:
        raise SchemaValidationError(f"finality {rec['finality']!r} invalid")
    val = rec["outcome_value"]
    if not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
        raise SchemaValidationError(
            f"outcome_value must be in [0,1], got {val!r}")
    extra = set(rec.get("metadata") or {}) - set(OUTCOME_METADATA_KEYS)
    if extra:
        raise SchemaValidationError(
            f"outcome metadata keys outside whitelist: {sorted(extra)}")
    return rec


# ---------- convenience constructors ----------

def make_decision_event(prompt, confidence, chosen_action, *, threshold=0.30,
                        session_id=None, message_id=None, traffic_stratum="unknown",
                        exploration_mode="disabled", chosen_propensity=None,
                        action_probabilities=None, eligibility_reason="not_eligible_no_exploration",
                        model_provider_revision=None, ts=None):
    """Build a decision record. `prompt` is used ONLY to derive the hash and is
    never stored. caller session/message ids are hashed and never stored."""
    if model_provider_revision is None:
        model_provider_revision = default_model_provider_revision()
    policy_cfg = {"policy_id": POLICY_ID, "threshold": threshold}
    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": new_event_id(),
        "ts": ts or utc_now_iso(),
        "session_id_hash": sha12(session_id) if session_id else None,
        "message_id_hash": sha12(message_id) if message_id else None,
        "prompt_hash": sha12(prompt),
        "traffic_stratum": traffic_stratum,
        "router_id": ROUTER_ID,
        "router_version": ROUTER_VERSION,
        "representation_version": REPRESENTATION_VERSION,
        "policy_id": POLICY_ID,
        "policy_config_hash": sha12(__import__("json").dumps(policy_cfg, sort_keys=True)),
        "action_set": list(ACTION_SET),
        "chosen_action": chosen_action,
        "chosen_propensity": chosen_propensity,
        "action_probabilities": action_probabilities,
        "scores": {"confidence": float(confidence), "threshold": float(threshold)},
        "model_provider_revision": model_provider_revision,
        "price_snapshot_id": PRICE_SNAPSHOT_ID,
        "exploration_mode": exploration_mode,
        "eligibility_reason": eligibility_reason,
        # prompt_id REMOVED in schema 1.1.0 (pre-approved cleanup A,
        # results/101/OUTCOME_CAPTURE_PREREG.md): new events no longer carry
        # it. Legacy 1.0.0 rows keep it and still validate. Old consumers
        # keying on prompt_id must move to prompt_hash / event_id.
    }


def default_model_provider_revision():
    """Frozen historical pair (LIVE_PREREG section 8). Never called."""
    return {
        "weak": {"model_id": "gpt-4o-mini-2024-07-18", "provider": "openai",
                 "revision": "2024-07-18"},
        "strong": {"model_id": "gpt-4o-2024-11-20", "provider": "openai",
                   "revision": "2024-11-20"},
    }


def make_outcome_event(event_id, outcome_value, *, provenance_class="synthetic",
                       outcome_type="routed_answer_correct", outcome_scale="binary_0_1",
                       evaluator_id="fixture", evaluator_version="1.0.0",
                       finality="final", metadata=None, outcome_ts=None,
                       supersedes_outcome_id=None):
    md = dict(metadata or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "outcome_id": new_event_id(),
        "event_id": event_id,
        "outcome_ts": outcome_ts or utc_now_iso(),
        "outcome_type": outcome_type,
        "outcome_value": float(outcome_value),
        "outcome_scale": outcome_scale,
        "provenance_class": provenance_class,
        "evaluator_id": evaluator_id,
        "evaluator_version": evaluator_version,
        "finality": finality,
        "metadata": md,
        "supersedes_outcome_id": supersedes_outcome_id,
    }
