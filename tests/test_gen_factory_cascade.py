"""RED-first tests for the cascade labeler (Task 4b, $0, mock-tested).

ZERO real network: `ask` is always monkeypatched; the thin real caller in
cascade_label.py is never executed by tests. Verifiers are the REAL
run_verifier from Task 3a.
"""
import json, os, sys
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
EV = os.path.join(REPO, "evidence", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import cascade_label as cl  # noqa: E402
import ledger as ledger_mod  # noqa: E402
from verifiers import run_verifier  # noqa: E402


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def make_items(n):
    out = []
    for i in range(n):
        out.append({
            "item_id": "item%016d" % i,
            "question": "What is %d + %d?" % (i, i),
            "answer": str(2 * i),
            "verifier": {"type": "numeric_tol", "value": 2 * i},
            "batch_id": "b1",
        })
    return out


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(cl, "LEDGER_APPEND", ledger_mod.append)
    monkeypatch.setattr(cl, "BATCH_SPEND", ledger_mod.batch_spend)
    return tmp_path


def run_cascade(items, answers_w, answers_s, tmp_path):
    """answers_w/s: per-ITEM answer texts (None -> simulated outage)."""
    import re as _re
    calls = {"weak": [], "strong": []}

    def fake_ask(model, question, key):
        m = _re.match(r"What is (\d+) \+", question)
        i = int(m.group(1)) if m else 0
        if model == cl.WEAK:
            calls["weak"].append((model, question))
            a = answers_w[i]
            if a is None:
                raise RuntimeError("simulated weak outage")
            return a, {"prompt_tokens": 500, "completion_tokens": 100}
        calls["strong"].append((model, question))
        a = answers_s[i]
        if a is None:
            raise RuntimeError("simulated strong outage")
        return a, {"prompt_tokens": 900, "completion_tokens": 200}

    cl.process_batch(items, str(tmp_path / "labels.jsonl"),
                     ask_fn=fake_ask, cap_usd=1000.0, key="test-key")
    return calls


def test_weak_pass_no_strong_call(env):
    items = make_items(2)
    calls = run_cascade(items, ["0", "2"], [], env)
    assert len(calls["weak"]) == 2 and calls["strong"] == []
    labels = read_jsonl(env / "labels.jsonl")
    assert [l["label"] for l in labels] == ["weak_ok", "weak_ok"]
    assert all(l["strong_ok"] is None for l in labels)


def test_weak_fail_strong_pass_labels_need_strong(env):
    items = make_items(2)  # answers: 0, 2
    calls = run_cascade(items, ["wrong", "999"], ["0", "2"], env)
    # strong called IFF weak failed: exactly the failing items
    assert len(calls["strong"]) == 2
    labels = read_jsonl(env / "labels.jsonl")
    assert [l["label"] for l in labels] == ["need_strong", "need_strong"]
    assert [l["weak_ok"] for l in labels] == [False, False]
    assert [l["strong_ok"] for l in labels] == [True, True]


def test_label_mapping_and_schema(env):
    items = make_items(2)
    run_cascade(items, ["0", "no number"], ["unused", "2"], env)
    labels = read_jsonl(env / "labels.jsonl")
    assert set(labels[0].keys()) == {"item_id", "question", "weak_ok",
                                     "strong_ok", "label", "ts"}
    assert labels[0]["label"] == "weak_ok"
    assert labels[1]["label"] == "need_strong"
    assert labels[1]["strong_ok"] is True
    assert labels[0]["ts"].endswith("Z")


def test_weak_exception_counts_as_fail_and_escalates(env):
    items = make_items(1)
    calls = run_cascade(items, [None], ["0"], env)
    assert len(calls["strong"]) == 1
    labels = read_jsonl(env / "labels.jsonl")
    assert labels[0]["weak_ok"] is False and labels[0]["label"] == "need_strong"


def test_strong_exception_marks_strong_fail(env):
    items = make_items(1)
    run_cascade(items, ["wrong"], [None], env)
    labels = read_jsonl(env / "labels.jsonl")
    assert labels[0]["label"] == "need_strong"
    assert labels[0]["strong_ok"] is False


def test_ledger_rows_have_cost_and_no_question_text(env):
    items = make_items(2)
    run_cascade(items, ["0", "wrong"], ["unused", "2"], env)
    rows = read_jsonl(ledger_mod.LEDGER_PATH)
    stages = [r["stage"] for r in rows]
    assert stages == ["weak", "weak", "strong"]  # strong only for item 1
    blob = json.dumps(rows)
    assert "What is" not in blob  # NO question text in the ledger
    for r in rows:
        assert "est_cost_usd" in r
        assert r["item_id"] in ("item%016d" % 0, "item%016d" % 1)
    assert rows[0]["weak_ok"] is True and rows[1]["weak_ok"] is False
    strong_row = rows[2]
    assert strong_row["strong_ok"] is True
    assert strong_row["est_cost_usd"] >= 0.0


def test_cap_exceeded_aborts_mid_batch_and_keeps_prefix(env, monkeypatch):
    items = make_items(3)
    # force the cap to flip after the first item's ledger rows land
    state = {"n": 0}
    real_append = ledger_mod.append
    orig_labels = env / "labels.jsonl"

    def counting_append(row):
        real_append(row)
        if row.get("stage") in ("weak", "strong"):
            state["n"] += 1

    def spend(cap, batch):
        return state["n"] < 2  # under until 2 stage-rows exist

    monkeypatch.setattr(cl, "LEDGER_APPEND", counting_append)
    monkeypatch.setattr(cl, "BATCH_SPEND", spend)
    calls = {"strong": 0}

    def fake_ask(model, question, key):
        if model == cl.WEAK:
            calls.setdefault("weak", 0)
            calls["weak"] += 1
            return "wrong", {"prompt_tokens": 1, "completion_tokens": 1}
        calls["strong"] += 1
        return "definitely wrong", {"prompt_tokens": 1, "completion_tokens": 1}

    with pytest.raises(SystemExit) as exc:
        cl.process_batch(items, str(orig_labels), ask_fn=fake_ask,
                         cap_usd=0.01, key="test-key")
    assert "ABORT" in str(exc.value)
    # prefix integrity: exactly the items fully processed before the abort
    labels = read_jsonl(orig_labels)
    assert len(labels) == 1
    assert labels[0]["item_id"] == items[0]["item_id"]
    # item 0 fully processed (weak + strong rows land, cap flips, abort
    # before item 1's weak call)
    assert calls["weak"] == 1 and calls["strong"] == 1


def test_main_refuses_without_gen_go(monkeypatch, tmp_path):
    monkeypatch.delenv("GEN_GO", raising=False)
    monkeypatch.delenv("SPEND_CAP_USD", raising=False)
    items_path = tmp_path / "items_batch9.jsonl"
    items_path.write_text(json.dumps(make_items(1)[0]))
    with pytest.raises(SystemExit) as exc:
        cl.main([str(items_path)])
    assert "REFUSED" in str(exc.value)


def test_main_refuses_with_zero_spend_cap(monkeypatch, tmp_path):
    monkeypatch.setenv("GEN_GO", "1")
    monkeypatch.delenv("SPEND_CAP_USD", raising=False)
    items_path = tmp_path / "items_batch9.jsonl"
    items_path.write_text(json.dumps(make_items(1)[0]))
    with pytest.raises(SystemExit) as exc:
        cl.main([str(items_path)])
    assert "REFUSED" in str(exc.value)


def test_main_happy_path_end_to_end_mocked(monkeypatch, tmp_path):
    monkeypatch.setenv("GEN_GO", "1")
    monkeypatch.setenv("SPEND_CAP_USD", "10.0")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(cl, "EVIDENCE_DIR", str(tmp_path))  # labels stay local
    items = make_items(2)
    items_path = tmp_path / "items_batch9.jsonl"
    with open(items_path, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")

    import re as _re

    def fake_ask(model, question, key):
        m = _re.match(r"What is (\d+) \+", question)
        i = int(m.group(1)) if m else 0
        return str(2 * i), {"prompt_tokens": 10, "completion_tokens": 5}

    monkeypatch.setattr(cl, "ask", fake_ask)
    cl.main([str(items_path)])
    labels = read_jsonl(tmp_path / "labels_batch9.jsonl")
    assert len(labels) == 2
    assert all(l["label"] == "weak_ok" for l in labels)


def test_env_override_changes_model_pair(monkeypatch):
    monkeypatch.setenv("WEAK_MODEL", "test/weak-x")
    monkeypatch.setenv("STRONG_MODEL", "test/strong-y")
    import importlib
    importlib.reload(cl)
    assert cl.WEAK == "test/weak-x" and cl.STRONG == "test/strong-y"
    monkeypatch.delenv("WEAK_MODEL")
    monkeypatch.delenv("STRONG_MODEL")
    importlib.reload(cl)
    assert cl.WEAK == "mistralai/mistral-7b-chat"
    assert cl.STRONG == "openai/gpt-4-1106-preview"
