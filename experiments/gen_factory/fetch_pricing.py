#!/usr/bin/env python3
"""Pricing probe + model candidate cache (R0, $0: one public HTTP GET).

Fetches https://openrouter.ai/api/v1/models (public catalog endpoint, NO API
key, NO Authorization header, no chat calls), extracts
id / pricing.prompt / pricing.completion / context_length for the plan's
candidate list (substring match, tolerates id drift), and writes
evidence/gen_factory/model_pricing_cache.json keyed by stable role labels.

Exit codes: 0 ok; 1 a matched candidate has context_length < 16384;
2 network fetch failed (error recorded in pricing_fetch_error.md, cache NOT
written, so downstream tests skip rather than use stale data)."""
import json, os, re, sys, time
import urllib.request

BASE = "https://openrouter.ai/api/v1/models"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "evidence", "gen_factory",
                   "model_pricing_cache.json")
ERR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "evidence", "gen_factory",
                   "pricing_fetch_error.md")
MIN_CONTEXT = 16384

# role label -> ordered regexes over lowercased model ids (drift-tolerant)
CANDIDATES = {
    "llama33_70b": [r"llama-3\.3-70b-instruct"],
    "mixtral_or_mistral_small": [r"mixtral-8x22b", r"mistral-small-3"],
    "glm_flash": [r"glm-[\d.]+-flash", r"glm-flash"],
    "deepseek_flash": [r"deepseek-v4-flash$", r"deepseek-v4-flash",
                       r"deepseek-v4"],
    # Frozen generator-pivot labeling pair (operator decision 2026-09-07):
    # weak = qwen3.7-flash. deepseek-v4-flash-latest exists only as a tilde
    # alias; the canonical id deepseek-v4-flash is matched first ($ anchor).
    "qwen_flash": [r"qwen3\.7-flash", r"qwen[\d.]*-flash"],
    # gpt-4-1106-preview was retired from the catalog; gpt-4-turbo-preview
    # (same family) survives — drift tolerated per plan. Same for the weak
    # tier: mistral-7b-chat is gone; the surviving small-Mistral chat class
    # is ministral-8b.
    "gpt4_1106": [r"gpt-4-1106-preview", r"gpt-4-turbo-preview", r"gpt-4-turbo"],
    "mistral_7b": [r"mistral-7b-chat", r"mistral-7b", r"ministral-8b"],
}

def fetch_catalog(timeout=45):
    req = urllib.request.Request(
        BASE, headers={"User-Agent": "gen-factory-pricing-probe/0.1"})
    # NOTE: intentionally no Authorization header — public endpoint, $0.
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def pick(models, pattern):
    hits = [m for m in models
            if re.search(pattern, m.get("id", "").lower())]
    if not hits:
        return None
    plain = [m for m in hits if ":" not in m["id"]] or hits
    return min(plain, key=lambda m: len(m["id"]))  # shortest id = canonical

def per_m(p):
    # OpenRouter pricing fields are USD-per-token strings; "-1" = unlisted.
    try:
        f = float(p)
        return round(f * 1e6, 6) if f >= 0 else -1.0
    except (TypeError, ValueError):
        return -1.0

def main():
    try:
        cat = fetch_catalog()
    except Exception as e:  # network failure: record, no cache, exit 2
        os.makedirs(os.path.dirname(ERR), exist_ok=True)
        with open(ERR, "w") as f:
            f.write("# pricing fetch failure\n\n- url: %s\n- ts: %s\n"
                    "- error: %r\n" % (BASE, time.strftime("%Y-%m-%dT%H:%M:%S"), e))
        print("FETCH FAILED: %r (recorded in %s)" % (e, os.path.basename(ERR)),
              file=sys.stderr)
        return 2
    models = cat.get("data", [])
    out = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "source": BASE, "models_scanned": len(models), "candidates": {}}
    short = []
    for key, pats in CANDIDATES.items():
        m = next((pick(models, p) for p in pats if pick(models, p)), None)
        if m is None:
            continue
        p = m.get("pricing", {})
        entry = {"id": m["id"],
                 "context_length": m.get("context_length"),
                 "pricing_prompt_usd_per_m": per_m(p.get("prompt")),
                 "pricing_completion_usd_per_m": per_m(p.get("completion"))}
        out["candidates"][key] = entry
        if isinstance(entry["context_length"], int) \
                and entry["context_length"] < MIN_CONTEXT:
            short.append(entry)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    if short:
        print("CONTEXT TOO SMALL (<%d): %s" % (MIN_CONTEXT, short),
              file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
