#!/bin/bash
# =============================================================================
# Run Collusion Analysis Visualization
# =============================================================================
# This script generates all collusion analysis visualizations for the 
# TruthMarketTwin paper.
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
DATA_DIR="${PROJECT_ROOT}/data"
OUTPUT_DIR="${PROJECT_ROOT}/visualization/figs/paper/collusion_analysis"

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
echo "Collusion Analysis Visualization Generator"
echo "============================================================================"
echo ""
echo "Project root: ${PROJECT_ROOT}"
echo "Data directory: ${DATA_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

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

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if required data files exist
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

# Check Python and required packages
echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Try to import required packages
if ! python3 -c "import matplotlib" 2>/dev/null; then
    echo "WARNING: matplotlib not installed, attempting to install..."
    pip install matplotlib numpy pandas scipy --quiet
fi

echo "  ✓ Python: $(python3 --version)"
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
