#!/bin/bash
# RQ4: Buyer Adaptation Mechanisms
# When buyers can share information, do they collectively adapt to avoid dishonest sellers over time?
# This script runs buyer communication experiments with Fake and Real channels
# Examines the defensive capabilities of buyer agents and their ability to learn from shared experiences

echo "=========================================="
echo "RQ4 Experiment: Buyer Adaptation Mechanisms"
echo "=========================================="

# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id r_wbc_F \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Fake \
    --runs 5

# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id r_wbc_R \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Real \
    --runs 5

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id rw_wbc_F \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Fake \
    --runs 5

# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id rw_wbc_R \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Real \
    --runs 5
