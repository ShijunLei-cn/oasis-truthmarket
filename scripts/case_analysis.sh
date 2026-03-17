#!/usr/bin/env bash
# Case Analysis Pipeline: Collusion Taxonomy of Seller Communication Posts
#
# Usage:
#   bash scripts/case_analysis.sh [extract|label|analyze|all]
#
# Defaults to 'all' (runs all three stages in sequence).
#
# Environment variables:
#   RQ2_DIR        Path to rq2 experiment results  (default: experiments/gpt-4o-mini/paper/rq2)
#   OUTPUT_DIR     Output directory                (default: data/case_analysis)
#   JUDGE_MODEL    OpenAI model used as LLM judge  (default: gpt-4o)
#   NO_RESUME      Set to 1 to re-label from scratch, ignoring existing output

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Configurable paths ──────────────────────────────────────────────────────
RQ2_DIR="${RQ2_DIR:-experiments/gpt-4o-mini/paper/rq2}"
OUTPUT_DIR="${OUTPUT_DIR:-data/case_analysis}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o}"
STAGE="${1:-all}"

# ── Resolve the analysis script ─────────────────────────────────────────────
ANALYSIS_SCRIPT="${SCRIPT_DIR}/esaypy/case_analysis.py"

if [[ ! -f "${ANALYSIS_SCRIPT}" ]]; then
    echo "[ERROR] Analysis script not found: ${ANALYSIS_SCRIPT}" >&2
    exit 1
fi

# ── Build optional flags ─────────────────────────────────────────────────────
RESUME_FLAG=""
if [[ "${NO_RESUME:-0}" == "1" ]]; then
    RESUME_FLAG="--no-resume"
fi

# ── Helper ───────────────────────────────────────────────────────────────────
run_stage() {
    local stage="$1"
    echo ""
    echo "=========================================="
    echo "Stage: ${stage}"
    echo "=========================================="
    shift
    python "${ANALYSIS_SCRIPT}" "${stage}" "$@"
}

# ── Main ──────────────────────────────────────────────────────────────────────
cd "${REPO_ROOT}"

echo "=========================================="
echo "Case Analysis Pipeline"
echo "  Stage      : ${STAGE}"
echo "  RQ2 dir    : ${RQ2_DIR}"
echo "  Output dir : ${OUTPUT_DIR}"
echo "  Judge model: ${JUDGE_MODEL}"
echo "=========================================="

case "${STAGE}" in

    extract)
        run_stage extract \
            --rq2-dir "${RQ2_DIR}" \
            --output-dir "${OUTPUT_DIR}"
        ;;

    label)
        run_stage label \
            --output-dir "${OUTPUT_DIR}" \
            --judge-model "${JUDGE_MODEL}" \
            ${RESUME_FLAG}
        ;;

    analyze)
        run_stage analyze \
            --output-dir "${OUTPUT_DIR}"
        ;;

    all)
        run_stage extract \
            --rq2-dir "${RQ2_DIR}" \
            --output-dir "${OUTPUT_DIR}"

        run_stage label \
            --output-dir "${OUTPUT_DIR}" \
            --judge-model "${JUDGE_MODEL}" \
            ${RESUME_FLAG}

        run_stage analyze \
            --output-dir "${OUTPUT_DIR}"
        ;;

    *)
        echo "[ERROR] Unknown stage '${STAGE}'. Use: extract | label | analyze | all" >&2
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Done. Results in: ${OUTPUT_DIR}"
echo "=========================================="
