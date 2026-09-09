# Downstream unblocks — idea 101 Phase 2-5 close-out (T062)

## What 101 now provides (verified on this branch)

1. **Service-side + CLI decision logging parity (closes G2):** every `/route`
   (HTTP) and CLI route appends a constitution-IV-compliant DecisionEvent via
   ONE shared logger (`telemetry/wiring.py`), with visible error counters on
   `/health`; logging failure never breaks a route (tested).
2. **Real event identity (closes G1):** `event_id` (uuid4) per decision
   replaces the hardcoded `prompt_id 0` as join identity; `prompt_id: 0`
   remains only as a deprecated response-shape compatibility constant.
3. **Privacy-conscious join keys (closes C1/C6 for 109's floor):**
   `prompt_hash` sha256[:12] (dedupe/verifiable), caller-supplied
   `session_id`/`message_id` hashed sha256[:12] (nullable when absent),
   `traffic_stratum` recorded. No raw prompt text or raw caller ids anywhere
   in a ledger (enforced by construction + leakage/PII tests + report scan).
4. **Outcome capture with fidelity classes (closes G4/C3):** append-only
   OutcomeEvent ledger, closed `provenance_class` vocabulary, deterministic
   exactly-one join with supersede-by-reference, ambiguity surfaced (never
   silently resolved).
5. **Data-quality gates, measured:** spec Stage-1 gates computed on
   >=1,000 fixture events — `results/101/STAGE1_DATA_QUALITY.md/.json`.
6. **Bounded exploration machinery, inert by default:** eligibility
   predicates, `shadow_dual`/`randomized_sentinel` modes (default
   `disabled`), seeded epsilon with exact logged propensities, rate/spend
   caps fail-closed, kill switch — all simulation-tested (10k-event rate
   proof), none enabled on any live path.

## Downstream effects

- **102 (Doubly Robust Uplift Router):** UNBLOCKED for its *retrospective
  Stage 0* (already ran on synthetic/simulated data) and for **shadow-data
  development against the new ledger format** — but NOT for real-data
  claims: it needs REAL joinable outcome data (real routed-model outcomes
  with task-native provenance), which only accumulates when the merged
  service actually serves traffic. 101 provides the substrate, not yet the
  real-outcome corpus.
- **108 (Multi-Fidelity Synthetic→Real Fusion):** same shape — real
  propensity-corrected truth requires real outcomes joined through this
  telemetry; unblocked for design against the schema, gated on real data
  existing.
- **109 (Hermes Stage-Aware Router):** its `TRACE_DATA_INSUFFICIENT` contract
  (C1 mission/step identity, C2 stage features, C4 progress/tool/test
  evidence, C5 cost accumulation) is partially addressed: C6 (content hash)
  and C7 (production decision log) are closed by this work; C1's
  session/message hashes now exist but 109 additionally needs
  `mission_id`/`step_id`/parent links and stage-derivable event features,
  which are caller-supplied concerns for the Hermes trace surface, not
  auto-derived here. 109 remains BLOCKED on trace data, less so than before.
- **Randomized exploration (Stage 2):** NOT activated. The DRAFT prereg
  (`experiments/101-live-exploration-prereg.md`) requires explicit operator
  approval fields; until countersigned, only `disabled` mode is valid.

## What the orchestrator must do to turn this into live data

1. Merge this branch; deploy/restart the production shadow service
   (`com.rath.router-shadow-v1`) — production contact is orchestrator-only.
2. Decide whether to countersign the Stage-2 exploration prereg (or keep
   deterministic shadow logging, which already produces joinable decisions).
3. Stand up an outcome-capture pipeline (routed-model answer correctness on
   a sampled subset) — explicitly out of 101's scope per the gap memo.
