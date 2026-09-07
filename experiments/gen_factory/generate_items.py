#!/usr/bin/env python3
"""R0 generator with verifier-by-construction + dedup gate ($0 in tests).

Generates benchmark-style questions with machine-checkable verifiers via
OpenRouter chat completions, parses STRICTLY (non-JSON / missing keys /
verifier-shape failures are counted rejects, never exceptions), self-verifies
each item with the Task-3a verifiers, gates every accepted candidate through
an embedding-dedup check against the sealed corpora (cosine >= 0.85 reject),
and appends survivors to evidence/gen_factory/items_batch{rung}.jsonl.

$0 posture: the real OpenRouter caller (`_run_openrouter`) is a thin
module-level function containing the only urllib usage; tests always inject
`call_fn` and never execute it. The dedup encoder defaults to the real
bge-small embedder (lazy, cpu) but accepts an injectable `encode_fn` /
`corpus_encode_fn`, so tests never download or run the model.
"""
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

import numpy as np

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(MODULE_DIR))
EVIDENCE_DIR = os.path.join(REPO_DIR, "evidence", "gen_factory")
ITEMS_DIR = EVIDENCE_DIR

# Sealed corpus frames used by the dedup gate (all expose a `prompt` column;
# verified in Wave 0 planning: winrate 36,497 / val 3,626 / test 3,678 rows).
CORPUS_FRAMES = ("winrate_table", "mf_val_frame", "mf_test_frame")
DEFAULT_CORPUS_ROOT = os.path.expanduser("~/transfer-bundle/analysis")

DEDUP_THRESHOLD = 0.85
GEN_MODEL_TAG = "BAAI/bge-small-en-v1.5"

GEN_PROMPT = """You generate ONE {domain} question for a model-routing benchmark. \
Difficulty: {difficulty}. Style seed: {style}. \
Emit STRICT JSON: {{"question": "...", "answer": "...", "verifier": {{"type": \
"exact_match"|"numeric_tol", "value": ...}}}}. The question must be \
self-contained, have ONE defensible answer, and be answerable in <= 200 words. \
No meta commentary."""

_FINAL_MARKER = re.compile(
    r"(?:the\s+)?final\s+answer\b(?:\s+is)?\s*[:\-]?\s*|answer\s*[:\-]\s*", re.I)

# ---------------------------------------------------------------- corpus I/O

_PROMPT_CACHE = None  # {"winrate_table": [...], ...}, loaded once


def load_prompt_sources(root=None):
    """Load the three corpus prompt columns ONCE as lists of str.

    `root` is injectable for tests; defaults to the transfer-bundle analysis
    dir (expanduser at runtime — no absolute user paths in source).
    """
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None and root is None:
        return _PROMPT_CACHE
    import pandas as pd
    root = root or DEFAULT_CORPUS_ROOT
    out = {}
    for frame in CORPUS_FRAMES:
        path = os.path.join(root, frame + ".parquet")
        df = pd.read_parquet(path, columns=["prompt"])
        out[frame] = [str(p) for p in df["prompt"].tolist() if p]
    if root is None:
        _PROMPT_CACHE = out
    return out


# ------------------------------------------------------- bge embedder (lazy)

_MODEL = None  # SentenceTransformer, loaded lazily once, device cpu


def bge():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(GEN_MODEL_TAG, device="cpu")
    return _MODEL


def bge_encode(texts):
    """L2-normalized bge-small embeddings (cosine == dot)."""
    return bge().encode(list(texts), normalize_embeddings=True,
                        show_progress_bar=False)


# ------------------------------------------------------------- dedup gate

def _max_cos(row, mat):
    """Max cosine similarity between row (D,) and rows of mat (N, D)."""
    if mat.size == 0:
        return 0.0
    sims = mat @ row
    return float(np.max(sims))


def _reject_dedup(item_id, max_sim, source_frame, dedup_path):
    with open(dedup_path, "a") as f:
        f.write(json.dumps({
            "item_id": item_id, "max_sim": round(max_sim, 6),
            "source_frame": source_frame, "ts": _utcnow_iso()}) + "\n")


# --------------------------------------------------------------- the caller

def _run_openrouter(model, prompt, api_key, seed):
    """THIN real OpenRouter caller — the only network code in this module.

    Tests inject `call_fn` and NEVER execute this. Chat-completions POST with
    temperature 0.9, max_tokens 500, deterministic seed.
    """
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9, "max_tokens": 500, "seed": seed}).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"]


# ------------------------------------------------------------ item pipeline

def _utcnow_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _strict_parse(text):
    """Strict parse with one retry: on failure, retry once on the largest
    ```json-fenced block (generators routinely wrap JSON in fences despite
    the no-meta instruction). None on any failure. Never raises."""
    if not isinstance(text, str):
        return None
    try:
        obj = json.loads(text.strip())
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # retry: prefer the LAST fenced block (final answer), else first/last
    # brace pair (nested-brace safe: greedy match from first { to last })
    for candidate in re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S):
        try:
            obj = json.loads(candidate.strip())
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e > s:
        try:
            obj = json.loads(text[s:e + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _verifier_shape_ok(verifier):
    if not isinstance(verifier, dict):
        return False
    if verifier.get("type") not in ("exact_match", "numeric_tol"):
        return False
    value = verifier.get("value")
    if verifier["type"] == "exact_match":
        if not isinstance(value, str) or not value.strip():
            return False
    else:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            return False
    return True


def _self_verifier_ok(item):
    """Generator must pass its OWN verifier on its OWN answer."""
    from verifiers import run_verifier
    return run_verifier(item.get("verifier"), item.get("answer")) is True


def generate_batch(rung, n_items, model, api_key, seed_base, call_fn=None,
                   encode_fn=None, corpus_encode_fn=None):
    """Generate `n_items` candidates for rung `rung`; return accepted items.

    call_fn(model, prompt, api_key, seed) -> response text. Defaults to the
    thin real OpenRouter caller (temperature 0.9, max_tokens 500,
    seed=batch_seed+i); tests inject fakes. encode_fn / corpus_encode_fn
    default to the real bge embedder but are injectable so tests never touch
    the model. Every failure mode is a counted reject; the batch never
    crashes on bad model output.
    """
    if call_fn is None:
        call_fn = _run_openrouter
    if encode_fn is None:
        encode_fn = bge_encode
    if corpus_encode_fn is None:
        corpus_encode_fn = encode_fn

    batch_seed = 1000 + 7919 * rung + seed_base
    batch_id = "r%d_b%d" % (rung, batch_seed)
    os.makedirs(ITEMS_DIR, exist_ok=True)
    items_path = os.path.join(ITEMS_DIR, "items_batch%d.jsonl" % rung)
    dedup_path = os.path.join(ITEMS_DIR, "dedup_log.jsonl")
    rejects_path = os.path.join(ITEMS_DIR, "gen_rejects_batch%d.jsonl" % rung)

    prompts = load_prompt_sources()
    # Corpus index -> source frame via parallel labels; question text from
    # the corpus is used ONLY for embedding, never written to any log.
    corpus_labels, corpus_texts = [], []
    for frame in CORPUS_FRAMES:
        texts = prompts.get(frame) or []
        corpus_texts.extend(texts)
        corpus_labels.extend([frame] * len(texts))

    corpus_mat = (np.asarray(corpus_encode_fn(corpus_texts), dtype=np.float32)
                  if corpus_texts else np.zeros((0, 1), dtype=np.float32))
    accepted, accepted_texts = [], []

    def reject(reason, detail=None):
        with open(rejects_path, "a") as f:
            f.write(json.dumps({"reason": reason, "batch_id": batch_id,
                                "ts": _utcnow_iso(), "detail": detail or ""})
                    + "\n")

    for i in range(n_items):
        seed = batch_seed + i
        try:
            text = call_fn(model, GEN_PROMPT, api_key, seed)
        except Exception:
            reject("exception")
            continue
        item = _strict_parse(text)
        if item is None:
            reject("not_json")
            continue
        missing = [k for k in ("question", "answer", "verifier")
                   if k not in item]
        if missing:
            reject("missing_keys", ",".join(missing))
            continue
        question = item["question"]
        if not isinstance(question, str) or not question.strip():
            reject("empty_question")
            continue
        if not _verifier_shape_ok(item["verifier"]):
            reject("verifier_shape")
            continue
        if not _self_verifier_ok(item):
            reject("self_verifier")
            continue
        item_id = _sha16(question)

        # ---- dedup gate: corpus + in-batch (cosine >= 0.85 reject) ----
        row = np.asarray(encode_fn([question]), dtype=np.float32)[0]
        max_sim, source = _max_cos(row, corpus_mat), None
        if corpus_mat.size:
            source = corpus_labels[int(np.argmax(corpus_mat @ row))]
        if max_sim >= DEDUP_THRESHOLD and source is not None:
            _reject_dedup(item_id, max_sim, source, dedup_path)
            continue
        batch_sim, batch_source = 0.0, "in_batch"
        if accepted_texts:
            acc_mat = np.asarray(encode_fn(accepted_texts), dtype=np.float32)
            batch_sim = _max_cos(row, acc_mat)
        if batch_sim >= DEDUP_THRESHOLD:
            _reject_dedup(item_id, batch_sim, batch_source, dedup_path)
            continue

        row_out = {"item_id": item_id, "question": question,
                   "answer": item["answer"], "verifier": item["verifier"],
                   "gen_model": model, "seed": seed, "batch_id": batch_id,
                   "ts": _utcnow_iso()}
        with open(items_path, "a") as f:
            f.write(json.dumps(row_out) + "\n")
        accepted.append(row_out)
        accepted_texts.append(question)

    return accepted


# ------------------------------------------------------------------ CLI

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        print("usage: generate_items.py --rung N --n N --model ID")
        return 0
    try:
        import argparse
        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument("--rung", type=int, required=True)
        ap.add_argument("--n", type=int, required=True)
        ap.add_argument("--model", required=True)
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    # Spend gate adjacency: the key is required only on the REAL call path.
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("REFUSED: OPENROUTER_API_KEY not set (real generation path "
              "requires a key; no calls were made)", file=sys.stderr)
        return 2
    accepted = generate_batch(rung=args.rung, n_items=args.n,
                              model=args.model, api_key=api_key,
                              seed_base=0)
    print("accepted=%d rejected-see=gen_rejects_batch%d.jsonl"
          % (len(accepted), args.rung))
    return 0


if __name__ == "__main__":
    sys.exit(main())
