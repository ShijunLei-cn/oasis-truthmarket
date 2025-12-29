#!/bin/bash
# RQ2: Can mechanism design using financial penalties reduce wealth inequalities in the marketplace?
# This script runs experiments comparing Reputation-Only vs Reputation+Warrant markets without communication

echo "=========================================="
echo "RQ2 Experiment: Wealth Inequality Comparison"
echo "Comparing Reputation-Only vs Reputation+Warrant markets"
echo "=========================================="

# Reputation only market (no communication)
echo ""
echo "Running Reputation-Only Market experiments..."
python ./example/run_single_config_experiment.py \
    --experiment-id r_wo \
    --market-type reputation_only \
    --communication none \
    --communication-channel-type Fake \
    --runs 10

# Reputation and warrant market (no communication)
echo ""
echo "Running Reputation+Warrant Market experiments..."
python ./example/run_single_config_experiment.py \
    --experiment-id rw_wo \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --runs 10

echo ""
echo "=========================================="
echo "RQ2 experiments completed!"
echo "Results saved in:"
echo "  - experiments/r_wo/"
echo "  - experiments/rw_wo/"
echo "=========================================="