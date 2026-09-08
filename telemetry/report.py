"""Data-quality report for the telemetry ledgers (T035).

Reports exactly the spec/task dimensions: unique ids, missing provenance
(action/model/router version), missing propensity on randomized events,
unjoined outcomes, ambiguous joins, schema drift (quarantined rows).
"""
import os
import re
from collections import Counter

from telemetry.decision_log import DECISIONS_FILENAME, read_decisions
from telemetry.join import join_stats, reconcile
from telemetry.outcome_log import OUTCOMES_FILENAME, read_outcomes

DEFAULT_LOG_DIR = os.path.join("evidence", "telemetry")

# Any prompt-TEXT-shaped key in a ledger line is a leak by definition.
_PROMPT_TEXT_KEY_RE = re.compile(
    r'"(prompt|prompt_text|text|raw_prompt|body|message)"\s*:')


def build_quality_report(log_dir=None):
    """Return the machine-readable quality report dict (T035/T044)."""
    log_dir = os.path.abspath(log_dir or DEFAULT_LOG_DIR)
    decisions_path = os.path.join(log_dir, DECISIONS_FILENAME)
    outcomes_path = os.path.join(log_dir, OUTCOMES_FILENAME)

    dq_quar, oq_quar = [], []
    decisions, _ = read_decisions(decisions_path, quarantine=dq_quar)
    outcomes, _ = read_outcomes(outcomes_path, quarantine=oq_quar)

    n = len(decisions)
    ids = [d["event_id"] for d in decisions]
    unique_ids = len(set(ids))
    unique_share = (unique_ids / n) if n else 0.0

    # Provenance: action/model/router version presence on every record.
    missing_provenance = 0
    for d in decisions:
        ok = (
            d.get("router_id") and d.get("router_version")
            and d.get("chosen_action")
            and isinstance(d.get("model_provider_revision"), dict)
            and all(k in d["model_provider_revision"] for k in ("weak", "strong"))
        )
        missing_provenance += 0 if ok else 1

    # Propensities on randomized events.
    randomized = [d for d in decisions
                  if d.get("exploration_mode") in ("shadow_dual", "randomized_sentinel")]
    missing_propensity = sum(
        1 for d in randomized
        if d.get("chosen_propensity") is None
        or not (0.0 < float(d["chosen_propensity"]) <= 1.0))
    prop_share = ((len(randomized) - missing_propensity) / len(randomized)) if randomized else 1.0

    # Joins.
    join_index, report_rows = reconcile(decisions, outcomes)
    st = join_stats(report_rows)
    ambiguous = [r["event_id"] for r in report_rows if r["status"] == "ambiguous"]
    orphan_count = sum(1 for v in join_index.values() if v["status"] == "orphan")
    join_rate = st["joined"] / n if n else 0.0

    # Prompt-text scan over the LEDGER SURFACES (files on disk).
    prompt_text_hits = scan_prompt_text_hits(decisions_path, outcomes_path)

    return {
        "log_dir": log_dir,
        "total_decisions": n,
        "total_outcomes": len(outcomes),
        "unique_event_ids": unique_ids,
        "unique_share": unique_share,
        "duplicate_ids": n - unique_ids,
        "missing_provenance": missing_provenance,
        "randomized_events": len(randomized),
        "missing_propensity_on_randomized": missing_propensity,
        "propensity_share_on_randomized": prop_share,
        "joined": st["joined"],
        "unjoined": st["unjoined"],
        "ambiguous_joins": len(ambiguous),
        "ambiguous_event_ids": ambiguous,
        "orphan_outcomes": orphan_count,
        "join_success_rate": join_rate,
        "schema_drift_quarantined": {
            "decisions": len(dq_quar), "outcomes": len(oq_quar)},
        "schema_drift_examples": {
            "decisions": dq_quar[:5], "outcomes": oq_quar[:5]},
        "prompt_text_hits": prompt_text_hits,
    }


def scan_prompt_text_hits(decisions_path, outcomes_path):
    """Scan ledger files for prompt-text-shaped JSON keys (defence in depth —
    raw text must never be written by construction, T034/A5)."""
    hits = []
    for path in (decisions_path, outcomes_path):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                for m in _PROMPT_TEXT_KEY_RE.finditer(line):
                    hits.append({"file": os.path.basename(path), "line_no": ln,
                                 "key": m.group(1)})
    return hits


def main():
    """CLI entry (T035): python3 -m telemetry.report [log_dir]"""
    import json
    import sys
    log_dir = sys.argv[1] if len(sys.argv) > 1 else None
    rep = build_quality_report(log_dir)
    print(json.dumps(rep, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
