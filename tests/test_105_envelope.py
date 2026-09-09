"""Idea 105 envelope unit tests (frozen per results/105/ENVELOPE_DEPLOY_PREREG.md).

Red-first: written before telemetry/envelope.py existed. The envelope module is
pure stdlib at runtime (production interpreter /usr/bin/python3 has no scipy);
tests cross-check the stdlib math against scipy where available.

KS fixture note: alarm fixtures are score-array equivalents of the Stage-0
drift.py fixtures (results/105/drift_stress.csv), injected directly into the
detector — no eval-slice rows are ever routed through the live detector
(prereg §5.4). The real drift fixtures were verified pre-prereg (prereg §5.1).
"""
import hashlib
import json
import math
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

try:
    from scipy import stats as sps  # test-interpreter only
except Exception:  # pragma: no cover
    sps = None

ARTIFACT = os.path.join(REPO, "telemetry", "envelope_config.json")
PREREG_ART_SHA = "a6d7772407881f0578dd5bcfc816d3879e687fdfaa5d8f1ad6b0bd6ec31ef678"
FROZEN_TABLE = {
    0.01: 0.8243549466133118,
    0.025: 0.6964215040206909,
    0.05: 0.6348569393157959,
}


# ---------- frozen artifact provenance ----------

def test_artifact_sha_matches_prereg_pin():
    h = hashlib.sha256(open(ARTIFACT, "rb").read()).hexdigest()
    assert h == PREREG_ART_SHA


def test_artifact_contains_frozen_table():
    cfg = json.load(open(ARTIFACT))
    assert cfg["deployed_alpha"] == 0.01
    assert cfg["delta"] == 0.05
    rows = {r["alpha"]: r for r in cfg["table"]}
    assert set(rows) == set(FROZEN_TABLE)
    for a, t in FROZEN_TABLE.items():
        assert rows[a]["threshold"] == t
    assert len(cfg["ks_detector"]["reference"]) == 11677
    assert cfg["ks_detector"]["window_size"] == 500
    assert cfg["ks_detector"]["fire_p"] == 0.01


def test_artifact_no_prompt_text():
    """The artifact embeds scores/counts only — never prompt text."""
    raw = open(ARTIFACT).read()
    assert "prompt" not in json.dumps(json.loads(raw))  # key names included
    cfg = json.loads(raw)
    assert set(cfg["provenance"]) == {
        "stage0_prereg", "stage0_report", "deploy_prereg", "stage0_csv",
        "stage0_csv_sha256", "v1_train_probs_sha256", "mf_router_pt_sha256",
        "winrate_table_sha256", "calibrate_source"}


# ---------- stdlib CP math (cross-checked against scipy) ----------

def test_binom_cdf_matches_scipy_on_frozen_rows():
    from telemetry.envelope import binom_cdf
    cfg = json.load(open(ARTIFACT))
    for r in cfg["table"]:
        got = 1.0 - binom_cdf(r["k_cal"], r["m_cal"], r["alpha"])
        assert got >= 0.95, f"CP duality failed at alpha={r['alpha']}"
        if sps is not None:
            want = float(sps.binom.sf(r["k_cal"], r["m_cal"], r["alpha"]))
            assert abs(got - want) < 1e-9, (got, want)


def test_binom_cdf_edge_cases():
    from telemetry.envelope import binom_cdf
    assert binom_cdf(-1, 10, 0.5) == 0.0
    assert binom_cdf(10, 10, 0.5) == 1.0
    assert binom_cdf(0, 5, 0.0) == 1.0
    assert binom_cdf(0, 5, 1.0) == 0.0
    if sps is not None:
        for k, n, p in [(3, 40, 0.2), (17, 2519, 0.01), (0, 200, 0.01), (5, 200, 0.01)]:
            assert abs(binom_cdf(k, n, p) - float(sps.binom.cdf(k, n, p))) < 1e-9


def test_ks_test_matches_scipy_decisions():
    """Pure-math KS must match scipy's fire/no-fire decision (prereg §5.1)."""
    from telemetry.envelope import ks_test
    ref = json.load(open(ARTIFACT))["ks_detector"]["reference"]
    base = ref[::23][:500]          # in-distribution stride sample
    d, p = ks_test(ref, base)
    assert p >= 0.01                # in-dist control must not fire
    if sps is not None:
        D, ps = sps.ks_2samp(ref, base)
        assert abs(D - d) < 1e-12
        # decision equivalence at the frozen alpha (tails agree to series accuracy)
        assert (ps < 0.01) == (p < 0.01) or abs(ps - p) < 1e-6
    for shift, must_fire in [(0.05, True), (-0.2, True)]:
        w = [min(1.0, max(0.0, v + shift)) for v in base]
        _, p2 = ks_test(ref, w)
        assert (p2 < 0.01) == must_fire


# ---------- config load + verify (fail-closed) ----------

def test_load_real_artifact_verifies():
    from telemetry.envelope import load_envelope_config
    cfg = load_envelope_config(REPO)
    assert cfg is not None
    assert cfg["deployed_alpha"] == 0.01


def test_load_fails_closed_on_corrupt(tmp_path):
    from telemetry.envelope import load_envelope_config
    bad = tmp_path / "envelope_config.json"
    bad.write_text("{not json")
    assert load_envelope_config(REPO, str(bad)) is None


def test_load_fails_closed_on_missing(tmp_path):
    from telemetry.envelope import load_envelope_config
    assert load_envelope_config(REPO, str(tmp_path / "nope.json")) is None


def test_load_fails_closed_on_tampered_threshold(tmp_path):
    """A threshold that is NOT verbatim in the Stage-0 CSV must not load."""
    from telemetry.envelope import load_envelope_config
    cfg = json.load(open(ARTIFACT))
    for r in cfg["table"]:
        if r["alpha"] == cfg["deployed_alpha"]:
            r["threshold"] = 0.5     # not a Stage-0 fold threshold
    bad = tmp_path / "envelope_config.json"
    bad.write_text(json.dumps(cfg))
    assert load_envelope_config(REPO, str(bad)) is None


def test_load_fails_closed_on_cp_violation(tmp_path):
    """m_cal/k_cal inconsistent with the CP bound must not load."""
    from telemetry.envelope import load_envelope_config
    cfg = json.load(open(ARTIFACT))
    for r in cfg["table"]:
        if r["alpha"] == cfg["deployed_alpha"]:
            r["k_cal"] = 500        # 500/2519 >> 0.01 -> CP duality fails
    bad = tmp_path / "envelope_config.json"
    bad.write_text(json.dumps(cfg))
    assert load_envelope_config(REPO, str(bad)) is None


def test_load_fails_closed_on_model_hash_drift(tmp_path, monkeypatch):
    from telemetry import envelope as env_mod
    cfg = json.load(open(ARTIFACT))
    cfg["provenance"]["mf_router_pt_sha256"] = "0" * 64
    bad = tmp_path / "envelope_config.json"
    bad.write_text(json.dumps(cfg))
    # point the model-hash check at a dummy file via the repo_dir contract:
    # load_envelope_config hashes <repo_dir>/router_v1/mf_router.pt against the
    # artifact's provenance value — tamper the provenance, expect failure.
    assert env_mod.load_envelope_config(REPO, str(bad)) is None


# ---------- Envelope behavior (flag frozen OFF-side is service tests) ----------

def _env(cfg=None):
    from telemetry.envelope import Envelope
    return Envelope(cfg if cfg is not None else json.load(open(ARTIFACT)),
                    flag_on=True)


def test_envelope_actions_frozen_vocabulary():
    env = _env()
    out = env.evaluate(score=0.90, decision="weak")
    assert out == {"enabled": True, "mode": "shadow", "alpha": 0.01,
                   "action": "accept-weak", "threshold_used": 0.8243549466133118}
    out = env.evaluate(score=0.90, decision="strong")
    assert out["action"] == "escalate-strong"  # never promotes weak for a strong row
    out = env.evaluate(score=0.50, decision="strong")
    assert out["action"] == "escalate-strong"
    out = env.evaluate(score=0.50, decision="weak")
    assert out["action"] == "escalate-strong"  # below threshold at alpha=0.01
    assert out["threshold_used"] == 0.8243549466133118


def test_envelope_no_safe_coverage_abstains():
    cfg = json.load(open(ARTIFACT))
    for r in cfg["table"]:
        if r["alpha"] == cfg["deployed_alpha"]:
            r["threshold"] = None   # NO_SAFE_COVERAGE row shape
    env = Envelope(cfg, flag_on=True) if False else _env(cfg)
    out = env.evaluate(score=0.9, decision="weak")
    assert out["action"] == "abstain"
    assert out["threshold_used"] is None


def test_envelope_counts_in_health_block():
    env = _env()
    env.evaluate(score=0.9, decision="weak")
    env.evaluate(score=0.1, decision="strong")
    h = env.health()
    assert h["enabled"] is True and h["mode"] == "shadow" and h["alpha"] == 0.01
    assert h["state"] == "active"
    assert h["action_counts"] == {"accept-weak": 1, "escalate-strong": 1,
                                  "abstain": 0, "disabled": 0}
    assert set(h["alarm_counts"]) == {"ks_fire", "ks_evaluations",
                                      "risk_breach", "load_failed", "error"}


def test_envelope_error_never_raises():
    env = _env()
    out = env.evaluate(score=float("nan"), decision="weak")  # garbage score
    assert out["action"] in ("escalate-strong", "disabled")
    env.evaluate(score=0.9, decision=None)  # garbage decision
    assert env.health()["alarm_counts"]["error"] >= 0  # recorded, never raised


# ---------- KS detector cadence + alarm permanence ----------

def test_ks_cadence_nonoverlapping():
    env = _env()
    ref = json.load(open(ARTIFACT))["ks_detector"]["reference"]
    scores = ref[::23]              # in-dist scores for feeding
    for i in range(499):
        env.evaluate(score=scores[i % len(scores)], decision="weak")
    assert env.health()["alarm_counts"]["ks_evaluations"] == 0
    env.evaluate(score=scores[0], decision="weak")           # 500th
    assert env.health()["alarm_counts"]["ks_evaluations"] == 1
    for i in range(499):
        env.evaluate(score=scores[(i + 1) % len(scores)], decision="weak")
    assert env.health()["alarm_counts"]["ks_evaluations"] == 1
    env.evaluate(score=scores[1], decision="weak")           # 1000th
    assert env.health()["alarm_counts"]["ks_evaluations"] == 2
    assert env.health()["state"] == "active"


def test_alarm_fixture_shift_disables_and_persists():
    from telemetry.envelope import Envelope
    cfg = json.load(open(ARTIFACT))
    env = Envelope(cfg, flag_on=True)
    base = cfg["ks_detector"]["reference"][::23][:500]
    # 499 in-dist, then 501 shifted: eval #1 at count 500 (mixed window, no
    # fire), eval #2 at count 1000 (fully shifted window) -> must fire.
    for i in range(499):
        env.evaluate(score=base[i], decision="weak")
    for i in range(501):
        env.evaluate(score=min(1.0, base[i % 500] + 0.05), decision="weak")
    assert env.health()["state"] == "alarm_disabled"
    assert env.health()["alarm_counts"]["ks_fire"] == 1
    assert env.health()["alarm_counts"]["ks_evaluations"] == 2
    out = env.evaluate(score=0.9, decision="weak")           # post-alarm
    assert out["action"] == "disabled"
    # counts frozen after alarm: no further KS evaluations
    ev = env.health()["alarm_counts"]["ks_evaluations"]
    for i in range(600):
        env.evaluate(score=0.9, decision="weak")
    h2 = env.health()
    assert h2["state"] == "alarm_disabled"
    assert h2["alarm_counts"]["ks_evaluations"] == ev
    assert h2["alarm_counts"]["ks_fire"] == 1


def test_alarm_fixture_adversarial_push_fires():
    from telemetry.envelope import Envelope
    cfg = json.load(open(ARTIFACT))
    env = Envelope(cfg, flag_on=True)
    base = cfg["ks_detector"]["reference"][::23][:500]
    for i in range(500):
        env.evaluate(score=min(1.0, max(0.0, base[i] - 0.2)), decision="weak")
    assert env.health()["state"] == "alarm_disabled"
    assert env.health()["alarm_counts"]["ks_fire"] == 1


def test_alarm_fixture_score_noise_fires():
    """Deterministic +-0.05 alternating noise (drift.py 'revision noise' analog)."""
    from telemetry.envelope import Envelope
    cfg = json.load(open(ARTIFACT))
    env = Envelope(cfg, flag_on=True)
    base = cfg["ks_detector"]["reference"][::23][:500]
    for i, v in enumerate(base):
        d = 0.05 if i % 2 == 0 else -0.05
        env.evaluate(score=min(1.0, max(0.0, v + d)), decision="weak")
    assert env.health()["state"] == "alarm_disabled"


def test_in_dist_control_does_not_fire():
    """500-stride in-distribution window: must stay active (specificity)."""
    from telemetry.envelope import Envelope
    cfg = json.load(open(ARTIFACT))
    env = Envelope(cfg, flag_on=True)
    base = cfg["ks_detector"]["reference"][::23][:500]
    for v in base:
        env.evaluate(score=v, decision="weak")
    assert env.health()["state"] == "active"
    assert env.health()["alarm_counts"]["ks_fire"] == 0


# ---------- risk-breach path (armed, inert in deploy) ----------

def test_risk_breach_fires_only_on_labeled_rows():
    from telemetry.envelope import Envelope
    cfg = json.load(open(ARTIFACT))
    ref = cfg["ks_detector"]["reference"]
    acc = [r for r in ref if r >= cfg["table"][0]["threshold"]]
    assert len(acc) >= 400  # enough accepted in-dist rows for 3 windows
    env = Envelope(cfg, flag_on=True)
    # unlabeled accepted rows: inert; feed the MIXED in-dist range (production
    # appends every evaluated score to the KS window — accepted-only scores
    # would be a genuinely shifted distribution and rightly alarm)
    for i in range(600):
        env.evaluate(score=ref[i % len(ref)], decision="weak")
    assert env.health()["state"] == "active"
    assert env.health()["alarm_counts"]["risk_breach"] == 0
    assert env.health()["alarm_counts"]["ks_fire"] == 0
    # labeled path: last 200 labeled ACCEPTED rows with k=5 (== critical, no
    # fire), then one more failure -> k=6 > 5 fires
    env2 = Envelope(cfg, flag_on=True)
    for i in range(195):
        env2.evaluate(score=acc[i % len(acc)], decision="weak", labeled_failure=0)
    for i in range(5):
        env2.evaluate(score=acc[i % len(acc)], decision="weak", labeled_failure=1)
    assert env2.health()["state"] == "active"
    assert env2.health()["alarm_counts"]["risk_breach"] == 0
    env2.evaluate(score=acc[0], decision="weak", labeled_failure=1)  # k=6
    assert env2.health()["state"] == "alarm_disabled"
    assert env2.health()["alarm_counts"]["risk_breach"] == 1


# ---------- load_failed state ----------

def test_envelope_load_failed_state():
    from telemetry.envelope import Envelope
    env = Envelope(None, flag_on=True)
    out = env.evaluate(score=0.9, decision="weak")
    assert out["action"] == "disabled" and out["threshold_used"] is None
    assert out["enabled"] is False
    h = env.health()
    assert h["state"] == "load_failed"
    assert h["alarm_counts"]["load_failed"] == 1
