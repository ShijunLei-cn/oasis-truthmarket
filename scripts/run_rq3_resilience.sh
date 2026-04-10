#!/bin/bash
# RQ3: Communication interference and deception resistance
# (macro welfare + deception metrics; old rq2 seller-communication setting)

set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXP_ROOT="${EXP_ROOT:-${MODEL_TYPE}/paper_important_results}"

echo "=========================================="
echo "RQ3: Communication Interference & Resistance"
echo "Config: ${CONFIG_FILE}"
echo "Output: experiments/${EXP_ROOT}/rq3_resilience"
echo "=========================================="

for MARKET in reputation_only reputation_and_warrant; do
    if [ "${MARKET}" = "reputation_only" ]; then
        PREFIX="r"
    else
        PREFIX="rw"
    fi

    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_policy_making" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller policy_making \
        --disable-reentry

    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_pressure_quickprofits" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller pressure_quickprofits \
        --disable-reentry

    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_psychological-based-attack" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller psychological-based-attack \
        --disable-reentry
done

echo ""
echo "RQ3 done."
