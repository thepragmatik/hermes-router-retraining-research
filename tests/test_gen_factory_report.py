"""RED-first tests for the ledger report (Task 5, $/usable-label aggregates).

The report is the ONLY decision metric: cost per usable label from ledger
rows. Tests use tmp_path fixtures with tiny synthetic ledger/labels/items
files; zero network, zero repo-evidence mutation. Costs in fixtures are
exact dyadic floats (0.0625/0.125/0.25/0.5) so aggregate sums and divisions
are EXACT in IEEE-754 — no approx anywhere.
"""
import json, os, sys
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "experiments", "gen_factory")
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import ledger_report as lr  # noqa: E402


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def row(stage, cost, item_id, batch_id="r1_b1", **kw):
    r = {"stage": stage, "model": "m/x", "batch_id": batch_id,
         "item_id": item_id, "est_cost_usd": cost,
         "ts": "2026-09-07T00:00:00Z"}
    r.update(kw)
    return r


def four_row_ledger(d):
    """Known 4-row cascade ledger, batch r1_b1:
    weak pass it1 0.25 | weak fail it2 0.5 | strong pass it2 0.125 |
    weak fail it3 0.0625 (no strong row -> both-fail stratum).
    total = 0.9375 EXACT (dyadic floats); labeled 3."""
    write_jsonl(os.path.join(d, "ledger.jsonl"), [
        row("weak", 0.25, "it1", weak_ok=True),
        row("weak", 0.5, "it2", weak_ok=False),
        row("strong", 0.125, "it2", weak_ok=False, strong_ok=True),
        row("weak", 0.0625, "it3", weak_ok=False),
    ])


# ------------------------------------------------------- no_data path

def test_no_data_missing_inputs_all_zeros(tmp_path):
    rep = lr.build_report(str(tmp_path))
    assert rep["status"] == "no_data"
    t = rep["rung_totals"]
    assert t["n_labeled"] == 0
    assert t["n_generated"] == 0
    assert t["total_est_cost_usd"] == 0.0
    assert t["cost_per_usable_label_usd"] == 0.0
    assert t["cost_per_weak_ok_usd"] == 0.0
    assert t["unpriced_call_count"] == 0
    assert rep["batches"] == {} and rep["rungs"] == {}


def test_no_data_empty_ledger_file(tmp_path):
    open(os.path.join(str(tmp_path), "ledger.jsonl"), "w").close()
    rep = lr.build_report(str(tmp_path))
    assert rep["status"] == "no_data"
    assert rep["rung_totals"]["n_generated"] == 0


# --------------------------------- known 4-row ledger: exact aggregates

def test_four_row_ledger_exact_aggregates(tmp_path):
    four_row_ledger(str(tmp_path))
    rep = lr.build_report(str(tmp_path))
    assert rep["status"] == "ok"
    t = rep["rung_totals"]
    assert t["n_labeled"] == 3
    assert t["weak_ok_count"] == 1
    assert t["need_strong_count"] == 1
    assert t["both_fail_count"] == 1
    assert t["strong_calls_made"] == 1
    assert t["total_est_cost_usd"] == 0.9375
    assert t["cost_per_usable_label_usd"] == 0.3125
    assert t["cost_per_weak_ok_usd"] == 0.9375
    assert t["unpriced_call_count"] == 0
    # strata partition: weak_ok + need_strong + both_fail == n_labeled
    assert t["weak_ok_count"] + t["need_strong_count"] \
        + t["both_fail_count"] == t["n_labeled"]


def test_multi_batch_grouping_exact(tmp_path):
    d = str(tmp_path)
    write_jsonl(os.path.join(d, "ledger.jsonl"), [
        # batch r1_b1: 2 labels, 1 weak_ok, 1 need_strong
        row("weak", 0.25, "it1", batch_id="r1_b1", weak_ok=True),
        row("weak", 0.5, "it2", batch_id="r1_b1", weak_ok=False),
        row("strong", 0.125, "it2", batch_id="r1_b1", weak_ok=False,
            strong_ok=True),
        # batch r2_b1: 1 label, weak fails AND strong fails -> both-fail
        row("weak", 0.5, "it4", batch_id="r2_b1", weak_ok=False),
        row("strong", 0.0625, "it4", batch_id="r2_b1", weak_ok=False,
            strong_ok=False),
    ])
    rep = lr.build_report(d)
    b1 = rep["batches"]["r1_b1"]
    assert b1["n_labeled"] == 2
    assert b1["weak_ok_count"] == 1
    assert b1["need_strong_count"] == 1
    assert b1["total_est_cost_usd"] == 0.875
    assert b1["cost_per_usable_label_usd"] == 0.4375
    b2 = rep["batches"]["r2_b1"]
    assert b2["n_labeled"] == 1
    assert b2["need_strong_count"] == 0
    assert b2["both_fail_count"] == 1
    assert b2["total_est_cost_usd"] == 0.5625
    # per-rung: rung = sum of its batches
    assert rep["rungs"]["r1"]["total_est_cost_usd"] == 0.875
    assert rep["rungs"]["r1"]["need_strong_count"] == 1
    assert rep["rungs"]["r2"]["total_est_cost_usd"] == 0.5625
    assert rep["rungs"]["r2"]["both_fail_count"] == 1
    t = rep["rung_totals"]
    assert t["n_labeled"] == 3
    assert t["total_est_cost_usd"] == 1.4375
    assert t["strong_calls_made"] == 2


# ------------------------------------ cost_per_usable_label division

def test_cost_per_usable_label_division_correctness(tmp_path):
    """5 weak rows all weak_ok at 0.5 -> total 2.5, /5 = 0.5 EXACT."""
    d = str(tmp_path)
    write_jsonl(os.path.join(d, "ledger.jsonl"),
                [row("weak", 0.5, "it%d" % i, weak_ok=True)
                 for i in range(5)])
    t = lr.build_report(d)["rung_totals"]
    assert t["n_labeled"] == 5
    assert t["weak_ok_count"] == 5
    assert t["total_est_cost_usd"] == 2.5
    assert t["cost_per_usable_label_usd"] == 0.5
    assert t["cost_per_weak_ok_usd"] == 0.5


def test_division_by_zero_n_labeled_gives_zero_not_crash(tmp_path):
    """Only 'log' rows (no labeling) -> cost fields 0.0, no crash."""
    d = str(tmp_path)
    write_jsonl(os.path.join(d, "ledger.jsonl"),
                [row("log", 0.25, "it1")])
    t = lr.build_report(d)["rung_totals"]
    assert t["n_labeled"] == 0
    assert t["total_est_cost_usd"] == 0.25
    assert t["cost_per_usable_label_usd"] == 0.0
    assert t["cost_per_weak_ok_usd"] == 0.0


# -------------------------------------------- unpriced rows: count only

def test_unpriced_rows_counted_not_crashed(tmp_path):
    d = str(tmp_path)
    write_jsonl(os.path.join(d, "ledger.jsonl"), [
        row("weak", 0.25, "it1", weak_ok=True),
        row("weak", 0.0, "it2", weak_ok=False, unpriced=True),
        row("strong", 0.125, "it2", weak_ok=False, strong_ok=True),
    ])
    t = lr.build_report(d)["rung_totals"]
    assert t["unpriced_call_count"] == 1
    assert t["n_labeled"] == 2
    assert t["need_strong_count"] == 1
    # unpriced row's est_cost (0.0) contributes nothing; math stays exact
    assert t["total_est_cost_usd"] == 0.375
    assert t["cost_per_usable_label_usd"] == 0.1875


# ------------------------------------------- generator-side funnel fields

def test_funnel_files_counted_cost_math_untouched(tmp_path):
    d = str(tmp_path)
    four_row_ledger(d)
    write_jsonl(os.path.join(d, "items_batch1.jsonl"),
                [{"item_id": "acc1"}, {"item_id": "acc2"},
                 {"item_id": "acc3"}])
    write_jsonl(os.path.join(d, "gen_rejects_batch1.jsonl"), [
        {"reason": "not_json"}, {"reason": "missing_keys"},
        {"reason": "verifier_shape"}, {"reason": "self_verifier"}])
    write_jsonl(os.path.join(d, "dedup_log.jsonl"),
                [{"item_id": "dup1", "max_sim": 0.9}])
    write_jsonl(os.path.join(d, "labels_batch1.jsonl"),
                [{"item_id": "acc1", "label": "weak_ok"},
                 {"item_id": "acc2", "label": "need_strong"}])
    rep = lr.build_report(d)
    t = rep["rung_totals"]
    assert t["n_items_accepted"] == 3
    assert t["n_parse_rejected"] == 3          # not_json/missing/shape
    assert t["n_other_gen_rejected"] == 1      # self_verifier
    assert t["n_dedup_rejected"] == 1
    assert t["n_labels_written"] == 2
    assert t["n_generated"] == 3 + 4 + 1
    # funnel files are rung-tagged by filename
    assert rep["rungs"]["r1"]["n_generated"] == 8
    assert rep["rungs"]["r1"]["n_dedup_rejected"] == 1
    # cost math untouched by generator-side files (ledger rows only)
    assert t["total_est_cost_usd"] == 0.9375
    assert t["n_labeled"] == 3
    assert t["cost_per_usable_label_usd"] == 0.3125


def test_malformed_ledger_lines_skipped_never_crash(tmp_path):
    d = str(tmp_path)
    with open(os.path.join(d, "ledger.jsonl"), "w") as f:
        f.write("{not json at all\n")
        f.write("\n")
        f.write(json.dumps(row("weak", 0.25, "it1", weak_ok=True)) + "\n")
    t = lr.build_report(d)["rung_totals"]
    assert t["n_labeled"] == 1
    assert t["total_est_cost_usd"] == 0.25
    assert t["cost_per_usable_label_usd"] == 0.25


# ---------------------------------------------------------- file outputs

def test_main_writes_json_and_md_reports(tmp_path):
    d = str(tmp_path)
    four_row_ledger(d)
    rc = lr.main(["--evidence", d])
    assert rc == 0
    rep = json.load(open(os.path.join(d, "ledger_report.json")))
    assert rep["status"] == "ok"
    assert rep["rung_totals"]["cost_per_usable_label_usd"] == 0.3125
    assert rep["rungs"]["r1"]["n_labeled"] == 3
    assert rep["batches"]["r1_b1"]["total_est_cost_usd"] == 0.9375
    md = open(os.path.join(d, "ledger_report.md")).read()
    assert "cost_per_usable_label_usd" in md
    assert "0.3125" in md
    assert "0.9375" in md
    assert "r1" in md
    assert "r1_b1" in md


def test_main_no_data_writes_zero_report(tmp_path):
    d = str(tmp_path)
    rc = lr.main(["--evidence", d])
    assert rc == 0
    rep = json.load(open(os.path.join(d, "ledger_report.json")))
    assert rep["status"] == "no_data"
    assert rep["rung_totals"]["n_labeled"] == 0
    assert rep["rung_totals"]["cost_per_usable_label_usd"] == 0.0
    md = open(os.path.join(d, "ledger_report.md")).read()
    assert "no_data" in md
