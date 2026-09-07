#!/usr/bin/env python3
"""Ledger report — $/usable-label unit economics (Task 5, $0).

THE decision metric for the generator pivot: cost per usable label,
computed ONLY from ledger rows (evidence/gen_factory/ledger.jsonl).
Generator-side files (items_batch*.jsonl, gen_rejects_batch*.jsonl,
dedup_log.jsonl, labels_batch*.jsonl) refine the funnel counters
(n_generated, rejects, dedup, labels written) but NEVER contribute cost:
every dollar in this report is a sum of ledger est_cost_usd. No token
counts are estimated outside the ledger — an unledgered call does not
exist here, and an unpriced ledger row is counted (unpriced_call_count)
with its zero est_cost, never silently dropped.

Strata per batch/rung (partition of n_labeled):
  weak_ok_count      weak row passed its verifier
  need_strong_count  weak failed AND the item's strong row passed
  both_fail_count    weak failed AND (no strong row OR strong failed)
  weak_ok + need_strong + both_fail == n_labeled

cost_per_usable_label_usd = total_est_cost_usd / n_labeled   (0.0 if none)
cost_per_weak_ok_usd      = total_est_cost_usd / weak_ok_count (0.0 if none)

CLI: /usr/bin/python3 experiments/gen_factory/ledger_report.py
     [--evidence DIR]  -> writes ledger_report.json + ledger_report.md
Empty/missing inputs -> zeros report with status "no_data"; malformed
JSONL lines are skipped. Never raises on bad input.
"""
import argparse
import glob as _glob
import json
import os
import re
import sys

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(MODULE_DIR))
EVIDENCE_DIR = os.path.join(REPO_DIR, "evidence", "gen_factory")

PARSE_REJECT_REASONS = {"not_json", "missing_keys", "verifier_shape",
                        "empty_question", "exception"}

RUNG_RE = re.compile(r"^r(\d+)_b")

_COST_KEYS = ("total_est_cost_usd", "cost_per_usable_label_usd",
              "cost_per_weak_ok_usd")


def _blank():
    return {
        "n_generated": 0, "n_items_accepted": 0, "n_parse_rejected": 0,
        "n_other_gen_rejected": 0, "n_dedup_rejected": 0,
        "n_labels_written": 0,
        "n_labeled": 0, "weak_ok_count": 0, "need_strong_count": 0,
        "both_fail_count": 0, "strong_calls_made": 0,
        "total_est_cost_usd": 0.0, "cost_per_usable_label_usd": 0.0,
        "cost_per_weak_ok_usd": 0.0, "unpriced_call_count": 0,
    }


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue
    return rows


def _rung_of(batch_id):
    m = RUNG_RE.match(str(batch_id or ""))
    return ("r" + m.group(1)) if m else None


def _add_cost(slot, cost, unpriced):
    slot["total_est_cost_usd"] += cost
    if unpriced:
        slot["unpriced_call_count"] += 1


def _finalize(t):
    t["cost_per_usable_label_usd"] = \
        (t["total_est_cost_usd"] / t["n_labeled"]) if t["n_labeled"] else 0.0
    t["cost_per_weak_ok_usd"] = \
        (t["total_est_cost_usd"] / t["weak_ok_count"]) \
        if t["weak_ok_count"] else 0.0
    return t


def build_report(evidence_dir):
    """Build the report dict from files in evidence_dir. Never raises."""
    ev = str(evidence_dir)
    agg = {
        "status": "ok", "evidence_dir": os.path.abspath(ev),
        "batches": {}, "rungs": {}, "rung_totals": _blank(),
        "labels_files_local_only": True,
    }

    ledger = _read_jsonl(os.path.join(ev, "ledger.jsonl"))

    # ---- pass 1: per-item outcome sets for cascade strata ----
    weak_rows, strong_pass = [], set()
    for r in ledger:
        try:
            stage = str(r.get("stage") or "")
        except Exception:
            continue
        if stage == "weak":
            weak_rows.append(r)
        elif stage == "strong" and r.get("strong_ok") is True:
            item = r.get("item_id")
            if item:
                strong_pass.add(item)
    weak_items = {r.get("item_id") for r in weak_rows}

    # ---- pass 2: every ledgered row contributes cost exactly once;
    # weak rows drive n_labeled + strata; strong rows drive call count ----
    for r in ledger:
        try:
            stage = str(r.get("stage") or "")
            batch_id = str(r.get("batch_id") or "unknown")
            cost = float(r.get("est_cost_usd") or 0.0)
        except Exception:
            continue
        unpriced = bool(r.get("unpriced"))
        b = agg["batches"].setdefault(batch_id, _blank())
        rung = _rung_of(batch_id) or "unknown_rung"
        rt = agg["rungs"].setdefault(rung, _blank())
        for slot in (b, rt, agg["rung_totals"]):
            _add_cost(slot, cost, unpriced)
            if stage == "weak":
                slot["n_labeled"] += 1
                if r.get("weak_ok") is True:
                    slot["weak_ok_count"] += 1
                elif r.get("item_id") and r.get("item_id") in strong_pass:
                    slot["need_strong_count"] += 1
                else:
                    slot["both_fail_count"] += 1
            elif stage == "strong":
                slot["strong_calls_made"] += 1

    # ---- generator-side funnel counters (no cost content) ----
    funnel = {
        "items": _glob.glob(os.path.join(ev, "items_batch*.jsonl")),
        "rejects": _glob.glob(os.path.join(ev, "gen_rejects_batch*.jsonl")),
    }
    items_n = sum(len(_read_jsonl(p)) for p in funnel["items"])
    rej_rows = [x for p in funnel["rejects"] for x in _read_jsonl(p)]
    parse_rj = sum(1 for x in rej_rows
                   if str(x.get("reason") or "") in PARSE_REJECT_REASONS)
    other_rj = len(rej_rows) - parse_rj
    dedup_n = len(_read_jsonl(os.path.join(ev, "dedup_log.jsonl")))
    labels_n = sum(len(_read_jsonl(p)) for p in
                   _glob.glob(os.path.join(ev, "labels_batch*.jsonl")))
    gen_files_present = bool(funnel["items"] or funnel["rejects"]
                             or dedup_n or labels_n)
    if gen_files_present:
        t = agg["rung_totals"]
        t["n_items_accepted"] += items_n
        t["n_parse_rejected"] += parse_rj
        t["n_other_gen_rejected"] += other_rj
        t["n_dedup_rejected"] += dedup_n
        t["n_labels_written"] += labels_n
        t["n_generated"] += items_n + len(rej_rows) + dedup_n
        # funnel files carry the rung in their filename; attach there
        for p in funnel["items"] + funnel["rejects"]:
            m = re.search(r"batch(\d+)", os.path.basename(p))
            rung = ("r" + m.group(1)) if m else None
            if rung and rung in agg["rungs"]:
                n = len(_read_jsonl(p))
                slot = agg["rungs"][rung]
                slot["n_generated"] += n
                if p in funnel["items"]:
                    slot["n_items_accepted"] += n
                else:
                    parse = sum(1 for x in _read_jsonl(p)
                                if str(x.get("reason") or "")
                                in PARSE_REJECT_REASONS)
                    slot["n_parse_rejected"] += parse
                    slot["n_other_gen_rejected"] += n - parse
        if dedup_n:
            # dedup log is rung-wide; attach to the earliest rung present
            rung = sorted(agg["rungs"].keys())[0] if agg["rungs"] else None
            if rung:
                agg["rungs"][rung]["n_generated"] += dedup_n
                agg["rungs"][rung]["n_dedup_rejected"] += dedup_n

    _finalize(agg["rung_totals"])
    for b in agg["batches"].values():
        _finalize(b)
    for rt in agg["rungs"].values():
        _finalize(rt)

    if not ledger and not gen_files_present:
        agg["status"] = "no_data"
    return agg


# --------------------------------------------------------------- output

def _fmt_cost(x):
    s = "%.8f" % float(x)
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def report_md(rep):
    lines = [
        "# gen_factory ledger report — $/usable-label",
        "",
        "Decision metric: `cost_per_usable_label_usd` (total ledgered cost",
        "divided by labels produced). All cost math from ledger rows only;",
        "both-fail items are labeled separately, never as weak_ok.",
        "",
        "## Rung totals (status: %s)" % rep["status"],
        "",
        "| metric | value |",
        "|---|---|",
    ]
    t = rep["rung_totals"]
    for k in ["n_generated", "n_items_accepted", "n_parse_rejected",
              "n_other_gen_rejected", "n_dedup_rejected",
              "n_labels_written", "n_labeled", "weak_ok_count",
              "need_strong_count", "both_fail_count", "strong_calls_made",
              "total_est_cost_usd", "cost_per_usable_label_usd",
              "cost_per_weak_ok_usd", "unpriced_call_count"]:
        v = t.get(k, 0)
        if k in _COST_KEYS:
            lines.append("| %s | %s |" % (k, _fmt_cost(v)))
        else:
            lines.append("| %s | %s |" % (k, v))
    lines.append("")

    head = ("| %s | n_labeled | weak_ok | need_strong | both_fail | "
            "strong_calls | total_est_cost_usd | "
            "cost_per_usable_label_usd |")
    sep = "|---|---|---|---|---|---|---|---|"
    for title, mapping in (("Per batch", agg_batches(rep)),
                           ("Per rung", agg_rungs(rep))):
        if not mapping:
            continue
        lines += ["## " + title, "", head % "id", sep, ""]
        for key in sorted(mapping):
            b = mapping[key]
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                key, b["n_labeled"], b["weak_ok_count"],
                b["need_strong_count"], b["both_fail_count"],
                b["strong_calls_made"], _fmt_cost(b["total_est_cost_usd"]),
                _fmt_cost(b["cost_per_usable_label_usd"])))
        lines.append("")
    return "\n".join(lines)


def agg_batches(rep):
    return rep["batches"]


def agg_rungs(rep):
    return rep["rungs"]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--evidence", default=EVIDENCE_DIR)
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    ev = args.evidence or EVIDENCE_DIR
    os.makedirs(ev, exist_ok=True)
    rep = build_report(ev)
    json_path = os.path.join(ev, "ledger_report.json")
    md_path = os.path.join(ev, "ledger_report.md")
    with open(json_path, "w") as f:
        json.dump(rep, f, indent=1)
        f.write("\n")
    with open(md_path, "w") as f:
        f.write(report_md(rep))
    print("ledger report -> %s (%s)" % (json_path, rep["status"]))
    print("ledger report -> %s" % md_path)
    if rep["status"] == "no_data":
        print("no_data: nothing to report (all zeros)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
