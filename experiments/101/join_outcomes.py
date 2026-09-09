#!/usr/bin/env python3
"""Decision<->outcome join summary for idea-101 outcome capture (read-only).

Joins the local-only ledgers (evidence/telemetry/decisions.jsonl and
outcomes.jsonl) on event_id and prints a summary to STDOUT (no file writes
unless --out is given). Frozen contract: results/101/OUTCOME_CAPTURE_PREREG.md.

Stdlib only. Read-only on both ledgers; corrupt rows are skipped, never fatal.

Sections:
  - counts: n_decisions, n_outcomes, join_rate, orphan_outcomes
  - outcome breakdown by chosen_action (decision ledger) and by outcome value
  - avg cost by chosen_action (rows carrying cost only; "-" when none)
  - join-readiness: fraction of decisions with null session_id_hash /
    message_id_hash; WARNING line when either fraction > 0.20 (frozen
    threshold) so operators see id-hygiene problems at a glance.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from telemetry.schema import ACCEPTED_SCHEMA_VERSIONS  # noqa: E402

WARN_THRESHOLD = 0.20  # frozen: warn when >20% of decisions lack an id hash


def read_jsonl(path):
    """Read a JSONL ledger read-only; skip blank/corrupt lines."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.read().splitlines():
            if not raw.strip():
                continue
            try:
                rows.append(json.loads(raw))
            except ValueError:
                continue
    return rows


def summarize(decisions, outcomes):
    """Build the frozen summary dict from decision/outcome rows."""
    n_dec = len(decisions)
    n_out = len(outcomes)
    dec_ids = {d.get("event_id") for d in decisions}
    joined = [o for o in outcomes if o.get("event_id") in dec_ids]
    orphans = [o for o in outcomes if o.get("event_id") not in dec_ids]
    join_rate = (len(joined) / n_out) if n_out else 0.0

    dec_by_id = {d.get("event_id"): d for d in decisions}

    by_action = {}
    cost_sum, cost_n = {}, {}
    for o in joined:
        d = dec_by_id.get(o.get("event_id")) or {}
        act = d.get("chosen_action", "unknown")
        ov = o.get("outcome", "unknown")
        by_action.setdefault(act, {}).setdefault(ov, 0)
        by_action[act][ov] += 1
        c = o.get("cost")
        if isinstance(c, (int, float)):
            cost_sum[act] = cost_sum.get(act, 0.0) + float(c)
            cost_n[act] = cost_n.get(act, 0) + 1
    avg_cost = {a: (round(cost_sum[a] / cost_n[a], 6) if cost_n.get(a) else None)
                for a in sorted(set(list(cost_n) + list(by_action)))}

    null_sid = sum(1 for d in decisions if d.get("session_id_hash") is None)
    null_mid = sum(1 for d in decisions if d.get("message_id_hash") is None)
    frac_sid = (null_sid / n_dec) if n_dec else 0.0
    frac_mid = (null_mid / n_dec) if n_dec else 0.0

    return {
        "n_decisions": n_dec,
        "n_outcomes": n_out,
        "joined_outcomes": len(joined),
        "join_rate": round(join_rate, 4),
        "orphan_outcomes": len(orphans),
        "breakdown_by_chosen_action": by_action,
        "avg_cost_by_chosen_action": avg_cost,
        "null_session_id_hash_frac": round(frac_sid, 4),
        "null_message_id_hash_frac": round(frac_mid, 4),
    }


def render(summary):
    lines = []
    lines.append(f"n_decisions: {summary['n_decisions']}")
    lines.append(f"n_outcomes: {summary['n_outcomes']}")
    lines.append(f"joined_outcomes: {summary['joined_outcomes']}")
    lines.append(f"join_rate: {summary['join_rate']}")
    lines.append(f"orphan_outcomes: {summary['orphan_outcomes']}")
    lines.append("outcome_breakdown_by_chosen_action:")
    if not summary["breakdown_by_chosen_action"]:
        lines.append("  (no joined outcomes)")
    for act in sorted(summary["breakdown_by_chosen_action"]):
        for ov, cnt in sorted(summary["breakdown_by_chosen_action"][act].items()):
            lines.append(f"  {act}/{ov}: {cnt}")
    lines.append("avg_cost_by_chosen_action:")
    for act, v in summary["avg_cost_by_chosen_action"].items():
        lines.append(f"  {act}: {'-' if v is None else v}")
    lines.append("join_readiness:")
    lines.append(f"  null_session_id_hash_frac: "
                 f"{summary['null_session_id_hash_frac']:.2f}")
    lines.append(f"  null_message_id_hash_frac: "
                 f"{summary['null_message_id_hash_frac']:.2f}")
    if (summary["n_decisions"] and
            (summary["null_session_id_hash_frac"] > WARN_THRESHOLD or
             summary["null_message_id_hash_frac"] > WARN_THRESHOLD)):
        lines.append(
            f"  WARNING: >{WARN_THRESHOLD:.0%} of decisions lack a caller id "
            f"hash (session_id/message_id omitted by callers); outcomes on "
            f"those rows cannot be joined by caller identity — fix upstream "
            f"id supply, not the ledger.")
    return "\n".join(lines)


def _self_test():
    """Tiny built-in fixtures; asserts frozen summary values. Exit 0 on pass."""
    decs = [
        {"schema_version": "1.1.0", "event_id": "a" * 32, "chosen_action": "weak",
         "session_id_hash": None, "message_id_hash": None},
        {"schema_version": "1.1.0", "event_id": "b" * 32, "chosen_action": "strong",
         "session_id_hash": "s1", "message_id_hash": "m1"},
    ]
    outs = [
        {"event_id": "a" * 32, "outcome": "success", "cost": 0.01},
        {"event_id": "b" * 32, "outcome": "failure"},
        {"event_id": "c" * 32, "outcome": "timeout"},  # orphan
    ]
    s = summarize(decs, outs)
    assert s["n_decisions"] == 2 and s["n_outcomes"] == 3
    assert s["join_rate"] == round(2 / 3, 4), s
    assert s["orphan_outcomes"] == 1
    assert s["breakdown_by_chosen_action"]["weak"] == {"success": 1}
    assert s["breakdown_by_chosen_action"]["strong"] == {"failure": 1}
    assert s["avg_cost_by_chosen_action"]["weak"] == 0.01
    assert s["avg_cost_by_chosen_action"]["strong"] is None
    assert s["null_session_id_hash_frac"] == 0.5
    text = render(s)
    assert "WARNING" in text  # 50% > 20% threshold
    print("self-test OK")
    print(text)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decisions",
                    default=os.path.join(REPO, "evidence", "telemetry",
                                         "decisions.jsonl"))
    ap.add_argument("--outcomes",
                    default=os.path.join(REPO, "evidence", "telemetry",
                                         "outcomes.jsonl"))
    ap.add_argument("--out", default=None,
                    help="optional path to also write the summary (stdout is "
                         "always the primary output)")
    ap.add_argument("--self-test", action="store_true",
                    help="run built-in fixtures and exit")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    decisions = read_jsonl(args.decisions)
    outcomes = read_jsonl(args.outcomes)
    summary = summarize(decisions, outcomes)
    text = render(summary)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
