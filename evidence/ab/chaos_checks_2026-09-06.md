# Kill-switch chaos checks — 2026-09-06 (007, Task 6)

Method: service on 127.0.0.1:8766 with temp config via ROUTER_CONFIG (/tmp/router_cfg_chaos.yaml,
copy of real config with enabled flipped); real router_config.yaml never modified (verified
`enabled: false` before and after). Guard order verified in source (router_v1_cli.py:55-65,
router_shadow.py:48-52): enabled check FIRST, then threshold check — so Check 1's config is
correctly reported "disabled" when it also would carry a drifted threshold.

1. mid-flight kill switch (enabled true→false, no service restart) → health flipped to
   enabled:false; POST /route returned {"decision": "disabled", "confidence": 0.0} → PASS
2. missing config (ROUTER_CONFIG=/nonexistent, CLI) → {"decision": "disabled", "reason":
   "config not found: /nonexistent"}, exit code 0 → PASS
3. threshold drift 0.5 (enabled:true temp cfg): CLI → {"error": "threshold 0.5 != frozen
   0.30"}, exit 2; HTTP → {"error": "threshold drift"}, HTTP 500 → PASS
4. malformed YAML `router: [unclosed`: CLI → yaml ScannerError traceback, exit 1, no decision
   JSON (fail LOUD); HTTP → curl exit 52 (empty reply), no JSON → PASS (known limitation:
   fail-loud, not fail-open; hardening out of scope per plan)

Cleanup verified: service killed (port 8766 free), temp configs removed, real config still
`enabled: false`.

Summary: 4/4 checks match specified behaviour (prereg gate A6: PASS).
