"""Stage-0 invariant tests: T013/T018 — propensity invariants, action
membership, exactness, corrupted/missing propensities fail loudly, truth
reconstruction, support flagging. Run with plain python."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telemetry import stage0


def test_logging_invariants():
    p, out, n = stage0.load_train_matrix()
    probs = stage0.logging_probs(p)
    assert probs.shape == (n, 2)
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert (probs > 0).all(), "epsilon-mixture must guarantee nonzero support"
    for seed in [101000, 101001]:
        actions, oc, props = stage0.simulate_logging(p, out, seed)
        assert set(np.unique(actions)) <= {0, 1}
        assert actions.shape == oc.shape == props.shape == (n,)
        assert ((props > 0) & (props <= 1)).all()
        # exactness: stored propensity equals policy prob of chosen action
        assert np.allclose(props, probs[np.arange(n), actions])
        # outcomes match chosen action's full-information outcome
        assert np.array_equal(oc, out[np.arange(n), actions])


def test_corrupted_propensity_loud():
    p, out, n = stage0.load_train_matrix()
    tp = stage0.target_policies(p)["V1"]
    actions, oc, props = stage0.simulate_logging(p, out, 101000)
    for bad_val in (0.0, 1.5, -0.1):
        bad = props.copy(); bad[0] = bad_val
        for fn in (lambda a, o, pr: stage0.ips(tp, a, o, pr),
                   lambda a, o, pr: stage0.dr_crossfit(p, tp, a, o, pr, 101000),
                   lambda a, o, pr: stage0.switch_dr(p, tp, a, o, pr, 101000)):
            try:
                fn(actions, oc, bad)
                raise AssertionError(f"silent estimate with propensity {bad_val}")
            except ValueError:
                pass
    bad = props.copy(); bad[0] = np.nan
    try:
        stage0.ips(actions, oc, bad) if False else stage0.ips(tp, actions, oc, bad)
        raise AssertionError("silent estimate with NaN propensity")
    except ValueError:
        pass


def test_truth_reconstruction_and_gates():
    res = stage0.run_stage0()
    g = stage0.evaluate_gates(res)
    assert g["G1_ordering"]["passed"], g
    assert g["G2_accuracy"]["passed"], g
    truth = res["truth"]
    assert truth["V1"] > truth["V1_hi"] > truth["always_weak"]


def test_support_flag():
    p, out, n = stage0.load_train_matrix()
    tp = np.zeros((n, 2))
    tp[p[:, 0] < 0.05, 1] = 1.0
    actions, oc, props = stage0.simulate_logging(p, out, 101000)
    v, se, w_raw, w_used, nc = stage0.switch_dr(p, tp, actions, oc, props, 101000)
    unsup, reasons = stage0.support_flag(tp, actions, props, w_raw)
    assert unsup and reasons, "zero-overlap target must be flagged"
    ok_tp = stage0.target_policies(p)["V1"]
    v2, se2, w2, _, _ = stage0.switch_dr(p, ok_tp, actions, oc, props, 101000)
    assert not stage0.support_flag(ok_tp, actions, props, w2)[0], "V1 must not be flagged"


if __name__ == "__main__":
    for fn in (test_logging_invariants, test_corrupted_propensity_loud,
               test_support_flag, test_truth_reconstruction_and_gates):
        fn()
        print("PASS", fn.__name__)
    print("ALL STAGE-0 TESTS PASS")
