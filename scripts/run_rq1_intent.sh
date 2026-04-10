#!/bin/bash
# RQ1: Vulnerability intention in reputation-only market

set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXP_ROOT="${EXP_ROOT:-${MODEL_TYPE}/newresults}"

echo "=========================================="
echo "RQ1: Vulnerability Intention (Reputation-Only)"
echo "Config: ${CONFIG_FILE}"
echo "Output: experiments/${EXP_ROOT}/rq1_intent/r_wo"
echo "=========================================="

python ./example/run_intent_probe_experiment.py \
    --market-type reputation_only \
    --output-dir "experiments/${EXP_ROOT}/rq1_intent/r_wo" \
    --config "${CONFIG_FILE}" \
    --reentry-allowed-round 2

echo ""
echo "RQ1 done."
