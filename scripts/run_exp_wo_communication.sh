#!/bin/bash
# RQ2: Can mechanism design using financial penalties reduce wealth inequalities in the marketplace?
# This script runs experiments comparing Reputation-Only vs Reputation+Warrant markets without communication

echo "=========================================="
echo "RQ2 Experiment: Wealth Inequality Comparison"
echo "Comparing Reputation-Only vs Reputation+Warrant markets"
echo "=========================================="

# Configuration file path (optional - if not provided, uses default config.py)
CONFIG_FILE="${CONFIG_FILE:-configs/rq2_experiment_0.yaml}"

# Reputation only market (no communication)
echo ""
echo "Running Reputation-Only Market experiments..."
# echo "Using config: ${CONFIG_FILE:-default config.py}"
# python ./example/run_single_config_experiment.py \
#     --experiment-id rq2_0/r_wo \
#     --market-type reputation_only \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs 5 \
#     --config "${CONFIG_FILE}"

# Reputation and warrant market (no communication)
echo ""
echo "Running Reputation+Warrant Market experiments..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_single_config_experiment.py \
    --experiment-id rq2_0/rw_wo \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --runs 5 \
    --config "${CONFIG_FILE}"

echo ""
echo "=========================================="
echo "RQ2 experiments completed!"
echo "Results saved in:"
echo "  - experiments/r_wo/"
echo "  - experiments/rw_wo/"
echo "=========================================="

# Different Setting: Run with custom YAML config
CONFIG_FILE=configs/rq2_experiment_1.yaml 

# Example: Run without YAML config (uses default config.py)
# python ./example/run_single_config_experiment.py \
#     --experiment-id rq2_1/r_wo \
#     --market-type reputation_only \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs 5 \
#     --config "${CONFIG_FILE}"


python ./example/run_single_config_experiment.py \
    --experiment-id rq2_1/rw_wo \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --runs 5 \
    --config "${CONFIG_FILE}"


# Different Setting: Run with custom YAML config
CONFIG_FILE=configs/rq2_experiment_2.yaml 

# python ./example/run_single_config_experiment.py \
#     --experiment-id rq2_2/r_wo \
#     --market-type reputation_only \
#     --communication none \
#     --communication-channel-type Fake \
#     --runs 5 \
#     --config "${CONFIG_FILE}"


python ./example/run_single_config_experiment.py \
    --experiment-id rq2_2/rw_wo \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --runs 5 \
    --config "${CONFIG_FILE}"