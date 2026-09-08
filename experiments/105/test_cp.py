"""Unit tests for the exact one-sided Clopper-Pearson upper bound (tasks.md T011)."""
import numpy as np
from scipy import stats as sps


def cp_upper(k, n, delta=0.05):
    """One-sided exact CP (1-delta) upper bound for Binomial(n, k/n)."""
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    return sps.beta.ppf(1 - delta, k + 1, n - k) if k > 0 else 1 - delta ** (1 / n)


def test_known_examples():
    assert abs(cp_upper(0, 100, 0.05) - (1 - 0.05 ** (1 / 100))) < 1e-9
    assert cp_upper(10, 10, 0.05) == 1.0
    ubs = [cp_upper(k, 200, 0.05) for k in range(0, 30)]
    assert all(ubs[i] < ubs[i + 1] for i in range(len(ubs) - 1))
    for k, n in [(3, 500), (7, 1000), (1, 50)]:
        assert abs(cp_upper(k, n, 0.05) - sps.beta.ppf(0.95, k + 1, n - k)) < 1e-9
        assert abs(cp_upper(k, n, 0.05) - sps.beta.ppf(0.95, k + 1, n - k)) < 1e-9
    # one-sided guarantee: P(X <= k) <= delta for X ~ Binomial(n, ub)
    # (at p = ub, observing <= k failures is a delta-probability event; the
    # scipy beta.ppf(1-d, k+1, n-k) definition satisfies cdf == delta exactly)
    for k, n in [(3, 500), (7, 1000), (0, 200)]:
        assert sps.binom.cdf(k, n, cp_upper(k, n, 0.05)) <= 0.05 + 1e-9
    # vectorized pipeline threshold matches the loop-form calibration on real data
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from calibrate import calibrate
    p = np.load('/tmp/v1p.npy'); wc = np.load('/tmp/wc.npy'); sc = np.load('/tmp/sc.npy')
    risk = ((wc == 0) & (sc == 1)).astype(int); s = 1.0 - p
    rng = np.random.default_rng(0); perm = rng.permutation(len(p)); cal = perm[:int(0.4 * len(p))]
    thr_v, cov_v, ub_v = calibrate(s[cal], risk[cal], 0.01)
    # loop-form reference
    order = np.argsort(-s[cal]); ys = risk[cal][order].astype(int)
    ubs = [cp_upper(int(ys[:m].sum()), m, 0.05) for m in range(1, len(ys) + 1)]
    ok = np.where(np.array(ubs) <= 0.01)[0]
    m = int(ok[-1]) + 1
    assert abs(thr_v - s[cal][order][m - 1]) < 1e-12
    assert abs(ub_v - ubs[ok[-1]]) < 1e-12
    print("CP bound unit tests: PASS (incl. vectorized-vs-loop equivalence on real data)")


if __name__ == "__main__":
    test_known_examples()
