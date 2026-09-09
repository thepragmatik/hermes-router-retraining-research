"""Idea 105 conformal safety envelope: runtime load + apply + alarms.

Frozen per results/105/ENVELOPE_DEPLOY_PREREG.md:
- Deployment form is the frozen qualified-threshold table in
  telemetry/envelope_config.json (per-alpha MAX fold-qualified CP threshold
  from Stage 0; deployed alpha 0.01).
- Score: s_runtime = 1 - round(p, 4) (the engine's reported confidence).
  Record-only shadow verdict: the envelope NEVER changes the V1 decision.
- Fail-open: any envelope trouble (load failure, exception, alarm) yields
  action "disabled" and the raw V1 decision stands.
- Runtime is STDLIB-ONLY: the production interpreter is /usr/bin/python3
  (no scipy/numpy/pandas). All math is pure Python.

CSV-verification note: the load-time check is threshold-verbatim-in-CSV +
CP duality + model-hash. The Stage-0 CSV in the MAIN checkout can carry
uncommitted float-precision churn (cp_ub/cost_ev last digits) from an old
pipeline rerun, so a CSV *content* gate would fail-closed forever there;
the pinned stage0_csv_sha256 is audit/test-only for that reason. The
threshold column itself is byte-stable (verified on the worktree copy).
"""
import csv
import hashlib
import json
import math
import os
import threading
from collections import deque

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(_THIS_DIR)
# Artifact path: repo default, overridable for tests/ops (ROUTER_ENVELOPE_CONFIG).
# The enable FLAG itself comes only from router_config.yaml (router.envelope_enabled).
ARTIFACT_DEFAULT = os.environ.get("ROUTER_ENVELOPE_CONFIG") or os.path.join(
    _THIS_DIR, "envelope_config.json")
MODEL_PATH = os.path.join(REPO_DIR, "router_v1", "mf_router.pt")
STAGE0_CSV = os.path.join(REPO_DIR, "results", "105", "coverage_risk_global.csv")

ACTIONS = ("accept-weak", "escalate-strong", "abstain", "disabled")


# ---------------- stdlib math (cross-checked against scipy in tests) ----------

def binom_cdf(k, n, p):
    """Exact binomial CDF via the regularized incomplete beta (stdlib only).

    P(X <= k), X ~ Binomial(n, p), = I_{1-p}(n-k, k+1).
    """
    if n <= 0:
        return 1.0
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    return _betainc_reg(float(n - k), float(k + 1), 1.0 - p)


def _betainc_reg(a, b, x):
    """Regularized incomplete beta I_x(a, b) via Lentz continued fraction."""
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log1p(-x))
    front = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * _betacf(b, a, 1.0 - x) / b


def _betacf(a, b, x, itmax=300, eps=3e-14):
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def ks_test(sample_a, sample_b):
    """Two-sample asymptotic KS (D, p). Pure math, matches scipy decisions."""
    a = sorted(float(v) for v in sample_a)
    b = sorted(float(v) for v in sample_b)
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
    allv = sorted(set(a) | set(b))
    d = 0.0
    i = j = 0
    cdf_a = cdf_b = 0.0
    for v in allv:
        while i < n1 and a[i] <= v:
            i += 1
        while j < n2 and b[j] <= v:
            j += 1
        cdf_a, cdf_b = i / n1, j / n2
        d = max(d, abs(cdf_a - cdf_b))
    en = math.sqrt(n1 * n2 / (n1 + n2))
    lam = en * d
    if lam == 0.0:
        return d, 1.0
    s = 0.0
    for k in range(1, 100000):
        term = (-1.0) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
        s += term
        if abs(term) < 1e-18:
            break
    p = max(0.0, min(1.0, 2.0 * s))
    return d, p


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------- config load + fail-closed verification ----------------

def load_envelope_config(repo_dir=REPO_DIR, artifact_path=ARTIFACT_DEFAULT):
    """Load + verify the frozen calibration artifact. Returns cfg or None.

    Verification (frozen prereg §3): JSON parses; table/ks structure intact;
    every table row's threshold appears VERBATIM in the committed Stage-0 CSV
    for that alpha; the producing fold's (m_cal, k_cal) satisfies the exact CP
    duality P(Bin(m_cal, alpha) >= k_cal + 1) >= 1 - delta (stdlib math);
    mf_router.pt sha256 matches the artifact's pinned provenance.
    """
    try:
        with open(artifact_path) as f:
            cfg = json.load(f)
    except Exception:
        return None
    try:
        table = cfg["table"]
        if not isinstance(table, list) or len(table) != 3:
            return None
        alphas = set()
        for r in table:
            if not isinstance(r, dict) or "alpha" not in r:
                return None
            alphas.add(round(float(r["alpha"]), 6))
        if alphas != {0.01, 0.025, 0.05}:
            return None
        if cfg["deployed_alpha"] not in alphas or cfg["delta"] != 0.05:
            return None
        ks = cfg["ks_detector"]
        if ks["window_size"] != 500 or ks["fire_p"] != 0.01:
            return None
        ref = ks["reference"]
        if not isinstance(ref, list) or len(ref) != 11677:
            return None
        if not all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in ref):
            return None
        # thresholds verbatim in the committed Stage-0 CSV (pure stdlib scan)
        csv_thresholds = {}
        with open(STAGE0_CSV, newline="") as f:
            for row in csv.DictReader(f):
                a = round(float(row["alpha"]), 6)
                csv_thresholds.setdefault(a, set()).add(row["threshold"])
        for r in table:
            t = r.get("threshold")
            a = round(float(r["alpha"]), 6)
            if t is None:
                continue  # NO_SAFE_COVERAGE row: legal; abstain at runtime
            if repr(float(t)) not in csv_thresholds.get(a, set()) \
                    and str(t) not in csv_thresholds.get(a, set()):
                return None
            # exact CP duality: P(Bin(m_cal, a) >= k_cal + 1) >= 1 - delta
            tail = 1.0 - binom_cdf(int(r["k_cal"]), int(r["m_cal"]),
                                   float(r["alpha"]))
            if tail < 0.95:
                return None
        want = cfg.get("provenance", {}).get("mf_router_pt_sha256")
        if not want or _sha256_file(MODEL_PATH) != want:
            return None
        return cfg
    except Exception:
        return None


# ---------------- runtime envelope ----------------

class Envelope:
    """Record-only conformal safety verdict + drift alarms (fail-open)."""

    def __init__(self, cfg, flag_on):
        self._lock = threading.Lock()
        self._flag_on = bool(flag_on)
        self._cfg = cfg if self._flag_on else None
        if self._cfg is not None:
            try:
                self._alpha = float(self._cfg["deployed_alpha"])
                rows = {round(float(r["alpha"]), 6): r for r in self._cfg["table"]}
                self._row = rows[self._alpha]
                self._threshold = (None if self._row.get("threshold") is None
                                   else float(self._row["threshold"]))
                self._ks_ref = list(self._cfg["ks_detector"]["reference"])
                self._ks_win = int(self._cfg["ks_detector"]["window_size"])
                self._ks_fire_p = float(self._cfg["ks_detector"]["fire_p"])
                # risk-breach critical count: smallest k with
                # P(X <= k) >= q at (window_n, alpha); fire iff observed k > crit
                rb = self._cfg.get("risk_breach", {})
                n_rb = int(rb.get("window", 200))
                q_rb = float(rb.get("quantile", 0.95))
                crit = 0
                while crit <= n_rb and binom_cdf(crit, n_rb, self._alpha) < q_rb:
                    crit += 1
                self._risk_crit = crit
                self._rb_window = n_rb
                self._rb_labels = deque(maxlen=n_rb)   # 1=failure, 0=ok
            except Exception:
                self._cfg = None
        if self._cfg is None:
            self._alpha = None
            self._row = None
            self._threshold = None
            self._ks_ref = []
            self._ks_win = 500
            self._ks_fire_p = 0.01
        self._reset_state()

    def _reset_state(self):
        self._window = deque(maxlen=self._ks_win)
        self._since_eval = 0
        self._rb_labels = deque(maxlen=getattr(self, "_rb_window", 200))
        self._state = "active" if (self._flag_on and self._cfg) else (
            "load_failed" if self._flag_on else "off")
        self._action_counts = {a: 0 for a in ACTIONS}
        self._alarm_counts = {"ks_fire": 0, "ks_evaluations": 0,
                              "risk_breach": 0, "load_failed": 0, "error": 0}
        if self._flag_on and self._cfg is None:
            self._alarm_counts["load_failed"] = 1

    # -- public API --

    def evaluate(self, score, decision, labeled_failure=None):
        """Record-only verdict for one route. NEVER raises, NEVER blocks."""
        with self._lock:
            try:
                return self._evaluate_locked(score, decision, labeled_failure)
            except Exception:
                self._alarm_counts["error"] += 1
                self._action_counts["disabled"] += 1
                return self._frame("disabled", None)

    def health(self):
        with self._lock:
            return {"enabled": self._flag_on and self._cfg is not None,
                    "mode": "shadow", "alpha": self._alpha,
                    "state": self._state,
                    "action_counts": dict(self._action_counts),
                    "alarm_counts": dict(self._alarm_counts)}

    # -- internals --

    def _frame(self, action, threshold_used):
        return {"enabled": self._flag_on and self._cfg is not None,
                "mode": "shadow", "alpha": self._alpha, "action": action,
                "threshold_used": threshold_used}

    def _evaluate_locked(self, score, decision, labeled_failure):
        if not self._flag_on or self._cfg is None:
            # flag OFF or load failure: silent no-op frame (service omits it)
            return self._frame("disabled", None)
        if self._state == "load_failed":
            self._action_counts["disabled"] += 1
            return self._frame("disabled", None)
        if self._state == "alarm_disabled":
            self._action_counts["disabled"] += 1
            return self._frame("disabled", self._threshold)
        try:
            s = float(score)
            if not (s == s) or s in (float("inf"), float("-inf")):
                raise ValueError("non-finite score")
        except Exception:
            self._alarm_counts["error"] += 1
            self._action_counts["disabled"] += 1
            return self._frame("disabled", self._threshold)
        # --- KS cadence (frozen: non-overlapping, every 500 new scores) ---
        self._window.append(s)
        self._since_eval += 1
        if self._since_eval >= self._ks_win:
            self._since_eval = 0
            self._alarm_counts["ks_evaluations"] += 1
            _, p = ks_test(self._ks_ref, list(self._window))
            if p < self._ks_fire_p:
                self._alarm_counts["ks_fire"] += 1
                self._state = "alarm_disabled"
                self._action_counts["disabled"] += 1
                return self._frame("disabled", self._threshold)
        # --- risk-breach path (armed but inert: only labeled accepted rows
        # count; sliding window of the last 200 labeled ACCEPTED rows) ---
        if self._threshold is not None and s >= self._threshold \
                and labeled_failure is not None:
            self._rb_labels.append(1 if labeled_failure else 0)
            if len(self._rb_labels) >= self._rb_window \
                    and sum(self._rb_labels) > self._risk_crit:
                self._alarm_counts["risk_breach"] += 1
                self._state = "alarm_disabled"
                self._action_counts["disabled"] += 1
                return self._frame("disabled", self._threshold)
        # --- frozen action vocabulary (record-only) ---
        if self._threshold is None:
            action = "abstain"          # NO_SAFE_COVERAGE at deployed alpha
        elif s >= self._threshold:
            action = ("accept-weak" if decision == "weak"
                      else "escalate-strong")
        else:
            action = "escalate-strong"
        self._action_counts[action] += 1
        return self._frame(action, self._threshold)
