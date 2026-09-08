#!/usr/bin/env python3
"""Cascade labeler: weak tier first, strong tier ONLY on weak failure.

SPEND-GATED (Task 4b): refuses to run without GEN_GO=1 and a positive
SPEND_CAP_USD; aborts mid-batch as soon as the ledger-driven gate says the
cap is reached. All calls go through the thin real caller `ask` (urllib,
max_tokens 300, temperature 0) — tests monkeypatch it, so the suite makes
zero network calls.

Defaults are the V1-frozen pair (router-contract compatibility). The operator
may override via WEAK_MODEL / STRONG_MODEL env vars for a different cascade
pair; any V2 pair selection must be frozen in GENERATOR_PREREG.md before any
spend occurs.

Ledger rows carry item_id only (never question text). The labels file is
local evidence and may carry question text.
"""
import datetime as _dt
import json
import os
import sys
import urllib.request

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# Defaults = the V1-frozen router pair (weak = mistral-7b-chat class,
# strong = gpt-4-1106-preview class) so labels stay composable with V1's
# frozen point. WEAK_MODEL / STRONG_MODEL env overrides exist for pair
# experiments; V2 pair selection must be frozen in GENERATOR_PREREG.md
# BEFORE any spend.
WEAK = os.environ.get("WEAK_MODEL", "mistralai/mistral-7b-chat")
STRONG = os.environ.get("STRONG_MODEL", "openai/gpt-4-1106-preview")

REPO_DIR = os.path.dirname(os.path.dirname(MODULE_DIR))
EVIDENCE_DIR = os.path.join(REPO_DIR, "evidence", "gen_factory")

from ledger import append as LEDGER_APPEND, batch_spend as BATCH_SPEND
from verifiers import run_verifier, _final_region


def _utcnow_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ANSWER_FORMAT_SUFFIX = (
    "\n\nEnd your reply with a final line of the form "
    "'Final answer: <answer>' where <answer> is only the answer itself."
)


def _payload(model, question):
    """Request body for one labeling call (max_tokens 700 + answer format).

    R1b postmortem root causes 2+3: 300-token cap truncated 31/65 strong
    answers past the final-answer region, and tiers were never asked for a
    machine-checkable final line, so verifiers graded solvable items False.
    """
    return {
        "model": model,
        "messages": [{"role": "user", "content": question + ANSWER_FORMAT_SUFFIX}],
        "max_tokens": 700, "temperature": 0}


def ask(model, question, key, base="https://openrouter.ai/api/v1"):
    """THIN real OpenRouter caller — the only network code here.

    Tests monkeypatch this symbol and never execute it.
    """
    body = json.dumps(_payload(model, question)).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"], d.get("usage", {})


def process_batch(items, labels_path, ask_fn=None, cap_usd=None, key=None):
    """Weak->verifier->(strong iff weak-fail) with per-step ledger rows.

    Aborts (SystemExit) as soon as the ledgered spend for this batch reaches
    cap_usd; the labels file then contains exactly the fully-processed
    prefix. ask_fn is injectable (defaults to the real `ask`); tests inject
    fakes, so no network happens under test.
    """
    if ask_fn is None:
        ask_fn = ask
    if cap_usd is None:
        cap_usd = float(os.environ.get("SPEND_CAP_USD", "0") or 0)
    batch_id = (items[0].get("batch_id") if items else None) or "unknown"
    labels = []
    with open(labels_path, "w") as f:
        pass
    for it in items:
        try:
            ans_w, usage_w = ask_fn(WEAK, it["question"], key)
        except Exception:
            ans_w, usage_w = None, {}
        weak_ok = run_verifier(it["verifier"], ans_w) if ans_w is not None \
            else False
        LEDGER_APPEND(price_row(
            WEAK, usage_w,
            {"stage": "weak", "item_id": it["item_id"],
             "batch_id": it.get("batch_id", batch_id), "weak_ok": weak_ok}))
        strong_ok = None
        if not weak_ok:
            try:
                ans_s, usage_s = ask_fn(STRONG, it["question"], key)
            except Exception:
                ans_s, usage_s = None, {}
            strong_ok = run_verifier(it["verifier"], ans_s) \
                if ans_s is not None else False
            LEDGER_APPEND(price_row(
                STRONG, usage_s,
                {"stage": "strong", "item_id": it["item_id"],
                 "batch_id": it.get("batch_id", batch_id),
                 "weak_ok": weak_ok, "strong_ok": strong_ok}))
        labels.append({
            "item_id": it["item_id"], "question": it["question"],
            "weak_ok": weak_ok, "strong_ok": strong_ok,
            "label": "weak_ok" if weak_ok else "need_strong",
            # R4 auditability (prereg): keep the strong tier's extracted
            # final-answer region on escalation rows so a 0/N rescue rate
            # can be split into "wrong" vs "right-but-formulation-mismatch".
            # Synthetic question/answer text only; capped at 200 chars.
            **({"strong_final": _final_region(ans_s)[:200]}
               if (not weak_ok and ans_s is not None) else {}),
            "ts": _utcnow_iso()})
        with open(labels_path, "a") as f:
            f.write(json.dumps(labels[-1]) + "\n")
        if not BATCH_SPEND(cap_usd, it.get("batch_id", batch_id)):
            sys.exit("ABORT: spend cap %.4f reached for batch %s "
                     "(labels file holds the processed prefix only)"
                     % (cap_usd, it.get("batch_id", batch_id)))
    return labels


def price_row(model, usage, base_row):
    from ledger import price_row
    return price_row(model, usage, base_row)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("GEN_GO") != "1":
        sys.exit("REFUSED: GEN_GO=1 required (spend gate); nothing ran")
    cap = float(os.environ.get("SPEND_CAP_USD", "0") or 0)
    if cap <= 0:
        sys.exit("REFUSED: SPEND_CAP_USD must be > 0 (spend gate); nothing ran")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("REFUSED: OPENROUTER_API_KEY not set; nothing ran")
    if len(argv) != 1:
        print("usage: cascade_label.py ITEMS_BATCH.jsonl", file=sys.stderr)
        return 2
    items_path = argv[0]
    with open(items_path) as f:
        items = [json.loads(ln) for ln in f if ln.strip()]
    rung = "".join(ch for ch in os.path.basename(items_path) if ch.isdigit()) \
        or "X"
    labels_path = os.path.join(EVIDENCE_DIR, "labels_batch%s.jsonl" % rung)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    process_batch(items, labels_path, cap_usd=cap, key=key)
    print("labels ->", labels_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
