#!/bin/bash
# RQ4: Buyer Adaptation Mechanisms
# When buyers can share information, do they collectively adapt to avoid dishonest sellers over time?
# This script runs buyer communication experiments with Fake and Real channels
# Examines the defensive capabilities of buyer agents and their ability to learn from shared experiences

echo "=========================================="
echo "RQ4 Experiment: Buyer Adaptation Mechanisms"
echo "=========================================="

# Configuration file path (optional - if not provided, uses default config.py)
CONFIG_FILE="${CONFIG_FILE:-configs/sim_gpt4omini_50s_50b_10r_runs5_base.yaml}"



# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Fake Channel..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id r_wbc_F \
    --market-type reputation_only \
    --communication both \
    --communication-channel-type Fake \
    --Posts4Seller policy_making \
    --runs 5 \
    --config "${CONFIG_FILE}"

# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Real Channel..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id r_wbc_R \
    --market-type reputation_only \
    --communication both \
    --communication-channel-type Real \
    --Posts4Seller policy_making \
    --runs 5 \
    --config "${CONFIG_FILE}"

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Fake Channel..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id rw_wbc_F \
    --market-type reputation_and_warrant \
    --communication both \
    --communication-channel-type Fake \
    --Posts4Seller policy_making \
    --runs 5 \
    --config "${CONFIG_FILE}"

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Real Channel..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id rw_wbc_R \
    --market-type reputation_and_warrant \
    --communication both \
    --communication-channel-type Real \
    --Posts4Seller policy_making \
    --runs 5 \
    --config "${CONFIG_FILE}"
