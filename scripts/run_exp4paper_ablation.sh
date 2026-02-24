#!/bin/bash
# Comprehensive experiment script for paper experiments
# Now using 3 RQs: RQ1_probe (cognitive), RQ2 seller comm, RQ3 buyer comm

echo "=========================================="
echo "Paper Experiments: Comprehensive Run"
echo "=========================================="

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
SAFE_MODEL_TYPE="${MODEL_TYPE//-/_}"
CONFIG_FILE="${CONFIG_FILE:-configs/rq2_experiment_0_${SAFE_MODEL_TYPE}.yaml}"

echo "Using config file: ${CONFIG_FILE}"
echo "Model type: ${MODEL_TYPE}"

# All hyperparameters are sourced from the YAML config; avoid CLI overrides to keep precedence clear.

# ==================== RQ1_probe: Cognitive Probing ====================
echo ""
echo "=========================================="
echo "RQ1_probe: Cognitive Probing for Reputation Manipulation"
echo "=========================================="

# Reputation only market
echo ""
echo "Running Reputation-Only Market experiments..."
python ./example/run_rq1_experiment.py \
    --market-type reputation_only \
    --output-dir experiments/${MODEL_TYPE}/paper/rq1/r_wo \
    --config "${CONFIG_FILE}"

# Reputation and warrant market
echo ""
echo "Running Reputation+Warrant Market experiments..."
python ./example/run_rq1_experiment.py \
    --market-type reputation_and_warrant \
    --output-dir experiments/${MODEL_TYPE}/paper/rq1/rw_wo \
    --config "${CONFIG_FILE}"

# ==================== RQ2: Seller Communication (with baseline) ====================
echo ""
echo "=========================================="
echo "RQ2: Group-Level Deception Dynamics (Seller Communication)"
echo "=========================================="

# Baseline no communication
echo ""
echo "Running Reputation-Only Market (no communication)..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper/rq2/r_wo \
    --market-type reputation_only \
    --communication none \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

echo ""
echo "Running Reputation+Warrant Market (no communication)..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper/rq2/rw_wo \
    --market-type reputation_and_warrant \
    --communication none \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}


# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_R_policy_making \
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
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_R_policy_making \
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
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_R_pressure_quickprofits \
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
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_R_pressure_quickprofits \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation only market - Real channel
echo ""
echo "Running Reputation-Only + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_R_psychological-based-attack \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Real \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}


# Reputation and warrant market - Real channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_R_psychological-based-attack \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Real \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}




echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_F_policy_making \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}

# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_F_policy_making \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller policy_making \
    ${MODEL_ARGS}


# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_F_pressure_quickprofits \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_F_pressure_quickprofits \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller pressure_quickprofits \
    ${MODEL_ARGS}


# Reputation only market - Fake channel
echo ""
echo "Running Reputation-Only + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/r_wsc_F_psychological-based-attack \
    --market-type reputation_only \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}


# Reputation and warrant market - Fake channel
echo ""
echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
python ./example/run_single_config_ablation_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq2/rw_wsc_F_psychological-based-attack \
    --market-type reputation_and_warrant \
    --communication seller \
    --communication-channel-type Fake \
    --config "${CONFIG_FILE}" \
    --Posts4Seller psychological-based-attack \
    ${MODEL_ARGS}

# ==================== RQ3: Buyer Communication ====================
echo ""
echo "=========================================="
echo "RQ3: Buyer Adaptation Mechanisms (Buyer Communication)"
echo "=========================================="

echo ""
echo "Running Reputation-Only + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wbc_F \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

echo ""
echo "Running Reputation-Only + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/r_wbc_R \
    --market-type reputation_only \
    --communication buyer \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

echo ""
echo "Running Reputation+Warrant + Buyer Communication + Fake Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wbc_F \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Fake \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

echo ""
echo "Running Reputation+Warrant + Buyer Communication + Real Channel..."
python ./example/run_single_config_experiment.py \
    --experiment-id ${MODEL_TYPE}/paper_largescale/rq3/rw_wbc_R \
    --market-type reputation_and_warrant \
    --communication buyer \
    --communication-channel-type Real \
    --runs ${RUNS} \
    --config "${CONFIG_FILE}" \
    ${MODEL_ARGS}

echo ""
echo "=========================================="
echo "All paper ablation experiments submitted!"
echo "=========================================="