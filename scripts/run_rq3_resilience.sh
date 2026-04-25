#!/bin/bash
# RQ3: Communication interference and deception resistance
# Tests three pressure scenarios: platform_fee_pressure, price_war_pressure, financial_distress_pressure

set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXP_ROOT="${EXP_ROOT:-${MODEL_TYPE}/newresults}"

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

    # Scenario 1: Platform Fee Pressure (survival pressure)
    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_platform_fee" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller platform_fee_pressure \
        --disable-reentry

    # Scenario 2: Price War Pressure (competitive pressure)
    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_price_war" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller price_war_pressure \
        --disable-reentry

    # Scenario 3: Financial Distress Pressure (post-pandemic debt crisis)
    python ./example/run_market_condition_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_financial_distress" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller financial_distress_pressure \
        --disable-reentry
done

echo ""
echo "RQ3 done."
