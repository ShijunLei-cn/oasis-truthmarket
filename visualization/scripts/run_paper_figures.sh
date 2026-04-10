#!/bin/bash
# ============================================================
# run_paper_figures.sh
# Figure generation entrypoint aligned with the NEW 3-RQ framing.
# ============================================================

set -euo pipefail

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
EXPERIMENT_PREFIX="experiments/${MODEL_TYPE}/paper_important_results"
OUTPUT_BASE="visualization/figs/${MODEL_TYPE}/paper_important_results"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "=========================================="
echo "Paper Figure Generation (New RQ Mapping)"
echo "Model   : ${MODEL_TYPE}"
echo "Data    : ${EXPERIMENT_PREFIX}"
echo "Output  : ${OUTPUT_BASE}"
echo "=========================================="

# ------------------------------------------------------------------
# RQ1: Vulnerability intention in reputation-only market
# ------------------------------------------------------------------
echo ""
echo "── RQ1: Rep-only Vulnerability Intention ─────────────"
python3 visualization/scripts/generate_rq1_figures.py \
    --r-dir  "${EXPERIMENT_PREFIX}/rq1_intent/r_wo" \
    --output-dir "${OUTPUT_BASE}/rq1" \
    --rep-only-only

if [ -f "${OUTPUT_BASE}/rq1/rq1_2_rep_only_manipulation_detection.png" ]; then
    cp "${OUTPUT_BASE}/rq1/rq1_2_rep_only_manipulation_detection.png" \
       "${OUTPUT_BASE}/rq1/rq1_intent_rep_only_manipulation_detection.png"
fi

# ------------------------------------------------------------------
# RQ2: Warrant welfare (rep vs rep+warrant, no communication)
# Uses original generator_rq1 pipeline then renames outputs to rq2_*
# ------------------------------------------------------------------
echo ""
echo "── RQ2: Warrant Welfare ──────────────────────────────"
python3 visualization/scripts/generate_rq1_figures.py \
    --r-dir  "${EXPERIMENT_PREFIX}/rq2_welfare/r_wo" \
    --rw-dir "${EXPERIMENT_PREFIX}/rq2_welfare/rw_wo" \
    --output-dir "${OUTPUT_BASE}/rq2"

for src in "${OUTPUT_BASE}/rq2"/rq1_*.png; do
    if [ -f "${src}" ]; then
        dst="${src/rq1_/rq2_}"
        cp "${src}" "${dst}"
    fi
done

# ------------------------------------------------------------------
# RQ3: Communication interference & resistance (old rq2 setting)
# ------------------------------------------------------------------
echo ""
echo "── RQ3: Communication Interference & Resistance ─────"
python3 visualization/scripts/generate_rq2_figures.py \
    --base-dir   "${EXPERIMENT_PREFIX}/rq3_resilience" \
    --baseline-dir "${EXPERIMENT_PREFIX}/rq2_welfare" \
    --output-dir "${OUTPUT_BASE}/rq3" \
    --file-prefix "rq3"

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
