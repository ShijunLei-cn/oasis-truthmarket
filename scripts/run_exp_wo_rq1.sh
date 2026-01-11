#!/bin/bash
# RQ1: Cognitive Probing for Reputation Manipulation
# This script runs experiments to study how agents exploit reputation mechanisms
# Comparing Reputation-Only vs Reputation+Warrant markets

echo "=========================================="
echo "RQ1 Experiment: Cognitive Probing for Reputation Manipulation"
echo "Comparing Reputation-Only vs Reputation+Warrant markets"
echo "=========================================="

# Configuration file path (optional - if not provided, uses default config.py)
CONFIG_FILE="${CONFIG_FILE:-configs/rq1_experiment_0.yaml}"

# Experiment configuration
RUNS=10
ROUNDS=10
SELLERS=5
BUYERS=5
PROBE_INTERVAL=1

# Reputation only market
echo ""
echo "Running Reputation-Only Market experiments..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_rq1_experiment.py \
    --runs ${RUNS} \
    --rounds ${ROUNDS} \
    --sellers ${SELLERS} \
    --buyers ${BUYERS} \
    --market-type reputation_only \
    --output-dir experiments/rq1_0/r_wo \
    --probe-interval ${PROBE_INTERVAL} \
    --config "${CONFIG_FILE}"

# Reputation and warrant market
echo ""
echo "Running Reputation+Warrant Market experiments..."
echo "Using config: ${CONFIG_FILE:-default config.py}"
python ./example/run_rq1_experiment.py \
    --runs ${RUNS} \
    --rounds ${ROUNDS} \
    --sellers ${SELLERS} \
    --buyers ${BUYERS} \
    --market-type reputation_and_warrant \
    --output-dir experiments/rq1_0/rw_wo \
    --probe-interval ${PROBE_INTERVAL} \
    --config "${CONFIG_FILE}"

echo ""
echo "=========================================="
echo "RQ1 experiments completed!"
echo "Results saved in:"
echo "  - experiments/rq1_0/r_wo/"
echo "  - experiments/rq1_0/rw_wo/"
echo "=========================================="

# Example: Run without YAML config (uses default config.py)
# python ./example/run_rq1_experiment.py \
#     --runs 10 \
#     --rounds 10 \
#     --sellers 5 \
#     --buyers 5 \
#     --market-type reputation_only \
#     --output-dir experiments/rq1_0/r_wo \
#     --probe-interval 1

# Example: Run with custom YAML config
# CONFIG_FILE=configs/custom_rq1_config.yaml python ./example/run_rq1_experiment.py \
#     --runs 10 \
#     --rounds 10 \
#     --sellers 5 \
#     --buyers 5 \
#     --market-type reputation_only \
#     --output-dir experiments/rq1_0/r_wo \
#     --probe-interval 1 \
#     --config "${CONFIG_FILE}"
