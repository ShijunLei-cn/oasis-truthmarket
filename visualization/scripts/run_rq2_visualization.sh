#!/bin/bash
# RQ2 Market Mechanism Comparison Visualization
# Generate academic-style visualizations comparing Reputation-Only vs Reputation+Warrant

set -e

# Default experiment IDs (update these based on your actual experiment IDs)
R_EXP_ID="${R_EXP_ID:-r_wo}"
RW_EXP_ID="${RW_EXP_ID:-rw_wo}"

# Check if experiment IDs are provided as arguments
if [ $# -ge 2 ]; then
    R_EXP_ID="$1"
    RW_EXP_ID="$2"
fi

echo "=========================================="
echo "RQ2 Market Mechanism Visualization"
echo "=========================================="
echo "Reputation-Only Experiment: $R_EXP_ID"
echo "Reputation+Warrant Experiment: $RW_EXP_ID"
echo ""

# Check if analysis data exists
if [ ! -f "analysis/${R_EXP_ID}/aggregated/aggregated_statistics.json" ]; then
    echo "Error: Analysis data not found for $R_EXP_ID"
    echo "Please run multi-run analysis first:"
    echo "  python analysis/multi_run_analysis.py --experiment_id $R_EXP_ID"
    exit 1
fi

if [ ! -f "analysis/${RW_EXP_ID}/aggregated/aggregated_statistics.json" ]; then
    echo "Error: Analysis data not found for $RW_EXP_ID"
    echo "Please run multi-run analysis first:"
    echo "  python analysis/multi_run_analysis.py --experiment_id $RW_EXP_ID"
    exit 1
fi

# Generate visualizations
echo "Generating visualizations..."
python visualization/scripts/rq2_visualization.py \
    --r-exp "$R_EXP_ID" \
    --rw-exp "$RW_EXP_ID"

echo ""
echo "=========================================="
echo "Visualization complete!"
echo "=========================================="

