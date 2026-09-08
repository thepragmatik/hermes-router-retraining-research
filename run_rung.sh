#!/bin/bash
# Rung runner for the generator-pivot factory (spend-gated).
#
# Usage: GEN_GO=1 SPEND_CAP_USD=0.10 OPENROUTER_API_KEY=... ./run_rung.sh [rung-number]
#
# Refuses to run (exit 1, REFUSED) unless GEN_GO=1 AND SPEND_CAP_USD>0.
# Exports the FROZEN labeling pair (GENERATOR_PREREG.md, 2026-09-07):
#   weak   = qwen/qwen3.7-flash
#   strong = deepseek/deepseek-v4-flash
# unless WEAK_MODEL / STRONG_MODEL are already set in the environment.
# cascade_label.py env defaults remain the V1-frozen pair for router-contract
# compat; this script overrides them via env for the rung run.
#
# $0 posture: with no API key / GEN_GO unset, nothing runs and nothing is
# spent. The pricing cache must be fresh (fetch_pricing.py) before real runs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

REFUSED() {
  echo "REFUSED: $1" >&2
  exit 1
}

[ "${GEN_GO:-}" = "1" ] || REFUSED "GEN_GO=1 required (spend gate); nothing ran"
CAP="${SPEND_CAP_USD:-0}"
case "$CAP" in
  ''|*[!0-9.]*) REFUSED "SPEND_CAP_USD must be a positive number; got '$CAP'" ;;
esac
/usr/bin/python3 -c "import sys; sys.exit(0 if float('$CAP') > 0 else 1)" \
  || REFUSED "SPEND_CAP_USD must be > 0 (spend gate); nothing ran"

export WEAK_MODEL="${WEAK_MODEL:-qwen/qwen3.7-flash}"
export STRONG_MODEL="${STRONG_MODEL:-deepseek/deepseek-v4-flash}"

# R6: GEN_JSON_MODE pass-through (default OFF — glm json_object support is
# probe-gated; both outcomes pre-registered in GENERATOR_PREREG.md R6).
# Set GEN_JSON_MODE=1 in the invoking environment to enable response_format.
export GEN_JSON_MODE="${GEN_JSON_MODE:-}"

# Pre-flight routeability smoke (R1b amendment): 2 calls/tier, aborts exit 3
# before any generation spend if a tier 404s (e.g. the qwen3.7-flash class).
if [ "${SMOKE_SKIP:-0}" != "1" ]; then
  /usr/bin/python3 experiments/gen_factory/smoke_tiers.py \
    || REFUSED "tier smoke failed — aborting before generation spend"
fi

echo "rung runner: weak=$WEAK_MODEL strong=$STRONG_MODEL cap=\$${SPEND_CAP_USD}"

# Derive RUNG from the --rung CLI arg (R1b lesson: env RUNG drifted from the
# arg actually passed to generate_items.py); fall back to env, then 1.
RUNG="$(/usr/bin/python3 -c "import sys; a=sys.argv[1:]; print(a[a.index('--rung')+1] if '--rung' in a else '1')" "$@" 2>/dev/null || echo 1)"
BATCH_SALT="$(date +%s)"

/usr/bin/python3 experiments/gen_factory/generate_items.py "$@" --batch-salt "$BATCH_SALT"
/usr/bin/python3 experiments/gen_factory/cascade_label.py \
  "evidence/gen_factory/items_batch${RUNG}.jsonl"
/usr/bin/python3 experiments/gen_factory/ledger_report.py

echo "RUNG COMPLETE — see evidence/gen_factory/ledger_report.md"
