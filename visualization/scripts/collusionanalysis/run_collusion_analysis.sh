#!/bin/bash
# =============================================================================
# Run Collusion Analysis Visualization (RQ2)
# =============================================================================
# This script generates the RQ2-relevant collusion analysis visualizations:
#   - fig1_deception_by_collusion.png (核心发现：欺诈率对比)
#   - fig1_1_sankey_by_condition.png (桑基图：post collusion → 行为欺诈)
#   - collusion_consistency_rep_vs_warrant.png (一致性箱线图 + 4分类热力图)
#
# Usage:
#   ./run_collusion_analysis.sh              # Default paths
#   ./run_collusion_analysis.sh --data-dir /path/to/data --output-dir /path/to/output
#
# =============================================================================

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Default paths (newresults)
DATA_DIR="${PROJECT_ROOT}/experiments/gpt-4o-mini/newresults/data"
OUTPUT_DIR="${PROJECT_ROOT}/figs/gpt-4o-mini/newresults/collusion_analysis"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--data-dir <path>] [--output-dir <path>]"
            echo ""
            echo "Options:"
            echo "  --data-dir      Path to data directory (default: ${DATA_DIR})"
            echo "  --output-dir    Path to output directory (default: ${OUTPUT_DIR})"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "============================================================================"
echo "Collusion Analysis Visualization Generator (RQ2)"
echo "============================================================================"
echo ""
echo "Project root: ${PROJECT_ROOT}"
echo "Data directory: ${DATA_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if data directory exists
if [ ! -d "${DATA_DIR}" ]; then
    echo "ERROR: Data directory not found: ${DATA_DIR}"
    exit 1
fi

# Check if case_analysis subdirectory exists
if [ ! -d "${DATA_DIR}/case_analysis" ]; then
    echo "ERROR: case_analysis directory not found in: ${DATA_DIR}"
    exit 1
fi

# Check required data files
REQUIRED_FILES=(
    "posts_labeled.jsonl"
)

echo "Checking required data files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${DATA_DIR}/case_analysis/${file}" ]; then
        echo "WARNING: Missing data file: ${DATA_DIR}/case_analysis/${file}"
    else
        echo "  ✓ ${file}"
    fi
done
echo ""

# Run the visualization script
echo "Running collusion analysis visualization..."
echo "----------------------------------------------------------------------------"
cd "${PROJECT_ROOT}"
python3 "${SCRIPT_DIR}/collusion_analysis.py" \
    --data-dir "${DATA_DIR}" \
    --output-dir "${OUTPUT_DIR}"

# Check if figures were generated
echo ""
echo "----------------------------------------------------------------------------"
echo "Generated figures:"
echo ""
if [ -d "${OUTPUT_DIR}" ]; then
    for fig in "${OUTPUT_DIR}"/*.png; do
        if [ -f "$fig" ]; then
            size=$(du -h "$fig" | cut -f1)
            echo "  ✓ $(basename $fig) (${size})"
        fi
    done
fi

echo ""
echo "============================================================================"
echo "Done! All figures saved to: ${OUTPUT_DIR}"
echo "============================================================================"
