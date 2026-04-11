#!/bin/bash
# ============================================================
# run_paper_figures.sh
# Figure generation entrypoint aligned with the NEW 3-RQ framing.
# ============================================================

set -euo pipefail

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
LOCKED_EXPERIMENT_PREFIX="./experiments/gpt-4o-mini/newresults"
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
OUTPUT_BASE="./figs/${MODEL_TYPE}/newresults"
TABLES_BASE="./tables/${MODEL_TYPE}/newresults"
GENERATE_STATS="${GENERATE_STATS:-0}"
GENERATE_TABLES="${GENERATE_TABLES:-1}"

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
if [ "${GENERATE_STATS}" = "1" ]; then
    echo "── Generating Statistical Report ─────────────────────"
    python3 visualization/scripts/generate_paper_stats_report.py \
        --base-dir "${EXPERIMENT_PREFIX}" \
        --output-dir "${OUTPUT_BASE}/stats"
else
    echo "── Statistical Report Skipped (GENERATE_STATS=${GENERATE_STATS}) ───"
fi

echo ""
if [ "${GENERATE_TABLES}" = "1" ]; then
    echo "── Generating LaTeX Tables ────────────────────────────"
    python3 visualization/scripts/generate_paper_tables.py \
        --base-dir "${EXPERIMENT_PREFIX}" \
        --output-dir "${TABLES_BASE}"
else
    echo "── Table Generation Skipped (GENERATE_TABLES=${GENERATE_TABLES}) ───"
fi

echo ""
echo "=========================================="
echo "All figures generated with new RQ1/RQ2/RQ3 mapping."
echo "=========================================="
echo ""
echo "RQ1:"
echo "  ${OUTPUT_BASE}/rq1/rq1_intent_rep_only_manipulation_detection.png"
echo "RQ2:"
echo "  ${OUTPUT_BASE}/rq2/rq2_warrant_vs_rep_welfare_overview.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_warrant_vs_rep_deception_and_profit.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_listed_vs_sold_quality.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_product_quality_over_rounds.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_warrant_micro_reasoning_impact.png"
echo "RQ3:"
echo "  ${OUTPUT_BASE}/rq3/rq3_welfare_overview.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_seller_comm_deception_by_constraint.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_profit_decomposition_honest_vs_dishonest.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_all_constraints_grouped.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_warrant_micro_reasoning_impact.png"
echo "Tables:"
echo "  ${TABLES_BASE}/all_tables.tex"
echo "  ${TABLES_BASE}/rq1/tab_rq1_intent_rep_only.tex"
echo "  ${TABLES_BASE}/rq2/tab_rq2_welfare_summary.tex"
echo "  ${TABLES_BASE}/rq2/tab_rq2_welfare_product_quality.tex"
echo "  ${TABLES_BASE}/rq3/tab_rq3_resilience_summary.tex"
echo "  ${TABLES_BASE}/rq3/tab_rq3_resilience_product_quality.tex"
if [ "${GENERATE_STATS}" = "1" ]; then
    echo "Stats:"
    echo "  ${OUTPUT_BASE}/stats/stats_report.txt"
    echo "  ${OUTPUT_BASE}/stats/stats_report.tex"
    echo "  ${OUTPUT_BASE}/stats/stats_report.csv"
fi
