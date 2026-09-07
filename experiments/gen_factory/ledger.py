#!/usr/bin/env python3
"""Append-only cost ledger + batch spend gate (Task 4a, pure-local, $0).

Every API-side stage (weak/strong/log) appends exactly one row to
evidence/gen_factory/ledger.jsonl, stamped with a UTC ts. Costs are priced
from the Wave-0 model_pricing_cache.json (USD per 1M tokens, prompt +
completion) — never hardcoded per-call figures. Rows whose model can't be
priced get est_cost_usd=0.0 plus unpriced=true, so a retired catalog id can
never silently zero the spend gate; the V1-frozen router pair (retired ids)
is covered by minimal role aliases.

batch_spend(cap_usd, batch_id) -> True only if the batch's ledgered spend is
STRICTLY BELOW the cap (>= cap means stop); a zero cap never passes unless
nothing was spent.
"""
import datetime as _dt
import json
import os
import sys

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(MODULE_DIR))
LEDGER_PATH = os.path.join(REPO_DIR, "evidence", "gen_factory", "ledger.jsonl")
PRICING_CACHE = os.path.join(REPO_DIR, "evidence", "gen_factory",
                             "model_pricing_cache.json")

# V1-frozen pair ids are retired from the OpenRouter catalog; the pricing
# cache holds current ids. Map retired ids (and id fragments) to the cache
# candidate keys so the spend gate prices the roles they actually played.
ROLE_ALIASES = {
    "mistral-7b-chat": "mistral_7b",
    "mistral-7b-instruct": "mistral_7b",
    "gpt-4-1106-preview": "gpt4_1106",
}


def _utcnow_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(row):
    """Append one JSON line to the ledger. Best-effort: never raises."""
    try:
        row = dict(row)
        row.setdefault("ts", _utcnow_iso())
        os.makedirs(os.path.dirname(LEDGER_PATH) or ".", exist_ok=True)
        with open(LEDGER_PATH, "a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def batch_spend(cap_usd, batch_id):
    """True iff ledgered spend for batch_id is strictly below cap_usd."""
    total = 0.0
    try:
        with open(LEDGER_PATH) as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("batch_id") == batch_id:
                    total += float(r.get("est_cost_usd") or 0.0)
    except Exception:
        pass
    return total < cap_usd


def _cache_candidates():
    try:
        with open(PRICING_CACHE) as f:
            return json.load(f).get("candidates", {})
    except Exception:
        return {}


def _model_to_cache_key(model):
    """Match a model id (or retired alias) to a pricing-cache candidate key.

    Exact id match first; then retired-id alias; then unambiguous substring
    over current catalog ids (single hit only).
    """
    cands = _cache_candidates()
    if not model:
        return None, {}
    model_l = str(model).lower()
    for key, entry in cands.items():
        if entry.get("id", "").lower() == model_l:
            return key, entry
    for frag, key in ROLE_ALIASES.items():
        if frag in model_l:
            e = cands.get(key)
            if e:
                return key, e
    hits = [(key, entry) for key, entry in cands.items()
            if entry.get("id", "").lower() in model_l]
    if len(hits) == 1:
        return hits[0]
    return None, {}


def price_row(model, usage, base_row=None):
    """Price one API row from the Wave-0 cache; unknown models are $0+flag.

    usage: {"prompt_tokens": int, "completion_tokens": int} (e.g. OpenRouter
    response usage dict, passed through as-is).
    """
    base = dict(base_row or {})
    key, entry = _model_to_cache_key(model)
    usage = usage or {}
    try:
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        ok_usage = usage and (pt > 0 or ct > 0)
    except Exception:
        pt = ct = 0
        ok_usage = False
    if entry and ok_usage:
        cost = (pt / 1e6) * entry["pricing_prompt_usd_per_m"] \
             + (ct / 1e6) * entry["pricing_completion_usd_per_m"]
        base["est_cost_usd"] = round(cost, 8)
    else:
        base["est_cost_usd"] = 0.0
        base["unpriced"] = True
    base["prompt_tokens"] = pt
    base["completion_tokens"] = ct
    if key:
        base["price_key"] = key
    base.setdefault("ts", _utcnow_iso())
    return base


if __name__ == "__main__":
    # tiny CLI: --cap X --batch Y -> prints "under"/"over"; --dump prints rows
    cap = batch = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--cap":
            cap = float(args[i + 1])
        elif a == "--batch":
            batch = args[i + 1]
    if cap is not None and batch is not None:
        print("under" if batch_spend(cap, batch) else "over")
    elif args and args[0] == "--dump":
        with open(LEDGER_PATH) as f:
            sys.stdout.write(f.read())
    else:
        print("usage: ledger.py --cap X --batch Y | --dump", file=sys.stderr)
        sys.exit(1)
