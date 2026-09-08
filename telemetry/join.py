"""Deterministic decision↔outcome reconciliation (T032).

Frozen join semantics (LIVE_PREREG section 2; refined supersede rule recorded
in CORRECTION_LOG before the affected tests ran):
- group outcomes by event_id, order by (outcome_ts, outcome_id);
- a row referenced by another row's `supersedes_outcome_id` is dead
  (append-only rows cannot be rewritten, so supersession is by reference);
- finality precedence final > provisional; ties by later ts;
- per-decision status: joined | ambiguous | unjoined;
- orphan: outcome whose event_id has no decision event.
Report rows are emitted per UNIQUE decision event id (duplicate appends of the
same event are one join unit, not two).
"""


def reconcile(decisions, outcomes):
    """Return (join_index, report_rows).

    join_index: {event_id: {"status": str, "outcome": dict|None,
                            "candidates": [outcome...]}}
    report_rows: list of {"event_id", "status"} — one per unique decision id.
    """
    by_event = {}
    for o in outcomes:
        by_event.setdefault(o["event_id"], []).append(o)
    for k in by_event:
        by_event[k].sort(key=lambda o: (o["outcome_ts"], o["outcome_id"]))

    # Append-only supersede semantics: a row referenced by another row's
    # `supersedes_outcome_id` is dead regardless of its stored finality.
    referenced = {o["supersedes_outcome_id"] for o in outcomes
                  if o.get("supersedes_outcome_id")}

    decision_ids = {d["event_id"] for d in decisions}
    join_index = {}
    report_rows = []

    # Orphans: outcomes with no decision event at all.
    for eid in sorted(by_event):
        if eid not in decision_ids:
            join_index[eid] = {"status": "orphan", "outcome": None,
                               "candidates": by_event[eid]}

    # One join unit per UNIQUE decision event id.
    for eid in sorted(decision_ids):
        outs = by_event.get(eid, [])
        if not outs:
            join_index[eid] = {"status": "unjoined", "outcome": None,
                               "candidates": []}
            report_rows.append({"event_id": eid, "status": "unjoined"})
            continue
        live = [o for o in outs
                if o["finality"] != "superseded" and o["outcome_id"] not in referenced]
        finals = [o for o in live if o["finality"] == "final"]
        if len(finals) > 1:
            # Two live finals with no supersession link = contradiction.
            chosen = max(finals, key=lambda o: (o["outcome_ts"], o["outcome_id"]))
            status = "ambiguous"
        elif len(finals) == 1:
            chosen = finals[0]
            status = "joined"
        elif len(live) > 1:
            # multiple provisionals, no final: deterministic pick but flag
            chosen = live[-1]
            status = "ambiguous"
        else:
            chosen = live[0] if live else outs[-1]
            status = "joined"
        join_index[eid] = {"status": status, "outcome": chosen,
                           "candidates": outs}
        report_rows.append({"event_id": eid, "status": status})
    return join_index, report_rows


def join_stats(report_rows):
    from collections import Counter
    c = Counter(r["status"] for r in report_rows)
    return {
        "total_decisions": len(report_rows),
        "joined": c.get("joined", 0),
        "unjoined": c.get("unjoined", 0),
        "ambiguous": c.get("ambiguous", 0),
        "orphans": c.get("orphans", 0),
    }


def compute_join_success_rate(report_rows):
    st = join_stats(report_rows)
    if st["total_decisions"] == 0:
        return 0.0
    return st["joined"] / st["total_decisions"]
