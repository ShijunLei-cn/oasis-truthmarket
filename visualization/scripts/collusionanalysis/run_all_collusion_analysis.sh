#!/bin/bash
# =============================================================================
# Run Complete Collusion Analysis Pipeline
# =============================================================================
# This script runs all collusion analysis components:
# 1. Statistical summary generation
# 2. Posts data analysis
# 3. Visualization generation
#
# Usage:
#   ./run_all_collusion_analysis.sh              # Default paths
#   ./run_all_collusion_analysis.sh --data-dir /path/to/data
# =============================================================================

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Default paths
DATA_DIR="${PROJECT_ROOT}/data"
OUTPUT_DIR="${PROJECT_ROOT}/visualization/figs/cache/collusion_analysis"

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
            exit 1
            ;;
    esac
done

echo "============================================================================"
echo "Complete Collusion Analysis Pipeline"
echo "============================================================================"
echo ""
echo "Project root: ${PROJECT_ROOT}"
echo "Data directory: ${DATA_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Change to project root
cd "${PROJECT_ROOT}"

# =============================================================================
# Step 1: Statistical Summary
# =============================================================================
echo ""
echo "============================================================================"
echo "Step 1: Generating Statistical Summary"
echo "============================================================================"
echo ""

python3 "${SCRIPT_DIR}/collusion_stats_summary.py" \
    --data-dir "${DATA_DIR}" \
    --output "${OUTPUT_DIR}/collusion_stats_summary.md"

# =============================================================================
# Step 2: Posts Data Analysis
# =============================================================================
echo ""
echo "============================================================================"
echo "Step 2: Analyzing Posts Data"
echo "============================================================================"
echo ""

python3 "${SCRIPT_DIR}/analyze_posts_collusion.py" \
    --data-dir "${DATA_DIR}" \
    --output-dir "${OUTPUT_DIR}"

# =============================================================================
# Step 3: Generate Visualizations
# =============================================================================
echo ""
echo "============================================================================"
echo "Step 3: Generating Visualizations"
echo "============================================================================"
echo ""

python3 "${SCRIPT_DIR}/collusion_analysis.py" \
    --data-dir "${DATA_DIR}" \
    --output-dir "${OUTPUT_DIR}"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "============================================================================"
echo "Pipeline Complete!"
echo "============================================================================"
echo ""
echo "Output files:"
echo ""

if [ -d "${OUTPUT_DIR}" ]; then
    for file in "${OUTPUT_DIR}"/*; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            ext="${file##*.}"
            if [ "$ext" = "png" ]; then
                echo "  📊 $(basename $file) (${size})"
            elif [ "$ext" = "md" ]; then
                echo "  📝 $(basename $file) (${size})"
            elif [ "$ext" = "json" ]; then
                echo "  📋 $(basename $file) (${size})"
            elif [ "$ext" = "csv" ]; then
                echo "  📋 $(basename $file) (${size})"
            else
                echo "  📄 $(basename $file) (${size})"
            fi
        fi
    done
fi

echo ""
echo "All results saved to: ${OUTPUT_DIR}"
echo "============================================================================"
