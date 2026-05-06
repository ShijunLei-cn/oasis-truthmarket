#!/bin/bash
# Paper experiment runner (new 3-RQ framing)
# Delegates to:
#   scripts/run_rq1_intent.sh
#   scripts/run_rq2_welfare.sh
#   scripts/run_rq3_resilience.sh

set -euo pipefail

echo "=========================================="
echo "Paper Experiments: New 3-RQ Pipeline"
echo "=========================================="

CONFIG_FILE="${CONFIG_FILE:-configs/sim_gemini3f_10s_10b_10r_runs5_base.yaml}"
MODEL_TYPE="${MODEL_TYPE:-gemini-3-flash-preview}"
EXP_ROOT="${MODEL_TYPE}/paper_important_results"

echo "Using config file: ${CONFIG_FILE}"
echo "Model type: ${MODEL_TYPE}"
echo "Experiment root: experiments/${EXP_ROOT}"

CONFIG_FILE="${CONFIG_FILE}" MODEL_TYPE="${MODEL_TYPE}" EXP_ROOT="${EXP_ROOT}" \
    ./scripts/run_rq1_intent.sh
CONFIG_FILE="${CONFIG_FILE}" MODEL_TYPE="${MODEL_TYPE}" EXP_ROOT="${EXP_ROOT}" \
    ./scripts/run_rq2_welfare.sh
CONFIG_FILE="${CONFIG_FILE}" MODEL_TYPE="${MODEL_TYPE}" EXP_ROOT="${EXP_ROOT}" \
    ./scripts/run_rq3_resilience.sh

echo ""
echo "=========================================="
echo "All experiments submitted for new RQ1/RQ2/RQ3 framing."
echo "=========================================="
