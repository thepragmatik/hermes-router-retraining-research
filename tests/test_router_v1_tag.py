"""Frozen-reference drift guard for Router V1.

router_v1/ is read-only (see router_v1/PROVENANCE.md). If these hashes change,
someone modified the frozen V1 reference; that invalidates every downstream
ablation that cites tag router-v1-frozen.
"""
import hashlib
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

MF_SHA = "db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7"
ROUTE_SHA = "b9fa430d300e3a1693f6bedfad51926a20a5192ebd46a4dfd07d6a877a8aeb46"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_checkpoint_matches_recorded_hash():
    assert _sha(ROOT / "router_v1" / "mf_router.pt") == MF_SHA


def test_route_py_matches_recorded_hash():
    assert _sha(ROOT / "router_v1" / "route.py") == ROUTE_SHA


def test_provenance_records_the_hashes():
    text = (ROOT / "router_v1" / "PROVENANCE.md").read_text()
    assert MF_SHA in text
