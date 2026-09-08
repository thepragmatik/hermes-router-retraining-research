# Run ledger (local, untracked raw logs)

- `stage0_run.log` / `corrected_run.log` — raw stdout of the two gate runs
  (kept locally; untracked per PII hygiene: absolute bundle path echoed).
- Commit chain: c5d9cc2 (PREREG freeze, pre-code) -> 82afb79 (modules+12 tests)
  -> d7672ec (first gate run, 30/30) -> 22fd693 (first-run gate table +
  correction declaration, pre-corrected-run) -> a82c9b3 (corrected run +
  ledgers + STAGE0_REPORT: G3 FAIL -> KILLED) -> 569d6f2 (PII scrub) -> f720b42
  (untrack raw logs).
- Terminal status: KILLED. Spend $0.
