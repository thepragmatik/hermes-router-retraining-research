"""R6 Task 2 (TDD): _gen_body pure function — max_tokens 900, GEN_JSON_MODE
wired into the body. No network: only the pure body builder is tested."""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

from generate_items import _gen_body  # noqa: E402


def test_gen_body_default_max_tokens_900(monkeypatch):
    monkeypatch.delenv("GEN_JSON_MODE", raising=False)
    body = _gen_body("test/gen", "prompt here", seed=42)
    assert body["max_tokens"] == 900
    assert body["model"] == "test/gen"
    assert body["seed"] == 42
    assert body["temperature"] == 0.9
    assert body["messages"][0]["role"] == "system"
    assert "response_format" not in body
    assert json.loads(json.dumps(body))  # json-serializable


def test_gen_body_json_mode_adds_response_format(monkeypatch):
    monkeypatch.setenv("GEN_JSON_MODE", "1")
    body = _gen_body("test/gen", "p", seed=1)
    assert body["response_format"] == {"type": "json_object"}
    assert body["max_tokens"] == 900
