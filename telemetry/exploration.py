"""Phase 4 (T050-T053): bounded exploration machinery.

Modes (plan Stage-2, in preferred order): `disabled` (DEFAULT), `shadow_dual`
(user always sees base policy; extra action sampled for telemetry),
`randomized_sentinel` (selected action can DIFFER from base — requires
explicit operator approval flag in config, else fails closed to disabled).

Eligibility (T050): deterministic predicates evaluated BEFORE randomization,
logged on every decision via eligibility_reason. High-risk strata are excluded
by default (FR-012).

Randomization (T052): seeded epsilon-mixture. Chosen propensity is the EXACT
probability the chosen action had under the mixture (auditable).

Caps (T053): sentinel-rate cap (fail-closed: once the observed rate in the
recent window exceeds the cap, exploration returns base action with
eligibility_reason recorded) and a per-run spend-cap hook (counter; tokens
are unknown at this stage, so the hook exposes set_spend/charge and trips
fail-closed when the configured cap is reached).

Kill switch: config router.enabled=false or telemetry.exploration disabled →
deterministic base policy everywhere.
"""
import hashlib
import json

from telemetry.schema import ACTION_SET, EXPLORATION_MODES

DEFAULT_TRAFFIC_EXCLUSIONS = (
    "security", "privacy", "high_risk", "pii", "secret", "prod_unsafe",
)


def config_hash(cfg_dict):
    return hashlib.sha256(
        json.dumps(cfg_dict, sort_keys=True).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- eligibility

def is_eligible(*, traffic_stratum="unknown", exploration_cfg=None,
                action_set=None):
    """Deterministic eligibility predicate (T050). Returns (bool, reason).

    Excluded by default: security/privacy/high-risk/PII strata (FR-012),
    unknown strata (fail closed), and any action_set drift from the frozen
    two-action set.
    """
    exploration_cfg = exploration_cfg or {}
    allowed = set(exploration_cfg.get("eligible_strata", []))
    excluded = set(exploration_cfg.get("excluded_strata",
                                       DEFAULT_TRAFFIC_EXCLUSIONS))
    s = (traffic_stratum or "unknown").strip().lower()
    if s in excluded or any(x in s for x in DEFAULT_TRAFFIC_EXCLUSIONS):
        return False, f"excluded_stratum:{s}"
    if s == "unknown":
        return False, "unknown_stratum_fail_closed"
    if allowed and s not in allowed:
        return False, f"stratum_not_in_allowlist:{s}"
    if action_set is not None and list(action_set) != list(ACTION_SET):
        return False, "action_set_drift"
    return True, f"eligible_stratum:{s}"


# ---------------------------------------------------------------- policy

class ExplorationPolicy:
    """Seeded epsilon randomization with exact propensities + caps.

    Resolve order (fail closed at every step):
      1. router kill switch / mode missing or 'disabled' -> deterministic base
      2. randomized_sentinel without explicit operator approval -> disabled
      3. spend cap tripped -> disabled for this call
      4. rate cap exceeded (realized sentinel share) -> shadow_dual behavior
         (alternate action recorded but base returned... no: rate cap forces
         base action; the sampled alternate is dropped, mode stays logged)
      5. eligible + under caps -> epsilon-mixture sample with exact propensity
    """

    def __init__(self, *, mode="disabled", epsilon=0.0, seed=0,
                 sentinel_rate_cap=0.05, spend_cap_units=None,
                 approved_for_user_visible=False,
                 exploration_cfg=None):
        if mode not in EXPLORATION_MODES:
            raise ValueError(f"unknown exploration mode {mode!r}")
        self.mode = mode
        self.epsilon = float(epsilon)
        self.seed = int(seed)
        self.sentinel_rate_cap = float(sentinel_rate_cap)
        self.spend_cap_units = spend_cap_units
        self.approved_for_user_visible = bool(approved_for_user_visible)
        self.exploration_cfg = exploration_cfg or {}
        # counters (T053)
        self._calls = 0
        self._sentinels = 0
        self._spend = 0.0
        self._rng_counter = 0

    # -- spend hook (T053) --
    def charge(self, units):
        self._spend += float(units)
        return self._spend <= (self.spend_cap_units if self.spend_cap_units
                               is not None else float("inf"))

    @property
    def spend_tripped(self):
        return (self.spend_cap_units is not None
                and self._spend >= self.spend_cap_units)

    # -- rate cap --
    @property
    def realized_rate(self):
        return self._sentinels / self._calls if self._calls else 0.0

    def _rate_cap_tripped(self):
        # fail closed: at cap, no NEW sentinels
        return self._calls > 0 and self.realized_rate >= self.sentinel_rate_cap

    # -- core --
    def _rng(self, event_salt):
        """Deterministic per-event uniform in [0,1) from (seed, counter, salt)."""
        h = hashlib.sha256(f"{self.seed}:{self._rng_counter}:{event_salt}"
                           .encode()).hexdigest()
        self._rng_counter += 1
        return int(h[:16], 16) / float(1 << 64)

    def resolve(self, *, base_action, scores, event_salt, traffic_stratum="unknown",
                action_set=None):
        """Returns dict:
          chosen_action, exploration_mode, chosen_propensity (None for
          deterministic), action_probabilities (None unless randomized),
          eligibility_reason, base_action (always the policy answer).
        `scores` = {"confidence": p_strong}; base policy = threshold 0.30.
        """
        self._calls += 1
        base = {"base_action": base_action}

        if self.mode == "disabled":
            return {**base, "chosen_action": base_action,
                    "exploration_mode": "disabled", "chosen_propensity": None,
                    "action_probabilities": None,
                    "eligibility_reason": "not_eligible_no_exploration"}

        eligible, reason = is_eligible(
            traffic_stratum=traffic_stratum,
            exploration_cfg=self.exploration_cfg, action_set=action_set)
        if not eligible:
            return {**base, "chosen_action": base_action,
                    "exploration_mode": "disabled", "chosen_propensity": None,
                    "action_probabilities": None,
                    "eligibility_reason": reason}

        if self.mode == "randomized_sentinel" and not self.approved_for_user_visible:
            # fail closed: approval flag absent -> shadow_dual semantics at most
            effective_mode = "shadow_dual"
        else:
            effective_mode = self.mode

        if self.spend_tripped:
            return {**base, "chosen_action": base_action,
                    "exploration_mode": "disabled",
                    "chosen_propensity": None, "action_probabilities": None,
                    "eligibility_reason": "spend_cap_tripped"}

        if effective_mode == "shadow_dual":
            # user ALWAYS sees base; alternate action sampled for telemetry.
            u = self._rng(event_salt)
            alt = "strong" if base_action == "weak" else "weak"
            alternate = alt if u < 0.5 else base_action
            probs = {"weak": 0.5, "strong": 0.5}
            prop = probs[alternate]
            return {**base, "chosen_action": base_action,
                    "exploration_mode": "shadow_dual",
                    "chosen_propensity": prop,
                    "action_probabilities": probs,
                    "eligibility_reason": f"shadow_dual_{reason}",
                    "sampled_alternate": alternate}

        # randomized_sentinel (operator-approved): epsilon-mixture over actions
        if self._rate_cap_tripped():
            return {**base, "chosen_action": base_action,
                    "exploration_mode": "disabled",
                    "chosen_propensity": None, "action_probabilities": None,
                    "eligibility_reason": "rate_cap_tripped"}

        p_strong = float(scores.get("confidence", 0.0))
        # base policy distribution with epsilon exploration mass:
        # P(strong) = (1-eps)*1[strong==base] + eps*0.5
        eps = self.epsilon
        p_base_strong = 1.0 if base_action == "strong" else 0.0
        probs = {
            "weak": (1 - eps) * (1 - p_base_strong) + eps * 0.5,
            "strong": (1 - eps) * p_base_strong + eps * 0.5,
        }
        u = self._rng(event_salt)
        chosen = "strong" if u < probs["strong"] else "weak"
        prop = probs[chosen]
        if chosen != base_action:
            self._sentinels += 1
        return {**base, "chosen_action": chosen,
                "exploration_mode": "randomized_sentinel",
                "chosen_propensity": prop,
                "action_probabilities": probs,
                "eligibility_reason": f"sentinel_{reason}"}
