#!/bin/bash
# Comprehensive experiment script for paper experiments
# Includes RQ1, RQ2, RQ3, and RQ4 experiments

echo "=========================================="
echo "Paper Experiments: Comprehensive Run"
echo "=========================================="

# Default configuration file (can be overridden via CONFIG_FILE environment variable)
CONFIG_FILE="${CONFIG_FILE:-configs/rq2_experiment_largescale_gpt_4o_mini.yaml}"

# Model configuration (can be overridden via environment variables)
MODEL_PLATFORM="${MODEL_PLATFORM:-}"
MODEL_TYPE="${MODEL_TYPE:-"gpt-4o-mini"}"

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


RUNS=5
ROUNDS=10
SELLERS=50
BUYERS=50
PROBE_INTERVAL=1

# # ==================== RQ1: Cognitive Probing ====================
# echo ""
# echo "=========================================="
# echo "RQ1: Cognitive Probing for Reputation Manipulation"
# echo "=========================================="


# # Reputation only market
# echo ""
# echo "Running Reputation-Only Market experiments..."
# python ./example/run_rq1_experiment.py \
#     --runs ${RUNS} \
#     --rounds ${ROUNDS} \
#     --sellers ${SELLERS} \
#     --buyers ${BUYERS} \
#     --market-type reputation_only \
#     --output-dir experiments/${MODEL_TYPE}/paper_largescale/rq1/r_wo \
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
#     --output-dir experiments/${MODEL_TYPE}/paper_largescale/rq1/rw_wo \
#     --probe-interval ${PROBE_INTERVAL} \
#     --config "${CONFIG_FILE}" \
#     --probe-interval 1

# # # ==================== RQ2: Market Mechanism Comparison ====================
# # echo ""
# # echo "=========================================="
# # echo "RQ2: Market Mechanism Comparison (No Communication)"
# # echo "=========================================="

# # Reputation only market (no communication)
# echo ""
# echo "Running Reputation-Only Market experiments..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wo \
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
#     --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wo \
#     --market-type reputation_and_warrant \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# # # ==================== RQ3: Seller Communication ====================
# # echo ""
# # echo "=========================================="
# # echo "RQ3: Group-Level Deception Dynamics (Seller Communication)"
# # echo "=========================================="

# # Reputation only market - Fake channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_F \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Fake \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# # Reputation only market - Real channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wsc_R \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Real \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# # Reputation and warrant market - Fake channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_F \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Fake \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wsc_R \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

# # ==================== RQ4: Buyer Communication ====================
# echo ""
# echo "=========================================="
# echo "RQ4: Buyer Adaptation Mechanisms (Buyer Communication)"
# echo "=========================================="

# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq4/r_wbc_F \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq4/r_wbc_R \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq4/rw_wbc_F \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq4/rw_wbc_R \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}


# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/paper/rq4/rw_wbsc_R \
#     --market-type reputation_and_warrant \
#     --communication both \
#     --communication-channel-type Real \
#     --runs ${RUNS} \
#     --config "${CONFIG_FILE}" \
#     ${MODEL_ARGS}


# echo ""
# echo "=========================================="
# echo "All paper experiments completed!"
# echo "=========================================="

