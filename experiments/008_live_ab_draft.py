#!/usr/bin/env python3
"""DRAFT — SPEND_GO-gated live A/B. Created by Task 9 (2026-09-06). NEVER RUN.

This file is committed as a DRAFT only. It has NEVER been executed against an
API (zero spend to date) and must stay that way until ALL of the following hold:
  1. Prereg 008 exists (evidence/ab/live_ab_prereg.md) and freezes: prompt
     source + sampling seed, judge model + judge prompt, n, budget cap,
     acceptance gates, and the analysis script — BEFORE any call is made.
  2. SPEND_GO=1 is set in the environment (explicit human spend approval).
  3. --approve-spend is passed on the command line (belt and braces).

Design (to be frozen by prereg 008, not by this file):
  Paired live A/B on fresh unseen prompts (train-derived, disjoint from the
  3626-row val frame and from the sealed test frame). Every prompt is sent to
  BOTH tiers (weak and strong) so the comparison is paired; the router@0.30
  decision is computed live per prompt (the val decision cache does NOT apply
  to new prompts). Primary endpoint mirrors prereg 007 H1: acc(router) -
  acc(always-weak), paired bootstrap CI. Hard per-run spend cap aborts the run
  before the cap is exceeded; partial results are written with status
  "aborted_cap".

Usage (only after prereg 008 is committed):
  SPEND_GO=1 python3 experiments/008_live_ab_draft.py \
      --n-prompts 200 --max-spend-usd 2.00 --approve-spend
  (no API call is made without SPEND_GO AND --approve-spend AND the prereg file)
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "evidence/ab"
PREREG = OUT / "live_ab_prereg.md"

# ---- hard gates: refuse BEFORE anything else -------------------------------
if os.environ.get("SPEND_GO") != "1":
    sys.exit("REFUSED: SPEND_GO != 1. Live A/B is a draft; no API calls. "
             "Freeze prereg 008 first, then re-run with SPEND_GO=1.")
if not PREREG.exists():
    sys.exit(f"REFUSED: prereg not found: {PREREG}. No API calls without a "
             "frozen preregistration.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-prompts", type=int, default=200)
    ap.add_argument("--max-spend-usd", type=float, default=2.00)
    ap.add_argument("--approve-spend", action="store_true")
    ap.add_argument("--judge-model", default="")  # must be frozen in prereg 008
    args = ap.parse_args()
    if not args.approve_spend:
        sys.exit("REFUSED: --approve-spend missing. No API calls.")
    if not args.judge_model:
        sys.exit("REFUSED: --judge-model empty; judge must be frozen in prereg 008.")

    # TODO(prereg 008): implement prompt sampling (seed 42, disjoint from val +
    # sealed test), the weak/strong client calls, judge scoring, paired
    # bootstrap, cap enforcement, and evidence/ab/live_ab_results.json output.
    sys.exit("DRAFT STUB: analysis implementation is frozen by prereg 008, "
             "not by this file. Nothing has been called; nothing spent.")


if __name__ == "__main__":
    main()
