#!/bin/bash
# Run Ablation Studies and Generate Visualizations
# Usage: ./run_ablation.sh [temperature|market_params|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

ABLATION_TYPE=${1:-temperature}

echo "=========================================="
echo "ABLATION STUDY: $ABLATION_TYPE"
echo "=========================================="

# Run the ablation study
python example/run_ablation_study.py --type "$ABLATION_TYPE"

# Find the latest ablation experiment
LATEST_EXP=$(ls -td experiments/ablation/${ABLATION_TYPE}_* 2>/dev/null | head -1)

if [ -z "$LATEST_EXP" ]; then
    echo "No ablation experiment found"
    exit 1
fi

# Extract relative path
ABLATION_BASE=$(echo "$LATEST_EXP" | sed 's|experiments/||')

echo ""
echo "=========================================="
echo "GENERATING VISUALIZATIONS"
echo "=========================================="

# Generate visualizations
python visualization/scripts/ablation_visualization.py "$ABLATION_BASE"

echo ""
echo "=========================================="
echo "COMPLETE"
echo "Results: $LATEST_EXP"
echo "Figures: visualization/figs/ablation/"
echo "=========================================="
