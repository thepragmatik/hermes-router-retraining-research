"""Unit tests for idea 102 Stage-0 invariants (G4/G5 style + structural
identity), run BEFORE the gate run (prereg integrity clause). pytest or plain
python execution both work."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import data as D
import diagnostics as DG
import dr_learner as DR
import evaluate as EV
import features as FE
import nuisance as NU
import policy as PO
import simulate as SI


def test_artifact_hashes():
    got = D.assert_artifacts()
    assert got["winrate_table"] == D.HASH_WINRATE
    assert got["v1_pstrong_fixture"] == D.HASH_PSTRONG


def test_load_and_split():
    d = D.load_train_matrix()
    assert d["n"] == 29193
    assert int(d["eval_mask"].sum()) == 5888
    assert int((~d["eval_mask"]).sum()) == 23305
    assert d["q_weak"].min() >= 0 and d["q_weak"].max() <= 1
    # measured data property: exactly 1 train row has cost_s < cost_w
    assert int((d["c_strong"] < d["c_weak"]).sum()) == 1


def test_v1_mask_matches_frozen_threshold():
    d = D.load_train_matrix()
    m = SI.v1_mask(d["p"])
    assert m.sum() == 22424  # measured frac_strong anchor 0.768129


def test_regimes_exact():
    d = D.load_train_matrix()
    p = d["p"]
    e1 = SI.regime_e("L1", p)
    assert np.allclose(e1, 0.5)
    e3 = SI.regime_e("L3", p)
    v1 = SI.v1_mask(p)
    assert np.allclose(e3, 0.8 * v1 + 0.1)
    assert (e3 >= 0.10 - 1e-12).all() and (e3 <= 0.90 + 1e-12).all()
    e2 = SI.regime_e("L2", p)
    assert np.allclose(e2, 0.6 * v1 + 0.2)


def test_simulate_exact_props_and_hidden_outcomes():
    d = D.load_train_matrix()
    sim = SI.simulate("L3", d["p"], 102000)
    SI.assert_log_invariants(sim, d["p"], ~d["eval_mask"], d)
    # recompute the exact formula and compare elementwise
    assert np.array_equal(sim["e1"], SI.regime_e("L3", d["p"]))
    # chosen propensities consistent
    e_ch = np.where(sim["a"] == 1, sim["e1"], 1 - sim["e1"])
    assert np.allclose(sim["e_chosen"], e_ch)
    # deterministic across reruns with same seed
    sim2 = SI.simulate("L3", d["p"], 102000)
    assert np.array_equal(sim["a"], sim2["a"])
    # different seed differs
    sim3 = SI.simulate("L3", d["p"], 102001)
    assert not np.array_equal(sim["a"], sim3["a"])


def test_g5_probes_loud():
    assert DG.nan_probe() is True
    assert DG.zero_probe() is True
    d = D.load_train_matrix()
    e1 = SI.regime_e("L3", d["p"])
    assert DG.corruption_probe(e1) is True


def test_identity_probe_exact_recovery():
    """A5: DR policy value of V1 with mu = true per-action means recovers the
    exact truth (estimator plumbing sanity on a tiny synthetic log)."""
    rng = np.random.default_rng(0)
    n = 4000
    p = rng.random(n)
    e1 = 0.8 * (p >= 0.3) + 0.1
    a = (rng.random(n) < e1).astype(int)
    q0 = (rng.random(n) < 0.2).astype(float)
    q1 = (rng.random(n) < 0.6).astype(float)
    y = np.where(a == 1, q1, q0)
    pi1 = (p >= 0.3).astype(float)
    mu0, mu1 = q0.copy(), q1.copy()  # "perfect" nuisances
    val, se, w = EV.dr_policy_value(pi1, a, y, e1, mu0, mu1, np.arange(n))
    truth = float(np.where(pi1 >= 0.5, q1, q0).mean())
    assert abs(val - truth) < 1e-10, (val, truth)


def test_dr_pseudo_outcome_unbiased_for_constant_tau():
    """On a synthetic log with known propensities and constant tau, the mean
    DR pseudo-outcome recovers tau (orthogonality sanity)."""
    rng = np.random.default_rng(1)
    n = 20000
    p = rng.random(n)
    e1 = 0.5 + 0.0 * p
    a = (rng.random(n) < e1).astype(int)
    q0 = (rng.random(n) < 0.2).astype(float)
    q1 = (rng.random(n) < 0.5).astype(float)  # tau = 0.3 everywhere
    y = np.where(a == 1, q1, q0)
    mu0 = np.full(n, 0.2)
    mu1 = np.full(n, 0.5)
    chi = DR.dr_pseudo_outcomes(mu0, mu1, a, y,
                                np.where(a == 1, e1, 1 - e1), e1)
    assert abs(chi.mean() - 0.3) < 0.02, chi.mean()


def test_policy_fallback_forces_v1():
    d = D.load_train_matrix()
    ev = d["eval_mask"]
    n_ev = int(ev.sum())
    score = np.zeros(n_ev)
    fb = np.ones(n_ev, bool)  # everything unsupported
    v1m = SI.v1_mask(d["p"])[ev]
    route, util = PO.route_from_score(score, 0, d["dcost"][ev], fb, v1m)
    assert np.array_equal(route, v1m)


def test_lambda_sweep_monotone_cost():
    d = D.load_train_matrix()
    ev = d["eval_mask"]
    n_ev = int(ev.sum())
    rng = np.random.default_rng(3)
    score = rng.normal(0.05, 0.05, n_ev)  # mostly mild positive
    fb = np.zeros(n_ev, bool)
    v1m = SI.v1_mask(d["p"])[ev]
    rows = PO.lambda_sweep(score, d, ev, d["dcost"][ev], fb, v1m)
    costs = [r["C"] for r in rows]
    assert costs == sorted(costs, reverse=True)  # higher lambda -> fewer strong
    assert [r["lambda"] for r in rows] == D.LAMBDA_GRID


def test_features_shape():
    d = D.load_train_matrix()
    fit = ~d["eval_mask"]
    top5 = FE.family_top5(d, fit)
    assert len(top5) == D.TOP_FAMILIES
    F, fams = FE.build_tau_features(d["p"], d["family"], fit, top5)
    assert F.shape[0] == d["n"]
    assert F.shape[1] == 2 + len(fams) + D.TOP_FAMILIES
    assert np.allclose(F[:, 0], 1.0)
    assert np.allclose(F[:, 1], d["p"])


def test_nuisance_oof_shapes():
    d = D.load_train_matrix()
    fit = ~d["eval_mask"]
    idx = np.flatnonzero(fit)
    sim = SI.simulate("L3", d["p"], 102000)
    y_all = np.where(sim["a"] == 1, d["q_strong"], d["q_weak"])
    mu0, mu1 = NU.oof_mu(d["p"][idx], sim["a"][idx], y_all[idx], 102000 + 777)
    assert mu0.shape == mu1.shape == (len(idx),)
    assert np.isfinite(mu0).all() and np.isfinite(mu1).all()


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"--- {len(fns) - failed}/{len(fns)} passed ---")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
