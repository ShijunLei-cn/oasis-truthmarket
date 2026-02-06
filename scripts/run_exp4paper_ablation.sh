#!/bin/bash
# Comprehensive experiment script for paper experiments
# Includes RQ1, RQ2, RQ3, and RQ4 experiments

echo "=========================================="
echo "Paper Experiments: Comprehensive Run"
echo "=========================================="

MODEL_TYPE="${MODEL_TYPE:-"gpt-4o-mini"}"
# Model configuration (can be overridden via environment variables)
MODEL_PLATFORM="${MODEL_PLATFORM:-}"


# Default configuration file (can be overridden via CONFIG_FILE environment variable)
SAFE_MODEL_TYPE="${MODEL_TYPE//-/_}"
CONFIG_FILE="${CONFIG_FILE:-configs/rq2_experiment_largescale_${SAFE_MODEL_TYPE}.yaml}"


# Build model arguments if provided
MODEL_ARGS=""
if [ -n "$MODEL_PLATFORM" ]; then
    MODEL_ARGS="$MODEL_ARGS --model-platform $MODEL_PLATFORM"
fi
if [ -n "$MODEL_TYPE" ] && [ "$MODEL_TYPE" != "default" ]; then
    MODEL_ARGS="$MODEL_ARGS --model-type $MODEL_TYPE"
fi

echo "Using config file: ${CONFIG_FILE}"
echo "Model type: ${MODEL_TYPE}"
if [ -n "$MODEL_ARGS" ]; then
    echo "Model overrides: $MODEL_ARGS"
fi

# ==================== RQ1: Cognitive Probing ====================
echo ""
echo "=========================================="
echo "RQ1: Cognitive Probing for Reputation Manipulation"
echo "=========================================="

# RUNS=5
# ROUNDS=10
# SELLERS=50
# BUYERS=50
# PROBE_INTERVAL=1

# Reputation only market
# echo ""
# echo "Running Reputation-Only Market experiments..."
# python ./example/run_rq1_experiment.py \
#     --runs ${RUNS} \
#     --rounds ${ROUNDS} \
#     --sellers ${SELLERS} \
#     --buyers ${BUYERS} \
#     --market-type reputation_only \
#     --output-dir experiments/${MODEL_TYPE}/paper/rq1/r_wo \
#     --probe-interval ${PROBE_INTERVAL} \
#     --config "${CONFIG_FILE}" \
#     --probe-interval 1

# # Reputation and warrant market
# echo ""
# echo "Running Reputation+Warrant Market experiments..."
# python ./example/run_rq1_experiment.py \
#     --runs ${RUNS} \
#     --rounds ${ROUNDS} \
#     --sellers ${SELLERS} \
#     --buyers ${BUYERS} \
#     --market-type reputation_and_warrant \
#     --output-dir experiments/${MODEL_TYPE}/paper/rq1/rw_wo \
#     --probe-interval ${PROBE_INTERVAL} \
#     --config "${CONFIG_FILE}" \
#     --probe-interval 1

# # ==================== RQ2: Market Mechanism Comparison ====================
# echo ""
# echo "=========================================="
# echo "RQ2: Market Mechanism Comparison (No Communication)"
# echo "=========================================="

# Reputation only market (no communication)
# echo ""
# echo "Running Reputation-Only Market experiments..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper/rq2/r_wo \
#     --market-type reputation_only \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# # Reputation and warrant market (no communication)
# echo ""
# echo "Running Reputation+Warrant Market experiments..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper/rq2/rw_wo \
#     --market-type reputation_and_warrant \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# # ==================== RQ3: Seller Communication ====================
# echo ""
# echo "=========================================="
# echo "RQ3: Group-Level Deception Dynamics (Seller Communication)"
# echo "=========================================="


# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_R_policy_making \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_R_policy_making \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}


# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_R_pressure_quickprofits \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_R_pressure_quickprofits \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_R_psychological-based-attack \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}


# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_R_psychological-based-attack \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}




echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_F_policy_making \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_F_policy_making \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}


# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_F_pressure_quickprofits \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_F_pressure_quickprofits \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_F_psychological-based-attack \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}


# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_F_psychological-based-attack \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}


