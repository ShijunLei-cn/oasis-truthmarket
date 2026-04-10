#!/bin/bash
# =============================================================================
# Run Collusion Analysis Visualization (RQ2)
# =============================================================================
# This script generates the RQ2-relevant collusion analysis visualizations:
#   - fig1_deception_by_collusion.png (核心发现：欺诈率对比)
#   - fig1_1_sankey_by_condition.png (桑基图：post collusion → 行为欺诈)
#   - fig1_2_embedding_cluster.png (UMAP散点图 + 词云)
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

# Default paths
DATA_DIR="${PROJECT_ROOT}/experiments/gpt-4o-mini/paper_important_results/data"
OUTPUT_DIR="${PROJECT_ROOT}/visualization/figs/gpt-4o-mini/paper_important_results/collusion_analysis"

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
    "deception_rate_by_collusion.csv"
    "type_distribution_by_condition.csv"
    "type_distribution_by_round.csv"
    "qualitative_examples.json"
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

# Run 2x2 analysis
echo ""
echo "----------------------------------------------------------------------------"
echo "Running 2x2 collusion analysis..."
echo "----------------------------------------------------------------------------"
python3 "${SCRIPT_DIR}/analyze_2x2_collusion.py" --data-dir "${DATA_DIR}/case_analysis"

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
