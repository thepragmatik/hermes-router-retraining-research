"""Task 1 (R4): verifier_shape / self_verifier rejects must capture the raw
parsed item in the detail field (capped at 400 chars) so rejects are
auditable post-hoc."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
import generate_items


def test_verifier_shape_reject_captures_raw():
    def fake_call(model, prompt, key, seed):
        return json.dumps({"question": "Q?", "answer": "a",
                           "verifier": {"type": "regex", "value": "x"}})

    d = tempfile.mkdtemp()
    with mock.patch.object(generate_items, "ITEMS_DIR", d):
        generate_items.generate_batch(4, 1, "m", "k", 0, call_fn=fake_call,
                                      encode_fn=lambda t: [[0.0]],
                                      corpus_encode_fn=lambda t: [])
    rej = [json.loads(l) for l in open(
        os.path.join(d, "gen_rejects_batch4.jsonl"))]
    r = [x for x in rej if x["reason"] == "verifier_shape"][0]
    assert r["detail"], "verifier_shape reject must carry the raw parsed item"


def test_self_verifier_reject_captures_raw():
    def fake_call(model, prompt, key, seed):
        return json.dumps({"question": "Q?", "answer": "wrong",
                           "verifier": {"type": "exact_match",
                                        "value": "right"}})

    d = tempfile.mkdtemp()
    with mock.patch.object(generate_items, "ITEMS_DIR", d):
        generate_items.generate_batch(4, 1, "m", "k", 0, call_fn=fake_call,
                                      encode_fn=lambda t: [[0.0]],
                                      corpus_encode_fn=lambda t: [])
    rej = [json.loads(l) for l in open(
        os.path.join(d, "gen_rejects_batch4.jsonl"))]
    r = [x for x in rej if x["reason"] == "self_verifier"][0]
    assert r["detail"], "self_verifier reject must carry the raw parsed item"


def test_detail_capped_at_400_chars():
    def fake_call(model, prompt, key, seed):
        return json.dumps({"question": "Q" * 1000, "answer": "a",
                           "verifier": {"type": "regex", "value": "x"}})

    d = tempfile.mkdtemp()
    with mock.patch.object(generate_items, "ITEMS_DIR", d):
        generate_items.generate_batch(4, 1, "m", "k", 0, call_fn=fake_call,
                                      encode_fn=lambda t: [[0.0]],
                                      corpus_encode_fn=lambda t: [])
    rej = [json.loads(l) for l in open(
        os.path.join(d, "gen_rejects_batch4.jsonl"))]
    r = [x for x in rej if x["reason"] == "verifier_shape"][0]
    assert len(r["detail"]) <= 400
