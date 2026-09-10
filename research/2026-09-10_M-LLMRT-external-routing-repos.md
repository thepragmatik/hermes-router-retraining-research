# M-LLMRT — External LLM-Routing Repository Research — 2026-09-10

Mission: analyze `github.com/topics/llm-router` ecosystem, specifically
`open-world-project/model-router` and `mnfst/llm-gateway`, for ideas
applicable to the Hermes uplift program (router research + operational
telemetry stack). $0 spend; all research steps routed through the
production shadow router with session/message ids, creating organic
joinable telemetry (5 decisions, 4 outcomes, join_rate 1.0).

## 1. open-world-project/model-router (30 stars, Python, Hermes plugin)

A Hermes Agent plugin doing per-turn cost-aware routing across 5 tiers
(T1 qwen-flash triage → T5 claude-sonnet-4-6 reasoning-medium). Key
mechanics from install.py (90 KB, the whole plugin):

- **LLM-as-classifier**: a separate cheap classifier call
  (qwen/qwen3.5-flash) classifies each turn, then picks the cheapest
  tier that "should work".
- **Fail-fast posture** (from its generated SOUL.md block):
  "if task complexity is unclear, choose the lowest plausible tier
  first"; "treat one cheap failed attempt as acceptable; escalate after
  mismatch, weak output, or repeated failure".
- **Manual pinning** `/t1`–`/t5`, `/auto` overrides auto-routing.
- Per-profile config (`model_router.yaml`), installer repairs/patches
  Hermes core files, syncs skill_routing.md + SOUL.md, hooks
  pre_llm_call / post_llm_call / post_tool_call.

Relevance to us:
- Same tier-escalation philosophy as V1 (weak→strong on low confidence),
  independently converged. Our weak/strong pair matches their T2/T4-ish
  split (deepseek-v4-flash is literally in both pools).
- Their "escalate only after weak output" is a POST-HOC escalation
  signal we do not currently use: our envelope escalates PRE-HOC on
  score. Their rule suggests outcome-driven escalation (record outcome
  failures → escalate retry). We now HAVE outcome capture to feed this.
- Their classifier call costs a per-turn LLM round-trip; our local V1
  classifier has zero marginal cost — our design is cheaper; their
  interest is the policy, not the mechanism.

## 2. mnfst/llm-gateway ("Manifest", 7.5k stars, TypeScript)

Full agent-gateway platform (1889 files) with provider routing,
fallbacks, per-agent routing, cost tracking, observability. Key signal:

- **They are RETIRING complexity-based routing**: commit trail shows
  "make complexity routing optional with a default tier" (#1675) →
  "merge complexity into default tab with toggle" (#1718) → "hide
  complexity/task-specific routing from new agents" (PR #2309
  deprecation strategy). New agents see only Default + Custom routing.
  This is external negative evidence for complexity/task-feature-driven
  routing — consistent with our program kills (prompt-only classifiers,
  102 threshold-on-p dominance).

- Their surviving architecture: **user-pinned default tier + explicit
  fallback chains** (model-fallback.ts: provider/model resolution with
  name-variant normalization, alias tables, pricing lookup) rather than
  automatic per-prompt routing. Reliability engineering (fallbacks,
  health probes, healing) replaced cleverness.

- Failure handling philosophy: structured fallbacks and health probes,
  i.e. spend engineering on making the cheap choice robust instead of
  predicting which tier is needed.

## 3. Synthesis — ideas for Hermes uplift (ranked, with program-fit)

1. **Outcome-driven escalation ladder (STRONG candidate, feeds 106 VOI
   later)**: our stack already captures outcomes. A policy layer "retry
   on the other tier after recorded failure" matches model-router's
   fail-fast rule and llm-gateway's fallback philosophy, and it needs
   NO prediction — just recorded outcomes. Prereg-gated, shadow-first.
   Evidence tier: shadow observational before any enforcement.

2. **External validation of our negative results**: llm-gateway's
   deprecation of complexity routing is independent-field negative
   evidence for the same direction our KILLED verdicts point. Worth
   citing in INTEGRATION_RECOMMENDATION as corroborating evidence
   (research tier, not a new experiment).

3. **Fallback chains ≠ routing**: llm-gateway's fallback resolution is
   about availability/reliability, not quality routing. Our envelope's
   `abstain` action is the analogous safety valve. Candidate future
   work: abstain → escalate to strong as a *fallback* (deterministic,
   not predicted) rather than as a classifier decision.

4. **Do NOT adopt**: LLM-as-classifier per-turn routing (costs a call,
   our router is free), 5-tier ladders (our data supports 2 tiers),
   user-facing tier pinning (conflicts with prereg-gated enforcement).

## 4. Mission traffic record (organic, joinable)
- 5 routes via POST /route with session_id=m-llmrt + message ids; all 200.
- 4 outcomes posted via POST /outcome (3 success, 1 aborted);
  join_rate 1.0, orphan_outcomes 0.
- Join-readiness warning fires on historical ledger (41% null-id rows
  are pre-enforcement test traffic); post-enforcement rows are 100%
  id-complete — enforcement working as designed.

## Verdict
Mission COMPLETE. Spend $0. No production changes. Deliverable: this
report; telemetry value realized (first joined organic outcomes).