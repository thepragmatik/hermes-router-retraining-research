#!/usr/bin/env python3
"""$0 tests: probe results are injected; no network under test."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
import smoke_tiers


def test_all_ok_passes(capsys):
    rc = smoke_tiers.main(models=["w", "s"], probe_fn=lambda m, k: {
        "model": m, "ok": True, "reply": "ok", "error": ""}, key="k")
    assert rc == 0


def test_any_failure_exits_3(capsys):
    def fake(m, k):
        return {"model": m, "ok": m != "w", "reply": "", "error": "HTTP 404"}
    rc = smoke_tiers.main(models=["w", "s"], probe_fn=fake, key="k")
    assert rc == 3
    captured = capsys.readouterr()
    assert "HTTP 404" in captured.out and "SMOKE: FAIL" in captured.err


def test_missing_key_refuses(capsys):
    env = os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        rc = smoke_tiers.main(models=["w", "s"],
                              probe_fn=lambda m, k: {}, key=None)
        assert rc == 2
    finally:
        if env is not None:
            os.environ["OPENROUTER_API_KEY"] = env
