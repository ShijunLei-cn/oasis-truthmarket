#!/bin/bash
# Comprehensive experiment script for 0410 experiments
# Now using 3 RQs: RQ1_probe (cognitive), RQ2 seller comm, RQ3 buyer comm

echo "=========================================="
echo "Paper Experiments: Comprehensive Run"
echo "=========================================="

# Default configuration file (can be overridden via CONFIG_FILE environment variable)
CONFIG_FILE="${CONFIG_FILE:-configs/rq2_experiment_0_gpt_4o_mini.yaml}"

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
echo "Using config file: ${CONFIG_FILE}"
echo "Model type: ${MODEL_TYPE}"

# All hyperparameters are taken from the YAML config; avoid CLI overrides to keep precedence clear.
# If needed, pass alternative configs via CONFIG_FILE.


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
    --output-dir experiments/${MODEL_TYPE}/0410/rq1/r_wo \
    --config "${CONFIG_FILE}"

# Reputation and warrant market
echo ""
echo "Running Reputation+Warrant Market experiments..."
python ./example/run_rq1_experiment.py \
    --market-type reputation_and_warrant \
    --output-dir experiments/${MODEL_TYPE}/0410/rq1/rw_wo \
    --config "${CONFIG_FILE}"

# # ==================== RQ2: Seller Communication ====================
# echo ""
# echo "=========================================="
# echo "RQ2: Group-Level Deception Dynamics (Seller Communication)"
# echo "=========================================="

# # Baseline no-communication
# echo ""
# echo "Running Reputation-Only Market (no communication)..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq1/r_wo \
#     --market-type reputation_only \
#     --communication none \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}"

# echo ""
# echo "Running Reputation+Warrant Market (no communication)..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq1/rw_wo \
#     --market-type reputation_and_warrant \
#     --communication none \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}"


# # Reputation only market - Real channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_R_policy_making \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller policy_making

# # Reputation and warrant market - Real channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_R_policy_making \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller policy_making


# # Reputation only market - Real channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_R_pressure_quickprofits \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller pressure_quickprofits


# # Reputation and warrant market - Real channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_R_pressure_quickprofits \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller pressure_quickprofits


# # Reputation only market - Real channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_R_psychological-based-attack \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller psychological-based-attack


# # Reputation and warrant market - Real channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Real Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_R_psychological-based-attack \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller psychological-based-attack




# echo ""
# echo "Running Reputation-Only + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_F_policy_making \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     # --Posts4Seller policy_making 

# # Reputation and warrant market - Fake channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_F_policy_making \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     # --Posts4Seller policy_making 


# # Reputation only market - Fake channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_F_pressure_quickprofits \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     # --Posts4Seller pressure_quickprofits 


# # Reputation and warrant market - Fake channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_F_pressure_quickprofits \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     # --Posts4Seller pressure_quickprofits 


# # Reputation only market - Fake channel
# echo ""
# echo "Running Reputation-Only + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/r_wsc_F_psychological-based-attack \
#     --market-type reputation_only \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     # --Posts4Seller psychological-based-attack 


# # Reputation and warrant market - Fake channel
# echo ""
# echo "Running Reputation+Warrant + Seller Communication + Fake Channel..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq2/rw_wsc_F_psychological-based-attack \
#     --market-type reputation_and_warrant \
#     --communication seller \
#     --communication-channel-type Fake \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller psychological-based-attack 



# #  ==================== RQ3: Buyer Communication (Adversarial Setting) ====================
# echo ""
# echo "=========================================="
# echo "RQ3: Buyer Collective Defense Against Seller Coordination"
# echo "=========================================="
# # #
# # ADVERSARIAL RQ3 DESIGN (clean causal isolation):

# #   Baseline (Seller comm active, NO buyer comm):
# #     → Reuse existing RQ2 Real-channel conditions:
# #         rq2/r_wsc_R_pressure_quickprofits   (Rep, seller-only comm, Real, PQP)
# #         rq2/rw_wsc_R_pressure_quickprofits  (RW,  seller-only comm, Real, PQP)

# #   Treatment (Both seller + buyer comm, Real channel):
# #     → New conditions below:
# #         rq3/r_both_R_pqp    (Rep, both comm, Real, PQP)
# #         rq3/rw_both_R_pqp   (RW,  both comm, Real, PQP)

# #   Research Question:
# #     "When sellers are already coordinating deception under Pressure-Quick-Profits,
# #      does adding buyer-to-buyer communication enable collective defense?"

# #   The ONLY difference between baseline and treatment is whether BUYERS can communicate.
# #   Seller communication and constraints are identical across all 4 conditions.


# echo ""
# echo "Running Rep + Both Comm + Real + Pressure-Quick-Profits (RQ3 Treatment)..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq3/r_both_R_pqp \
#     --market-type reputation_only \
#     --communication both \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller pressure_quickprofits

# echo ""
# echo "Running Rep+Warrant + Both Comm + Real + Pressure-Quick-Profits (RQ3 Treatment)..."
# python ./example/run_single_config_experiment.py \
#     --experiment-id ${MODEL_TYPE}/0410/rq3/rw_both_R_pqp \
#     --market-type reputation_and_warrant \
#     --communication both \
#     --communication-channel-type Real \
#     --config "${CONFIG_FILE}" \
#     --Posts4Seller pressure_quickprofits

# echo ""
# echo "=========================================="
# echo "All 0410 ablation experiments submitted!"
# echo "=========================================="