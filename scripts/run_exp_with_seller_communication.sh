#!/bin/bash
# RQ3: Group-Level Deception Dynamics
# When sellers can observe market behavior, does group-level deception emerge through social learning?
# This script runs seller communication experiments with Fake and Real channels
# Explores whether deceptive strategies spread through agent observation and imitation

echo "=========================================="
echo "RQ3 Experiment: Group-Level Deception Dynamics"
echo "=========================================="

# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id r_wsc_F \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --runs 5

# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id r_wsc_R \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Real \
    --runs 5

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id rw_wsc_F \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --runs 5

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id rw_wsc_R \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --runs 5

echo ""
echo "=========================================="
echo "RQ3 experiments completed!"
echo "Generating visualization..."
echo "=========================================="


# Analyze collusion behavior for all seller communication experiments
echo ""
echo "=========================================="
echo "Running Collusion Analysis for Seller Communication Experiments..."
echo "=========================================="

python3 visualization/overseer_draw.py --experiment-ids r_wsc_F r_wsc_R rw_wsc_F rw_wsc_R

echo ""
echo "Collusion analysis complete!"
echo "Results saved in: analysis/communication_effects/"
echo "=========================================="


echo ""
echo "RQ3 analysis complete!"
echo "Results saved in:"
echo "  - experiments/r_wsc_F/"
echo "  - experiments/r_wsc_R/"
echo "  - experiments/rw_wsc_F/"
echo "  - experiments/rw_wsc_R/"
echo "=========================================="