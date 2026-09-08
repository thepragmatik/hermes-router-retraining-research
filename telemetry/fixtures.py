"""Edge-case outcome fixtures for idea 101 (T033).

Builds duplicate / late / provisional-final / contradictory outcome scenarios
against a base decision event, for the join-reconciliation tests (A1-A4).
Prompts here are synthetic strings; only their hashes enter ledgers.
"""

from telemetry.schema import make_decision_event, make_outcome_event

FIXTURE_PROMPTS = [
    "synthetic fixture prompt alpha",
    "synthetic fixture prompt bravo",
    "synthetic fixture prompt charlie",
]


def base_decision(prompt=FIXTURE_PROMPTS[0], session_id="sess-fixture-1",
                  message_id=None):
    return make_decision_event(prompt, confidence=0.42, chosen_action="weak",
                               session_id=session_id, message_id=message_id)


def duplicate_outcomes(d):
    """Same event joined by two rows sharing... same outcome content but
    DISTINCT outcome_ids (a true double-append). Reconciliation must collapse
    them deterministically (later ts wins within equal finality)."""
    o1 = make_outcome_event(d["event_id"], 1.0, finality="final",
                            metadata={"source": "fixture", "fixture": "duplicate"})
    o2 = make_outcome_event(d["event_id"], 1.0, finality="final",
                            metadata={"source": "fixture", "fixture": "duplicate"})
    # Force o2 later so the pick is deterministic.
    o2["outcome_ts"] = "2099-01-01T00:00:00+00:00"
    return [o1, o2]


def late_outcomes(d):
    """A provisional outcome arrives first, a LATE final arrives later (A2):
    must resolve to the final, never reassign to another decision."""
    early = make_outcome_event(d["event_id"], 0.0, finality="provisional",
                               metadata={"source": "fixture", "fixture": "late"})
    late = make_outcome_event(d["event_id"], 1.0, finality="final",
                              metadata={"source": "fixture", "fixture": "late"})
    return [early, late]


def provisional_then_final(d):
    """Provisional superseded by final for the same event (A3)."""
    prov = make_outcome_event(d["event_id"], 0.0, finality="provisional",
                              metadata={"source": "fixture", "fixture": "prov_final"})
    fin = make_outcome_event(d["event_id"], 1.0, finality="final",
                             metadata={"source": "fixture", "fixture": "prov_final"})
    return [prov, fin]


def contradictory_outcomes(d):
    """Two non-superseded finals with different values (A4): status must be
    ambiguous and surfaced in the quality report."""
    f1 = make_outcome_event(d["event_id"], 0.0, finality="final",
                            metadata={"source": "fixture", "fixture": "contradictory"})
    f2 = make_outcome_event(d["event_id"], 1.0, finality="final",
                            metadata={"source": "fixture", "fixture": "contradictory"})
    return [f1, f2]


def superseded_chain(d):
    """final -> superseded -> new final: newest final wins, superseded one is
    linked via supersedes_outcome_id."""
    o1 = make_outcome_event(d["event_id"], 0.0, finality="final",
                            metadata={"source": "fixture", "fixture": "chain"})
    o2 = make_outcome_event(d["event_id"], 1.0, finality="superseded",
                            supersedes_outcome_id=o1["outcome_id"],
                            metadata={"source": "fixture", "fixture": "chain"})
    o3 = make_outcome_event(d["event_id"], 1.0, finality="final",
                            supersedes_outcome_id=o2["outcome_id"],
                            metadata={"source": "fixture", "fixture": "chain"})
    return [o1, o2, o3]
