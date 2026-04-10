#!/bin/bash
# ============================================================
# run_paper_figures.sh
# Figure generation entrypoint aligned with the NEW 3-RQ framing.
# ============================================================

set -euo pipefail

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
LOCKED_EXPERIMENT_PREFIX="./experiments/paper_important_results"
if [ -n "${EXPERIMENT_PREFIX:-}" ] && [ "${EXPERIMENT_PREFIX}" != "${LOCKED_EXPERIMENT_PREFIX}" ]; then
    echo "ERROR: EXPERIMENT_PREFIX is locked for this stage."
    echo "Allowed only: ${LOCKED_EXPERIMENT_PREFIX}"
    echo "Received    : ${EXPERIMENT_PREFIX}"
    exit 1
fi
EXPERIMENT_PREFIX="${LOCKED_EXPERIMENT_PREFIX}"
if [ ! -d "${EXPERIMENT_PREFIX}" ]; then
    echo "ERROR: experiment directory not found: ${EXPERIMENT_PREFIX}"
    exit 1
fi
OUTPUT_BASE="./figs/${MODEL_TYPE}/paper_important_results"

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

echo "=========================================="
echo "Paper Figure Generation (New RQ Mapping)"
echo "Model   : ${MODEL_TYPE}"
echo "Data    : ${EXPERIMENT_PREFIX}"
echo "Output  : ${OUTPUT_BASE}"
echo "=========================================="

echo ""
echo "── Generating RQ1/RQ2/RQ3 Figures ────────────────────"
python3 visualization/scripts/generate_main_figures.py \
    --base-dir "${EXPERIMENT_PREFIX}" \
    --output-dir "${OUTPUT_BASE}"

echo ""
echo "── Generating Statistical Report ─────────────────────"
python3 visualization/scripts/generate_paper_stats_report.py \
    --base-dir "${EXPERIMENT_PREFIX}" \
    --output-dir "${OUTPUT_BASE}/stats"

echo ""
echo "=========================================="
echo "All figures generated with new RQ1/RQ2/RQ3 mapping."
echo "=========================================="
echo ""
echo "RQ1:"
echo "  ${OUTPUT_BASE}/rq1/rq1_intent_rep_only_manipulation_detection.png"
echo "RQ2:"
echo "  ${OUTPUT_BASE}/rq2/rq2_warrant_vs_rep_deception_and_profit.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_exit_loophole_vulnerability.png"
echo "RQ3:"
echo "  ${OUTPUT_BASE}/rq3/rq3_seller_comm_deception_by_constraint.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_profit_decomposition_honest_vs_dishonest.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_ALL_markettype_hqfake_profit.png"
echo "Stats:"
echo "  ${OUTPUT_BASE}/stats/stats_report.txt"
echo "  ${OUTPUT_BASE}/stats/stats_report.tex"
echo "  ${OUTPUT_BASE}/stats/stats_report.csv"
