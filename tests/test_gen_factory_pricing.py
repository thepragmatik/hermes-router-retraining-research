import json, os, time
import pytest
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "evidence", "gen_factory", "model_pricing_cache.json")
ERR = os.path.join(REPO, "evidence", "gen_factory", "pricing_fetch_error.md")

# Candidate keys (cache is keyed by role label, not by provider id string,
# so id drift does not break freshness checks).
CANDIDATE_KEYS = ["llama33_70b", "mixtral_or_mistral_small", "glm_flash",
                  "deepseek_flash", "gpt4_1106", "mistral_7b", "qwen_flash"]

def test_pricing_cache_exists_fresh_and_complete():
    if not os.path.exists(CACHE):
        if os.path.exists(ERR):
            pytest.skip("network fetch of OpenRouter models failed; "
                        "error recorded in pricing_fetch_error.md")
        # Fallback (offline dev only): attempt the fetch once; if it fails,
        # the script records the error file and we skip with the real reason.
        import subprocess
        r = subprocess.run(["/usr/bin/python3",
                            os.path.join(REPO, "experiments", "gen_factory",
                                         "fetch_pricing.py")],
                           capture_output=True, text=True, timeout=180)
        if not os.path.exists(CACHE):
            assert os.path.exists(ERR), (
                "no cache and no pricing_fetch_error.md; fetch_pricing.py "
                "must record failures: " + (r.stderr[-500:] or r.stdout[-500:]))
            pytest.skip("network fetch of OpenRouter models failed; "
                        "error recorded in pricing_fetch_error.md")
    age_days = (time.time() - os.path.getmtime(CACHE)) / 86400.0
    assert age_days < 7, f"pricing cache stale: {age_days:.1f} days old"
    cache = json.load(open(CACHE))
    present = [k for k in CANDIDATE_KEYS if k in cache.get("candidates", {})]
    assert len(present) >= 5, (
        f"only {len(present)} candidate keys in cache: {present}")
    for k in present:
        c = cache["candidates"][k]
        assert c.get("id"), f"{k}: missing model id"
        assert "context_length" in c, f"{k}: missing context_length"
        assert "pricing_prompt_usd_per_m" in c, f"{k}: missing input price"
        assert "pricing_completion_usd_per_m" in c, f"{k}: missing output price"
