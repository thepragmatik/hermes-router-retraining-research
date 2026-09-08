"""Task 3 (R4): escalation label rows must carry strong_final (the extracted
final-answer region of the strong-tier answer, capped) so 0/N strong rescues
become auditable ("wrong" vs "right-but-formulation-mismatch")."""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import json

import cascade_label as cl  # noqa: E402
import ledger as ledger_mod  # noqa: E402


def _make_item():
    return {
        "item_id": "item0000000000000001",
        "question": "What is 2 + 2?",
        "answer": "4",
        "verifier": {"type": "numeric_tol", "value": 4},
        "batch_id": "b1",
    }


def read_jsonl(p):
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def test_escalation_row_carries_strong_final(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(cl, "LEDGER_APPEND", ledger_mod.append)
    monkeypatch.setattr(cl, "BATCH_SPEND", ledger_mod.batch_spend)

    def fake_ask(model, question, key):
        if model == cl.WEAK:
            return "totally wrong", {"prompt_tokens": 1,
                                     "completion_tokens": 1}
        # strong gets it right but with extra formulation text
        return ("Let me think. The final answer: 4",
                {"prompt_tokens": 1, "completion_tokens": 1})

    labels_path = str(tmp_path / "labels.jsonl")
    cl.process_batch([_make_item()], labels_path, ask_fn=fake_ask,
                     cap_usd=1000.0, key="test-key")
    row = read_jsonl(labels_path)[0]
    assert "strong_final" in row, "escalation rows must capture strong_final"
    assert row["strong_final"] == "4"
    assert len(row["strong_final"]) <= 200


def test_weak_ok_row_has_no_strong_final(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(cl, "LEDGER_APPEND", ledger_mod.append)
    monkeypatch.setattr(cl, "BATCH_SPEND", ledger_mod.batch_spend)

    def fake_ask(model, question, key):
        return "4", {"prompt_tokens": 1, "completion_tokens": 1}

    labels_path = str(tmp_path / "labels.jsonl")
    cl.process_batch([_make_item()], labels_path, ask_fn=fake_ask,
                     cap_usd=1000.0, key="test-key")
    row = read_jsonl(labels_path)[0]
    assert row["strong_ok"] is None
    assert "strong_final" not in row
