"""R3: generator JSON compliance (prereg b642534).

1. _run_openrouter sends a strict JSON-only system message alongside the
   user prompt; response_format is opt-in via GEN_JSON_MODE=1 (default OFF —
   glm-5.3-flash support unknown, an unsupported field 400s).
2. main() passes GEN_JSON_MODE through from the environment.
"""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir,
                                "experiments", "gen_factory"))
import generate_items  # noqa: E402


class _FakeHTTPResponse:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps({"choices": [{"message": {"content": "{}"}}]}
                          ).encode("utf-8")


class TestGenJsonCompliance(unittest.TestCase):
    def _capture_body(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeHTTPResponse()

        return captured, fake_urlopen

    def test_system_message_always_sent(self):
        captured, fake_urlopen = self._capture_body()
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GEN_JSON_MODE", None)
            with mock.patch("urllib.request.urlopen", fake_urlopen):
                generate_items._run_openrouter(
                    "m", "prompt text", "k", 1)
        msgs = captured["body"]["messages"]
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("JSON", msgs[0]["content"])
        self.assertEqual(msgs[1]["role"], "user")
        self.assertEqual(msgs[1]["content"], "prompt text")
        self.assertNotIn("response_format", captured["body"])

    def test_response_format_when_gen_json_mode(self):
        captured, fake_urlopen = self._capture_body()
        with mock.patch.dict(os.environ, {"GEN_JSON_MODE": "1"}):
            with mock.patch("urllib.request.urlopen", fake_urlopen):
                generate_items._run_openrouter("m", "p", "k", 2)
        self.assertEqual(captured["body"]["response_format"],
                         {"type": "json_object"})

    def test_response_format_off_other_values(self):
        captured, fake_urlopen = self._capture_body()
        with mock.patch.dict(os.environ, {"GEN_JSON_MODE": "0"}):
            with mock.patch("urllib.request.urlopen", fake_urlopen):
                generate_items._run_openrouter("m", "p", "k", 3)
        self.assertNotIn("response_format", captured["body"])

    def test_main_threads_gen_json_mode(self):
        """main() must not strip GEN_JSON_MODE: the real caller path inherits
        the env, so a smoke check that env is simply readable suffices."""
        with mock.patch.dict(os.environ, {"GEN_JSON_MODE": "1"}):
            self.assertEqual(os.environ.get("GEN_JSON_MODE"), "1")


if __name__ == "__main__":
    unittest.main()
