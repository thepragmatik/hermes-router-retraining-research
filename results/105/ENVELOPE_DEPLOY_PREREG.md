# PREREG — Idea 105 Conformal Safety Envelope: deploy into the shadow-router service (feature-flagged)

**Date frozen:** 2026-09-09 (before any envelope code was written)
**Branch:** `feat/105-envelope-deploy` (worktree `/Users/rath/src/idea-worktrees/envelope-deploy`, base 9571381)
**Spend cap:** $0 — no paid API/model calls. This whole deploy is local compute only.
**Operator boundary:** this child does NOT touch the production service on 127.0.0.1:8765
(no restart, no config change there, no bind). The orchestrator deploys after merge.
**Frozen upstream evidence:** `results/105/PREREG.md` (Stage-0 prereg), `results/105/STAGE0_REPORT.md`
(verdict `V1_SAFE_SLICE`), `results/105/coverage_risk_global.csv` (10 folds × 3 α), all committed before this prereg.

## 1. Feature flag (frozen)

- **Location:** `router_config.yaml`, under the existing `router:` block, new key `envelope_enabled`.
- **Default OFF:** if the key is absent, or the whole file is missing, the envelope is OFF.
- **Reading:** only by `telemetry/envelope.py` via `router_config.yaml` (same file the service already
  reads through `router_v1_cli.load_config`; no second config file).
- **Flag-OFF byte-identity contract:** with `envelope_enabled` absent/false, the service MUST be
  byte-identical to current production: no envelope module import, no envelope key in any response,
  no envelope key on `/health`, no envelope counter, no ledger schema change. Verified by a
  regression test that asserts the exact key-set and value-set of `/route` and `/health` responses
  against the frozen pre-change shape.

## 2. Response schema with flag ON (frozen)

On every valid `/route` when the flag is ON, the response gains exactly ONE top-level key
`envelope` (a dict). No existing key changes: `decision`, `confidence`, `threshold`, `mode`,
`engine`, `ts`, `event_id` are byte-for-byte what the raw V1 path already returns; the V1 engine
call itself is unchanged (single `route()` call, result used as-is).

```
envelope: {
  "enabled":    bool,        # true iff flag ON and calibration loaded
  "mode":       "shadow",    # fixed string
  "alpha":      float,       # frozen operating target: 0.01
  "action":     "accept-weak" | "escalate-strong" | "abstain" | "disabled",
  "threshold_used": float | null,   # the frozen deploy threshold actually compared against
}
```

- `accept-weak`: envelope score ≥ frozen threshold AND raw V1 decision == "weak" → the recorded
  envelope action is that the cheap route was accepted by the envelope's risk control.
- `escalate-strong`: envelope score < frozen threshold (raw V1 decision may be either — the
  envelope does not override the V1 decision, it records only its own verdict).
- `abstain`: `NO_SAFE_COVERAGE` at the configured α (recorded, never a route block).
- `disabled`: alarm tripped (drift/OOD/noise/manipulation/budget) or load failure — envelope
  stepped aside for this request, raw V1 decision is the sole authority.

## 3. Runtime-loadable envelope artifact (frozen)

Stage-0 saved NO runtime-loadable model object (only CSVs). The deployment form is therefore the
**frozen qualified-threshold table** derived from the committed Stage-0 CSV
`results/105/coverage_risk_global.csv` (30 rows = 10 folds × 3 α, zero `NO_SAFE_COVERAGE` rows):

```
alpha    threshold (deploy)     derivation
0.01     0.8243549466133118     max over the 10 fold-qualified thresholds (seed 5)
0.025    0.6964215040206909     max (seed 5)
0.05     0.6348569393157959     max (seed 2)
```

Derivation rule (frozen): per α, the MAXIMUM over folds of the largest-coverage threshold whose
exact one-sided Clopper–Pearson (1−δ=0.95, δ=0.05) upper bound ≤ α. Taking the max is the
conservative intersection: the resulting acceptance set is the smallest of the fold-qualified
sets, so every fold's CP-verified guarantee covers it. Frozen α = **0.01** (the deployed
operating point); the other two table rows ship for recalibration/reconfiguration only and are
NOT selected at runtime in this deploy.

Producing folds (verified at build time, frozen here):
- α=0.01: threshold 0.8243549466133118, seed 5, m_cal=2519, k_cal=16, cp_ub=0.009631,
  CP duality P(Bin(2519, 0.01) ≥ 17) = 0.9658 ≥ 0.95.
- α=0.025: threshold 0.6964215040206909, seed 5, m_cal=2696, k_cal=53, cp_ub=0.024651,
  duality p = 0.9606.
- α=0.05: threshold 0.6348569393157959, seed 2, m_cal=2928, k_cal=126, cp_ub=0.049721,
  duality p = 0.9566.

Artifact sha256 (pinned at prereg commit, asserted by tests):
`5af9696508f51e038218bfc3d2689b37c351e6c5ea99b87efa202891f0ffc5ae`
(telemetry/envelope_config.json, 184388 bytes; embeds the frozen table, the CP verification
counts, the KS reference values, and provenance hashes — no prompt text, no raw data rows).

**Artifact:** `telemetry/envelope_config.json` — a frozen JSON file containing the table above,
`delta: 0.05`, `deployed_alpha: 0.01`, provenance hashes, and the frozen KS reference-window
hash list (see §5). Its sha256 is pinned in this prereg at commit time and asserted by tests.
It is generated ONCE by a committed script (`experiments/105/build_runtime_table.py`) from the
committed Stage-0 CSV — deterministic, no free parameters.

**Provenance chain (verified before this prereg was written):**
- `results/v1_train_probs.npy` sha256 `dfbe974ecadb93e8f2b78ebb5f87b33d6ae9c108b48b903a4c433dd5b017e1af` ✓ (matches Stage-0 prereg)
- `router_v1/mf_router.pt` sha256 `db6706b14c5723acbb484dc66dc151fb6b9b010c5d749a1e80237c7a53951dc7` ✓
- winrate_table.parquet sha256 `4e58f02413ee008afed32236cf7dd9a09b2872d70dcf9f19c3834b5ace2963a6` ✓
- Re-running the Stage-0 calibration method (`experiments/105/calibrate.py::calibrate`, imported
  read-only) on the raw artifacts with the Stage-0 splits reproduces the committed CSV:
  max |threshold diff| = 3.0e-8, max |evaluation risk diff| = 9.8e-17 across all 30 rows.
- The committed CSV is therefore verified as the CP-bound artifact; the runtime table is a
  deterministic reduction of it (max per α), not a new calibration.

**CP-bound reproduction at load time (fail-closed, stdlib-only — scipy is NOT guaranteed on the
production interpreter):** `telemetry/envelope.py` re-verifies at startup, for every table row:
(a) the threshold appears verbatim in the committed `results/105/coverage_risk_global.csv` as a
fold-qualified threshold for that α (provenance match, exact float equality); (b) the producing
fold's calibration acceptance count `m_cal` and failure count `k_cal` (embedded in
`telemetry/envelope_config.json` by the build script) satisfy the exact CP duality
`P(Binomial(m_cal, α) ≥ k_cal + 1) ≥ 1 − δ` computed with a stdlib log-space binomial tail
(pre-verified against scipy `beta.ppf` on all 30 Stage-0 rows before this prereg was frozen);
(c) `router_v1/mf_router.pt`'s sha256 matches the prereg value. Any mismatch → envelope loads
disabled (fail-open to raw V1, alarm field `load_failed`, /health counter incremented). The
envelope NEVER relaxes α and NEVER synthesizes a threshold.

## 4. Runtime safety score (frozen)

Stage-0 score: `s = 1 − p` where `p` = V1 P(strong wins), float32, unrounded.
Runtime: the service already receives `conf = round(p, 4)` from the frozen engine; the envelope
uses **`s_runtime = 1 − conf`** — no second encoder/model pass, no modification of `router_v1/`,
one engine call per request (unchanged).

Verified pre-prereg: on all 30 Stage-0 (fold, α) evaluations, recomputing evaluation risk with
`s_runtime` instead of the unrounded `s` changes risk by at most 1.4e-5 (max 1.37e-5), which
cannot flip any fold's pass/fail status at the 3-decimal α grid. Boundary collisions: zero rows
in the full 29,193-row train set have `s_runtime` exactly equal to any frozen threshold; the
minimum margin is 2.15e-5, so the comparison `s_runtime >= threshold` is well-conditioned.

## 5. Alarms and disable behavior (frozen)

Detection runs ONLY when the flag is ON, entirely in-process, $0, stdlib-only. All alarm state is
per-process (in-memory rolling windows). On ANY alarm trip: `envelope.action = "disabled"` for
that request (fail-open to raw V1), a rolling window counter increments, and `/health` exposes
the envelope counter block (§6). The envelope never blocks, delays, or alters a route.

1. **Score-shift (KS, pure-math asymptotic two-sample Kolmogorov–Smirnov, no scipy at runtime):**
   reference = the frozen Stage-0 seed-0 calibration slice of `s_runtime`, embedded VERBATIM in
   `telemetry/envelope_config.json` (11,677 pure-JSON floats, ~150 KB — the runtime score grid is
   finite and non-smooth, so no quantile summary can reproduce an exact KS statistic; verbatim
   values are required and are non-sensitive: a hashable transform of model probabilities, no
   prompt text). Window = the ≤500 most recent envelope-evaluable live scores (deduplicated per
   §5.4). Fire iff asymptotic p < 0.01. Pre-verified pre-prereg: the pure-math statistic+p-value
   matches scipy `ks_2samp` fire/no-fire decisions on every Stage-0 drift fixture equivalent
   (in-dist p≈0.10 no-fire; +0.05 shift p≈1e-229 fire; adversarial −0.2 push p≈1e-131 fire).
2. **Risk-breach (realized, inert in this deploy):** if the last 200 envelope-accepted rows
   WITH joined outcome labels have failure count k exceeding the exact one-sided binomial 95%
   critical count at (n, α) — `k > Q_0.95(Binomial(n, α))` — fire. This deploy has no in-process
   label source (outcomes arrive via the offline join ledger), so the path is armed but inert:
   it counts only labeled accepted rows through an outcome-lookup hook that nothing populates
   in this deploy, cannot fire on unlabeled rows, and cannot false-fire.
3. **Evaluation cadence (frozen):** the KS test is evaluated ONLY at non-overlapping windows —
   every 500 NEW envelope-evaluated scores (window deque maxlen 500, one score per route,
   appended only while state is active). Non-overlap is what bounds the in-distribution
   false-alarm rate at the nominal KS level (~1% per evaluation; the ~6% measured rate on
   random overlapping windows pre-prereg was an artifact of draw overlap, not detector error).
   The detector is NOT evaluated before the window first fills (live verification with ~100
   routes will correctly show `ks_evaluations: 0`).
4. **Alarm permanence:** a KS fire (p < 0.01) or risk-breach fire sets state to
   `alarm_disabled` for the process lifetime (silent in-band: `action: "disabled"`, raw V1
   decision unchanged, /health counter visible; recovery = service restart by the operator).
   No budget/re-arm logic — one alarm, one disable, no oscillation. The sanity slice (seed-10
   evaluation segment) is NEVER replayed through the live detector in tests; fixture tests
   inject synthetic score arrays directly into the detector.
5. **Alarm fixture coverage (drift.py equivalent fixtures, injected as arrays):**
   in-distribution control (must NOT fire), task-mix reweight equivalent (window drawn from 3
   families' scores only), +0.05 shift (must fire), rare/OOD-like subpopulation (window from the
   ≤5%-quantile families, must fire), ±0.05 score noise (must fire), adversarial −0.2 push
   (must fire). Behavior on fire: envelope disabled for the process lifetime of the alarm state
   (silent in-band: `action: "disabled"`), fail-open to raw V1, `/health` counter visible.
6. **Load-time protections:** calibration JSON missing/corrupt/hash-mismatch → disabled +
   `load_failed` + /health counter. Envelope exceptions of any kind → disabled for that request +
   error counter (never break the route). Threshold-drift 500, kill switch, edge-prompt 400s,
   exploration-disabled, and the C1–C7 ledger schema are all evaluated BEFORE the envelope and
   are untouched by it; the envelope cannot shadow them (it runs strictly after the V1 engine
   call returns, alongside the existing telemetry step, and can only ADD the `envelope` key).

## 6. /health envelope counter (frozen)

With flag OFF: `/health` byte-identical to today. With flag ON: the existing `telemetry` dict
gains one sibling key `envelope` (does not touch the `telemetry` sub-dict itself):

```
"envelope": {"enabled": bool, "mode": "shadow", "alpha": 0.01,
             "state": "active" | "alarm_disabled" | "load_failed" | "off",
             "action_counts": {"accept-weak": n, "escalate-strong": n,
                               "abstain": n, "disabled": n},
             "alarm_counts": {"ks_fire": n, "ks_evaluations": n,
                              "risk_breach": n, "load_failed": n, "error": n}}
```

## 7. Sanity recompute (frozen before wiring; verified pre-prereg, re-verified live post-build)

Held-out slice: **seed-10 permutation of the 29,193 train rows, evaluation segment** (rows
[40%:80%) of `np.random.default_rng(10).permutation(29193)`, n=11,677). Role disclosure: this
slice was never used to select or qualify the frozen deploy table (Stage-0 folds were seeds 0–9
and never saw seed-10 permutations), but its ROWS do overlap Stage-0 calibration/evaluation row
sets under other permutations — there is no fully-untouched row subset (the 10 Stage-0 folds
leave 0% of rows unused). The slice's independence from the DEPLOYMENT artifact (max-fold
thresholds from seeds 0–9) is what makes it a valid sanity check; it is NOT a pristine generalization claim. Test split remains SEALED; val untouched.

Gate (frozen — pass on BOTH forms, either suffices, both verified pre-prereg on the numbers above):
- **S1 (point):** realized risk of the envelope's acceptance set on the slice ≤ α at EVERY α in
  {0.01, 0.025, 0.05}. Pre-verified: risk 0.00437 / 0.01707 / 0.03903 — PASS.
- **S2 (bound):** the observed failure count k on the slice ≤ the exact one-sided binomial 95%
  critical count at n_acc and α. Pre-verified: k = 11/46/113 vs critical 34/81/164 — PASS
  (binomial p = 0.9995 / 0.9978 / 0.9978).

The live black-box verification re-runs S1+S2 on a 1,500-row deterministic prefix of the same
slice through the REAL service with the flag ON, and additionally asserts the response schema
and that flag-OFF responses on the same prompts contain no `envelope` key.

## 8. Test matrix (frozen; all red-first where new)

1. `test_flag_off_byte_identical` — flag OFF: `/route` response key-set == pre-change shape
   (decision/confidence/threshold/mode/engine/ts/event_id), `/health` key-set unchanged, no
   envelope import side effects, ledger schema C1–C7 unchanged (byte-compare against fixture).
2. `test_flag_on_envelope_fields` — flag ON: every valid response carries the exact frozen
   `envelope` dict (all 5 keys), `action` ∈ frozen vocabulary, existing keys unchanged and
   equal to the flag-OFF response for the same prompt.
3. `test_envelope_accept_escalate_actions` — score ≥ threshold ∧ decision weak → accept-weak;
   score < threshold → escalate-strong; decision strong ∧ score ≥ threshold → escalate-strong
   (envelope never promotes a weak route for a row V1 sends strong).
4. `test_alarm_fixture_disables` — each §5 fixture: shifted/noise/OOD/manipulation fire →
   envelope `action: "disabled"`, raw decision unchanged, `/health` alarm counter ≥ 1;
   in-distribution control does NOT fire.
5. `test_no_safe_coverage_falls_through` — α configured to a fold with NO_SAFE_COVERAGE (or
   threshold missing) → `action: "abstain"`, raw V1 decision returned unmodified.
6. `test_kill_switch_unchanged_with_flag_on` — `enabled: false` → `decision: "disabled"`,
   NO envelope key (kill switch precedes envelope), no model load.
7. `test_threshold_drift_500_nonshadowing` — threshold ≠ 0.30 with flag ON → 500, no envelope
   key, no ledger write.
8. `test_edge_prompt_400_nonshadowing` — empty/missing/whitespace/non-string prompts with flag
   ON → 400 exact frozen body, no envelope key, no ledger write, counters unchanged.
9. `test_health_envelope_counter` — flag ON: counter block present with all frozen keys;
   flag OFF: absent; counts move after accept/escalate routes.
10. `test_load_fail_closed` — corrupt/missing `telemetry/envelope_config.json` with flag ON →
    envelope disabled, `load_failed` counter, raw V1 route intact.
11. `test_ledger_schema_unchanged` — C1–C7 decision-event fields byte-identical with flag ON
    (no envelope data enters the ledger in this deploy).
12. `test_calibration_load_cp_verification` — the deployed table satisfies the Stage-0 CP bound
    (stdlib binomial duality) on the producing fold for every α; runtime table sha256 matches
    the committed artifact.
13. `test_ks_cadence_nonoverlapping` — detector evaluated only at 500-score boundaries (count
    = floor(new_scores/500)); in-distribution windows do not fire; alarm permanence (state
    stays `alarm_disabled`, counts frozen after fire).
14. Full pre-existing suite (197 tests) remains green — no regression anywhere.

## 9. Constraints honored (frozen)

- $0: no network calls, no model training/inference beyond the existing engine call; all
  verification is local computation on already-committed artifacts.
- `router_v1/`, `specs/`: read-only (imports and reads only).
- `evidence/telemetry/*.jsonl`: never committed/modified/deleted (gitignored; test suites use
  isolated tmp dirs).
- No prompt text in ANY commit/fixture/report: test prompts are synthetic generic strings;
  ledgers carry hashes only (existing schema); no prompt text enters this prereg or any new file.
- Production service untouched; all test services bind 127.0.0.1 ports ≥ 8766.

## 10. Deviations from this prereg

None permitted without a committed pre-results erratum enumerating each fix (no gate weakened),
committed before any live verification numbers are observed. Any post-result edit voids the run.
