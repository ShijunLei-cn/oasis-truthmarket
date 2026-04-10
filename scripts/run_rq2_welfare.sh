#!/bin/bash
# RQ2: Warrant effect on market welfare (no communication)

set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXP_ROOT="${EXP_ROOT:-${MODEL_TYPE}/paper_important_results}"

echo "=========================================="
echo "RQ2: Warrant Welfare (No Communication)"
echo "Config: ${CONFIG_FILE}"
echo "Output: experiments/${EXP_ROOT}/rq2_welfare"
echo "=========================================="

python ./example/run_market_condition_experiment.py \
    --experiment-id "${EXP_ROOT}/rq2_welfare/r_wo" \
    --market-type reputation_only \
    --communication none \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --disable-reentry

python ./example/run_market_condition_experiment.py \
    --experiment-id "${EXP_ROOT}/rq2_welfare/rw_wo" \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --disable-reentry

echo ""
echo "RQ2 done."
