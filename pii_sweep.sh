#!/bin/bash
cd ~/src/hermes-router-retraining-research
grep -RInE '/Users/rath|sk-or-v1-|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' \
  experiments/gen_factory tests/ GENERATOR_PREREG.md run_rung.sh \
  evidence/gen_factory evidence/shadow evidence/handoff \
  results/V1_BASELINE_GAPS.md MISSION_LOG.md memo/ \
  | grep -v expanduser > /tmp/pii_sweep_hits.txt
echo "PII_HITS=$(wc -l < /tmp/pii_sweep_hits.txt | tr -d ' ')"
cat /tmp/pii_sweep_hits.txt
echo "---GIT---"
git log --oneline -5
git status --short | head -8
