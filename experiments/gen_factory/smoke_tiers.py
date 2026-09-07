#!/usr/bin/env python3
"""Pre-flight routeability smoke (R1b amendment): 2 calls per tier.

Any HTTP error (e.g. the qwen3.7-flash 404 class) aborts the rung with exit 3
BEFORE generation spend. 4 tiny calls ~= $0.0001. Never raises.
"""
import json
import os
import sys
import urllib.error
import urllib.request

SMOKE_PROMPT = "Reply with the single word: ok"


def probe(model, key, base="https://openrouter.ai/api/v1"):
    """One tiny chat call. Returns a dict result; never raises."""
    body = json.dumps({"model": model, "messages": [
        {"role": "user", "content": SMOKE_PROMPT}],
        "max_tokens": 5, "temperature": 0}).encode("utf-8")
    req = urllib.request.Request(base + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        return {"model": model, "ok": True,
                "reply": (d["choices"][0]["message"]["content"] or "")[:20],
                "error": ""}
    except urllib.error.HTTPError as e:
        return {"model": model, "ok": False, "reply": "",
                "error": "HTTP %d" % e.code}
    except Exception as e:
        return {"model": model, "ok": False, "reply": "",
                "error": type(e).__name__}


def main(models=None, probe_fn=None, key=None):
    key = key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("REFUSED: OPENROUTER_API_KEY not set; nothing ran", file=sys.stderr)
        return 2
    probe_fn = probe_fn or probe
    models = models or [os.environ.get("WEAK_MODEL", "z-ai/glm-5.3-flash"),
                        os.environ.get("STRONG_MODEL",
                                       "deepseek/deepseek-v4-flash")]
    results = [probe_fn(m, key) for m in models for _ in range(2)]  # 2 calls each
    for r in results:
        print(json.dumps(r))
    if not all(r["ok"] for r in results):
        print("SMOKE: FAIL — abort rung before generation spend", file=sys.stderr)
        return 3
    print("SMOKE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
