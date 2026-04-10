#!/bin/bash
# ============================================================
# run_paper_figures.sh
# One-command script to generate all paper figures (RQ1/2/3).
# Run from the project root directory.
# ============================================================

set -e

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXPERIMENT_PREFIX="experiments/${MODEL_TYPE}/paper_important_results"
OUTPUT_BASE="visualization/figs/${MODEL_TYPE}/paper_important_results"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "=========================================="
echo "Paper Figure Generation"
echo "Model   : ${MODEL_TYPE}"
echo "Data    : ${EXPERIMENT_PREFIX}"
echo "Output  : ${OUTPUT_BASE}"
echo "=========================================="

# ── RQ1 ──────────────────────────────────────────────────────
echo ""
echo "── RQ1: Warrant vs. Reputation-Only ──────────────────"
python3 visualization/scripts/generate_rq1_figures.py \
    --r-dir  "${EXPERIMENT_PREFIX}/rq1/r_wo" \
    --rw-dir "${EXPERIMENT_PREFIX}/rq1/rw_wo" \
    --output-dir "${OUTPUT_BASE}/rq1"

# ── RQ2 ──────────────────────────────────────────────────────
echo ""
echo "── RQ2: Seller Communication under Constraints ───────"
python3 visualization/scripts/generate_rq2_figures.py \
    --base-dir   "${EXPERIMENT_PREFIX}/rq2" \
    --output-dir "${OUTPUT_BASE}/rq2"

# ── RQ3 ──────────────────────────────────────────────────────
echo ""
echo "── RQ3: Buyer Communication & Collective Defense ─────"
python3 visualization/scripts/generate_rq3_figures.py \
    --base-dir   "${EXPERIMENT_PREFIX}/rq3" \
    --output-dir "${OUTPUT_BASE}/rq3"

echo ""
echo "── RQ3: Tables ───────────────────────────────────────"
python3 visualization/scripts/generate_rq3_tables.py \
    --base-dir   "${EXPERIMENT_PREFIX}" \
    --output-dir "visualization/table/paper_important_results/rq3"

# ── Statistical Significance Report ─────────────────────────
echo ""
echo "── Statistical Significance Report ───────────────────"
python3 visualization/scripts/generate_paper_stats_report.py \
    --base-dir   "${EXPERIMENT_PREFIX}" \
    --output-dir "${OUTPUT_BASE}/stats"

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "All figures and statistics generated!"
echo "=========================================="
echo ""
echo "Main paper figures:"
echo "  ${OUTPUT_BASE}/rq1/rq1_warrant_vs_rep_deception_and_profit.png"
echo "  ${OUTPUT_BASE}/rq1/rq1_1_manipulation_detection.png"
echo "  ${OUTPUT_BASE}/rq1/rq1_2_rep_only_manipulation_detection.png"
echo "  ${OUTPUT_BASE}/rq1/rq1_exit_loophole_vulnerability.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_seller_comm_deception_by_constraint.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_profit_decomposition_honest_vs_dishonest.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_All_constraints_combined.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_ALL_markettype_hqfake_profit.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_buyer_comm_market_outcomes.png"
echo ""
echo "Appendix figures:"
echo "  ${OUTPUT_BASE}/rq1/rq1_product_mix_appendix.png"
echo "  ${OUTPUT_BASE}/rq2/rq2_product_mix_appendix.png"
echo "  ${OUTPUT_BASE}/rq3/rq3_round_adaptation_appendix.png"
echo ""
echo "Statistical reports:"
echo "  ${OUTPUT_BASE}/stats/stats_report.txt   (human-readable p-values)"
echo "  ${OUTPUT_BASE}/stats/stats_report.tex   (LaTeX table for appendix)"
echo "  ${OUTPUT_BASE}/stats/stats_report.csv   (CSV for manual inspection)"
