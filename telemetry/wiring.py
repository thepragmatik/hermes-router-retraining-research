"""Shared decision-logging client for both routing paths (T040/T041).

ONE logger construction path for router_v1_cli.py and router_shadow.py —
service-side logging parity (closes G2) comes from both importing this module.
Environment overrides:
  ROUTER_TELEMETRY_DIR  — ledger directory (default evidence/telemetry)
  ROUTER_TELEMETRY_DISABLE — any non-empty value disables logging entirely
Legacy log (evidence/shadow/shadow_log.jsonl) is untouched; the new ledgers
are evidence/telemetry/decisions.jsonl + outcomes.jsonl (LIVE_PREREG section 1).
"""
import os

from telemetry.decision_log import DecisionLogger
from telemetry.schema import make_decision_event

# Module-level shared logger per process (service threads share it; the
# DecisionLogger is lock-protected). Never bound to port logic.
_shared = None


def telemetry_dir():
    d = os.environ.get("ROUTER_TELEMETRY_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "evidence", "telemetry")
    return d


def logging_enabled():
    return not os.environ.get("ROUTER_TELEMETRY_DISABLE")


def get_logger():
    global _shared
    if _shared is None:
        _shared = DecisionLogger(log_dir=telemetry_dir(),
                                 enabled=logging_enabled())
    return _shared


def reset_logger():
    """Test isolation hook: drop the shared instance (tests set env first)."""
    global _shared
    if _shared is not None:
        _shared.close()
    _shared = None


def record_route_decision(*, prompt, decision, confidence, threshold,
                          session_id=None, message_id=None,
                          traffic_stratum="unknown",
                          exploration_mode="disabled",
                          chosen_propensity=None,
                          action_probabilities=None,
                          eligibility_reason="not_eligible_no_exploration",
                          model_provider_revision=None):
    """Build + append the decision event for one route. Best-effort: returns
    the event dict on success, None on failure; NEVER raises into the route
    path (A11 contract)."""
    event = make_decision_event(
        prompt, confidence=confidence, chosen_action=decision,
        threshold=threshold, session_id=session_id, message_id=message_id,
        traffic_stratum=traffic_stratum, exploration_mode=exploration_mode,
        chosen_propensity=chosen_propensity,
        action_probabilities=action_probabilities,
        eligibility_reason=eligibility_reason,
        model_provider_revision=model_provider_revision)
    ok = get_logger().log_decision(event)
    return event if ok else None
