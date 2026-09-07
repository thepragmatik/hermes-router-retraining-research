#!/usr/bin/env python3
"""$0: distinct seed_base values must yield distinct batch ids (R1b lesson:
bare seed collided across reruns, forcing a ts-filter split in the report)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "gen_factory"))
from generate_items import _batch_id


def test_batch_id_distinguishes_reruns():
    assert _batch_id(1, 0) != _batch_id(1, 1759270000)
    assert _batch_id(1, 12345) != _batch_id(2, 12345)
