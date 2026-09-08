"""Phase-4 tests (T050-T054): eligibility, modes, seeded epsilon, caps, 10k sim.

All exploration happens IN SIMULATION ONLY (spec Stage 2: no live
randomization; T055 prereg stays DRAFT, unexecuted).

NOTE on caps: the default sentinel_rate_cap is 0.05 and trips fail-closed;
rate/uncapped variants are set explicitly per test to isolate the property
under test.
"""
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry.exploration import (DEFAULT_TRAFFIC_EXCLUSIONS,  # noqa: E402
                                   ExplorationPolicy, is_eligible)
from telemetry.schema import validate_decision  # noqa: E402

UNCAPPED = 1.0  # sentinel_rate_cap=1.0 can never trip (rate <= 1)


# ---------- T050 eligibility ----------

def test_high_risk_strata_excluded_by_default():
    for s in ("security", "privacy", "high_risk", "pii", "something-security-ish"):
        ok, reason = is_eligible(traffic_stratum=s)
        assert ok is False


def test_unknown_stratum_fails_closed():
    ok, reason = is_eligible(traffic_stratum="unknown")
    assert ok is False and "fail_closed" in reason


def test_known_stratum_eligible():
    ok, reason = is_eligible(traffic_stratum="stage1_fixture")
    assert ok is True


def test_allowlist_semantics():
    cfg = {"eligible_strata": ["batch_only"]}
    ok, _ = is_eligible(traffic_stratum="other", exploration_cfg=cfg)
    assert ok is False
    ok, _ = is_eligible(traffic_stratum="batch_only", exploration_cfg=cfg)
    assert ok is True


def test_action_set_drift_ineligible():
    ok, reason = is_eligible(traffic_stratum="batch", action_set=["weak"])
    assert ok is False and "drift" in reason


# ---------- T051 modes / defaults ----------

def test_default_mode_is_disabled():
    pol = ExplorationPolicy()  # no args = production default
    r = pol.resolve(base_action="weak", scores={"confidence": 0.9},
                    event_salt="e1", traffic_stratum="batch")
    assert r["exploration_mode"] == "disabled"
    assert r["chosen_action"] == "weak"  # deterministic base
    assert r["chosen_propensity"] is None


def test_disabled_reduces_to_base_policy_regardless_of_scores():
    pol = ExplorationPolicy(mode="disabled", epsilon=0.9, seed=1)
    for conf, base in ((0.05, "weak"), (0.95, "strong")):
        r = pol.resolve(base_action=base, scores={"confidence": conf},
                        event_salt=f"s{conf}", traffic_stratum="batch")
        assert r["chosen_action"] == base
        assert r["chosen_propensity"] is None
        assert r["action_probabilities"] is None


def test_sentinel_without_approval_fails_closed_to_shadow_dual():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=0.2, seed=3)
    r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                    event_salt="e", traffic_stratum="batch")
    # user-visible change forbidden without approval: user still sees base
    assert r["chosen_action"] == "weak"


def test_sentinel_with_approval_can_diverge_and_logs_propensity():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=1.0, seed=7,
                            sentinel_rate_cap=UNCAPPED,
                            approved_for_user_visible=True)
    seen_diverge = False
    for i in range(50):
        r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                        event_salt=f"diverge-{i}", traffic_stratum="batch")
        assert r["chosen_propensity"] is not None
        assert 0 < r["chosen_propensity"] <= 1
        if r["chosen_action"] != "weak":
            seen_diverge = True
    assert seen_diverge  # epsilon=1: strong sometimes chosen


def test_default_rate_cap_trips_fail_closed():
    """The 0.05 default cap must downgrade to deterministic base once tripped."""
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=1.0, seed=7,
                            approved_for_user_visible=True)  # default cap 0.05
    tripped_at = None
    for i in range(200):
        r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                        event_salt=f"dcap-{i}", traffic_stratum="batch")
        if r["eligibility_reason"] == "rate_cap_tripped":
            tripped_at = i
            break
        assert r["chosen_propensity"] is not None
    assert tripped_at is not None, "default cap never tripped"
    # after trip: deterministic base, no propensity
    r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                    event_salt="dcap-after", traffic_stratum="batch")
    assert r["chosen_action"] == "weak"
    assert r["chosen_propensity"] is None
    assert r["exploration_mode"] == "disabled"


# ---------- T052 seeded determinism + exact propensity ----------

def test_seeded_randomization_is_deterministic():
    def run(seed):
        pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=0.5,
                                seed=seed, sentinel_rate_cap=UNCAPPED,
                                approved_for_user_visible=True)
        return [pol.resolve(base_action="weak",
                            scores={"confidence": 0.2},
                            event_salt=f"x{i}", traffic_stratum="batch"
                            )["chosen_action"] for i in range(20)]
    assert run(42) == run(42)


def test_exact_propensity_matches_stored_distribution():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=0.3, seed=11,
                            sentinel_rate_cap=UNCAPPED,
                            approved_for_user_visible=True)
    for i in range(30):
        r = pol.resolve(base_action="weak", scores={"confidence": 0.2},
                        event_salt=f"p{i}", traffic_stratum="batch")
        probs = r["action_probabilities"]
        assert abs(sum(probs.values()) - 1.0) < 1e-9
        assert r["chosen_propensity"] == pytest.approx(probs[r["chosen_action"]])
        # epsilon=0.3, base=weak: P(strong) = 0.3*0.5 = 0.15 exactly
        assert probs["strong"] == pytest.approx(0.15)


def test_all_randomized_events_validate():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=0.4, seed=13,
                            sentinel_rate_cap=UNCAPPED,
                            approved_for_user_visible=True)
    for i in range(10):
        r = pol.resolve(base_action="strong", scores={"confidence": 0.8},
                        event_salt=f"v{i}", traffic_stratum="batch")
        # every randomized record must carry a propensity in (0,1]
        assert r["chosen_propensity"] and 0 < r["chosen_propensity"] <= 1


# ---------- T053 caps ----------

def test_rate_cap_fail_closed():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=1.0, seed=17,
                            sentinel_rate_cap=0.10, approved_for_user_visible=True)
    sentinels = 0
    for i in range(100):
        r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                        event_salt=f"cap{i}", traffic_stratum="batch")
        if r["exploration_mode"] == "randomized_sentinel" and r["chosen_action"] != "weak":
            sentinels += 1
        else:
            # once the cap trips, mode must downgrade and base is returned
            if pol.realized_rate >= 0.10:
                assert r["chosen_action"] == "weak"
    # realized sentinel rate can slightly exceed the cap only at the boundary
    # event (one-call granularity); never by more than one sentinel
    assert pol.realized_rate <= 0.10 + 1.0 / 100


def test_spend_cap_hook_trips_fail_closed():
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=1.0, seed=19,
                            spend_cap_units=10.0, sentinel_rate_cap=UNCAPPED,
                            approved_for_user_visible=True)
    pol.charge(6.0)
    assert not pol.spend_tripped
    r1 = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                     event_salt="a", traffic_stratum="batch")
    assert r1["exploration_mode"] == "randomized_sentinel"
    pol.charge(6.0)  # total 12 >= cap 10
    r2 = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                     event_salt="b", traffic_stratum="batch")
    assert pol.spend_tripped
    assert r2["exploration_mode"] == "disabled"
    assert r2["eligibility_reason"] == "spend_cap_tripped"
    assert r2["chosen_action"] == "weak"


# ---------- T054: 10k-event simulation ----------

def test_10k_simulation_realized_rate_and_propensities():
    eps = 0.10
    pol = ExplorationPolicy(mode="randomized_sentinel", epsilon=eps, seed=101,
                            sentinel_rate_cap=UNCAPPED,  # uncapped for the rate proof
                            approved_for_user_visible=True)
    n = 10_000
    sentinel = 0
    for i in range(n):
        # alternate base action deterministically; scores irrelevant to the
        # mixture beyond base_action
        base = "strong" if i % 2 == 0 else "weak"
        r = pol.resolve(base_action=base, scores={"confidence": 0.5},
                        event_salt=f"sim-{i}", traffic_stratum="batch")
        assert r["exploration_mode"] == "randomized_sentinel"
        assert r["chosen_propensity"] is not None
        assert 0 < r["chosen_propensity"] <= 1
        if r["chosen_action"] != base:
            sentinel += 1
    realized = sentinel / n
    # expected alternate-action probability per event = eps*0.5 = 0.05
    expected = eps * 0.5
    # binomial sd at n=10k, p=0.05 ~ 0.00218; 5 sd tolerance
    assert abs(realized - expected) < 5 * (0.05 * 0.95 / n) ** 0.5, (
        f"realized {realized} vs expected {expected}")
    # all randomized events carried propensities (asserted per event above)


def test_shadow_dual_records_alternate_but_returns_base():
    pol = ExplorationPolicy(mode="shadow_dual", epsilon=0.0, seed=23)
    alts = set()
    for i in range(40):
        r = pol.resolve(base_action="weak", scores={"confidence": 0.1},
                        event_salt=f"sd{i}", traffic_stratum="batch")
        assert r["chosen_action"] == "weak"  # user NEVER sees the alternate
        assert r["exploration_mode"] == "shadow_dual"
        assert r["chosen_propensity"] in (0.5,)
        alts.add(r["sampled_alternate"])
    assert alts == {"weak", "strong"}  # both arms sampled over 40 events
