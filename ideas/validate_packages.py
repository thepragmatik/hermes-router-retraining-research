#!/usr/bin/env python3
"""Validate Router Innovation Spec Kit package completeness.

Run from repository root:
    python3 ideas/validate_packages.py

This performs filesystem/JSON structure checks only. It does not execute experiments,
access RouterBench, call networks, or authorize spend.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ideas" / "package-manifest.json"


def main() -> int:
    data = json.loads(MANIFEST.read_text())
    required = data["required_package_files"]
    errors: list[str] = []

    for rel in [data["constitution"], data["orchestrator_prompt"], data["status_ledger"], data["roadmap"]]:
        if not (ROOT / rel).is_file():
            errors.append(f"missing program file: {rel}")

    seen_ids: set[int] = set()
    seen_paths: set[str] = set()
    for idea in data["ideas"]:
        idea_id = int(idea["id"])
        path = str(idea["path"])
        if idea_id in seen_ids:
            errors.append(f"duplicate idea id: {idea_id}")
        if path in seen_paths:
            errors.append(f"duplicate idea path: {path}")
        seen_ids.add(idea_id)
        seen_paths.add(path)
        pkg = ROOT / path
        if not pkg.is_dir():
            errors.append(f"missing package directory: {path}")
            continue
        for filename in required:
            p = pkg / filename
            if not p.is_file() or p.stat().st_size == 0:
                errors.append(f"missing/empty required file: {path}/{filename}")

    expected_ids = set(range(101, 110))
    if seen_ids != expected_ids:
        errors.append(f"idea ids must be 101..109; got {sorted(seen_ids)}")

    if errors:
        print("SPEC_KIT_PACKAGE_VALIDATION=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SPEC_KIT_PACKAGE_VALIDATION=PASS")
    print(f"ideas={len(seen_ids)} required_files_per_idea={len(required)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
