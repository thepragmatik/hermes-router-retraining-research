"""RED-first tests for the spend-gated ledger (Task 4a, $0, pure-local)."""
import json, os, sys
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
CACHE = os.path.join(REPO, "evidence", "gen_factory", "model_pricing_cache.json")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import ledger as ledger_mod  # noqa: E402


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(ln) for ln in f if ln.strip()]


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(ledger_mod, "PRICING_CACHE", CACHE)
    return tmp_path


def test_append_writes_valid_jsonl(env):
    ledger_mod.append({"stage": "weak", "item_id": "abc", "batch_id": "b1"})
    ledger_mod.append({"stage": "strong", "item_id": "def", "batch_id": "b1"})
    rows = read_jsonl(ledger_mod.LEDGER_PATH)
    assert len(rows) == 2
    assert rows[0]["stage"] == "weak" and rows[1]["stage"] == "strong"


def test_append_never_raises_on_bad_path(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "no", "such", "dir",
                                     "x.jsonl"))
    ledger_mod.append({"stage": "weak"})  # dir does not exist -> best effort


def test_append_stamps_utc_ts(env):
    ledger_mod.append({"stage": "weak"})
    rows = read_jsonl(ledger_mod.LEDGER_PATH)
    assert rows[0]["ts"].endswith("Z") and "T" in rows[0]["ts"]


def test_batch_spend_under_and_over_cap(env):
    ledger_mod.append({"batch_id": "b1", "est_cost_usd": 0.01})
    ledger_mod.append({"batch_id": "b1", "est_cost_usd": 0.01})
    ledger_mod.append({"batch_id": "b2", "est_cost_usd": 0.50})
    assert ledger_mod.batch_spend(0.03, "b1") is True    # 0.02 < 0.03
    assert ledger_mod.batch_spend(0.02, "b1") is False   # 0.02 >= 0.02 -> over
    assert ledger_mod.batch_spend(0.10, "b2") is False   # 0.50 >= 0.10
    assert ledger_mod.batch_spend(1.0, "b_unknown") is True  # 0 spent
    assert ledger_mod.batch_spend(0.0, "b1") is False    # zero cap never passes


def test_batch_spend_missing_cache_file_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger_mod, "LEDGER_PATH",
                        os.path.join(str(tmp_path), "ledger.jsonl"))
    monkeypatch.setattr(ledger_mod, "PRICING_CACHE",
                        os.path.join(str(tmp_path), "missing.json"))
    ledger_mod.append({"batch_id": "b1", "est_cost_usd": 0.005})
    assert ledger_mod.batch_spend(0.01, "b1") is True


def test_price_row_known_model_priced_from_cache(env):
    entry = json.load(open(CACHE))["candidates"]["gpt4_1106"]
    row = ledger_mod.price_row(
        model=entry["id"],
        usage={"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000},
        base_row={"stage": "strong", "batch_id": "b9", "item_id": "i1"})
    assert row["est_cost_usd"] == pytest.approx(
        entry["pricing_prompt_usd_per_m"] + entry["pricing_completion_usd_per_m"])
    assert "unpriced" not in row
    assert row["prompt_tokens"] == 1_000_000
    assert row["completion_tokens"] == 1_000_000


def test_price_row_unknown_model_zero_cost_with_flag(env):
    row = ledger_mod.price_row(
        model="nope/totally-unknown-model",
        usage={"prompt_tokens": 1000, "completion_tokens": 500},
        base_row={"stage": "weak", "item_id": "i1", "batch_id": "b1"})
    assert row["est_cost_usd"] == 0.0
    assert row["unpriced"] is True
    ledger_mod.append(row)
    # $0-priced unknown-model rows never trip the cap
    assert ledger_mod.batch_spend(0.0001, "b1") is True


def test_price_row_legacy_router_pair_maps_via_role_alias(env):
    # V1-frozen pair ids are retired from the OpenRouter catalog; the cache
    # holds current ids. Role aliases keep the spend gate functional.
    cache = json.load(open(CACHE))
    weak = ledger_mod.price_row(
        model="mistralai/mistral-7b-chat",
        usage={"prompt_tokens": 1_000_000, "completion_tokens": 0},
        base_row={})
    strong = ledger_mod.price_row(
        model="openai/gpt-4-1106-preview",
        usage={"prompt_tokens": 0, "completion_tokens": 1_000_000},
        base_row={})
    assert weak["est_cost_usd"] == pytest.approx(
        cache["candidates"]["mistral_7b"]["pricing_prompt_usd_per_m"])
    assert strong["est_cost_usd"] == pytest.approx(
        cache["candidates"]["gpt4_1106"]["pricing_completion_usd_per_m"])
    assert "unpriced" not in weak and "unpriced" not in strong


def test_price_row_bad_usage_is_unpriced_not_crash(env):
    row = ledger_mod.price_row(model="mistralai/mistral-7b-chat",
                               usage={}, base_row={})
    assert row["est_cost_usd"] == 0.0 and row["unpriced"] is True
    row2 = ledger_mod.price_row(model=None, usage=None, base_row={})
    assert row2["est_cost_usd"] == 0.0 and row2["unpriced"] is True
