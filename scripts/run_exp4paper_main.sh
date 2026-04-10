#!/bin/bash
# Paper experiment runner (refactored to the new 3-RQ framing)
# RQ1: Vulnerability intention in reputation-only market
# RQ2: Welfare effect of warrant mechanism (no communication)
# RQ3: Communication interference and market resistance (macro+micro via old rq2 setup)

set -euo pipefail

echo "=========================================="
echo "Paper Experiments: New 3-RQ Pipeline"
echo "=========================================="

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXP_ROOT="${MODEL_TYPE}/paper_important_results"

echo "Using config file: ${CONFIG_FILE}"
echo "Model type: ${MODEL_TYPE}"
echo "Experiment root: experiments/${EXP_ROOT}"

# --------------------------------------------------------------------
# RQ1: Reputation-only vulnerability intention
# --------------------------------------------------------------------
echo ""
echo "=========================================="
echo "RQ1: Vulnerability Intention (Reputation-Only)"
echo "=========================================="

python ./example/run_rq1_experiment.py \
    --market-type reputation_only \
    --output-dir "experiments/${EXP_ROOT}/rq1_intent/r_wo" \
    --config "${CONFIG_FILE}"

# --------------------------------------------------------------------
# RQ2: Warrant -> market welfare (baseline, no communication)
# --------------------------------------------------------------------
echo ""
echo "=========================================="
echo "RQ2: Warrant Welfare (No Communication)"
echo "=========================================="

python ./example/run_single_config_experiment.py \
    --experiment-id "${EXP_ROOT}/rq2_welfare/r_wo" \
    --market-type reputation_only \
    --communication none \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}"

python ./example/run_single_config_experiment.py \
    --experiment-id "${EXP_ROOT}/rq2_welfare/rw_wo" \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}"

# --------------------------------------------------------------------
# RQ3: Communication interference vs deception resistance
# Reuses the old rq2 design (policy / pressure / psychology, seller comm)
# --------------------------------------------------------------------
echo ""
echo "=========================================="
echo "RQ3: Communication Interference & Resistance"
echo "=========================================="

for MARKET in reputation_only reputation_and_warrant; do
    if [ "${MARKET}" = "reputation_only" ]; then
        PREFIX="r"
    else
        PREFIX="rw"
    fi

    python ./example/run_single_config_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_policy_making" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller policy_making

    python ./example/run_single_config_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_pressure_quickprofits" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller pressure_quickprofits

    python ./example/run_single_config_experiment.py \
        --experiment-id "${EXP_ROOT}/rq3_resilience/${PREFIX}_wsc_R_psychological-based-attack" \
        --market-type "${MARKET}" \
        --communication seller \
        --communication-channel-type Real \
        --config "${CONFIG_FILE}" \
        --Posts4Seller psychological-based-attack
done

echo ""
echo "=========================================="
echo "All experiments submitted for new RQ1/RQ2/RQ3 framing."
echo "=========================================="
