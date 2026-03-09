#!/bin/bash
# RQ4 Communication Channel Impact Visualization
# Generate academic-style visualizations comparing 4 conditions: R_F, R_R, RW_F, RW_R

set -e

# Default experiment IDs (update these based on your actual experiment IDs)
R_F_EXP_ID="${R_F_EXP_ID:-r_wbc_F}"
R_R_EXP_ID="${R_R_EXP_ID:-r_wbc_R}"
RW_F_EXP_ID="${RW_F_EXP_ID:-rw_wbc_F}"
RW_R_EXP_ID="${RW_R_EXP_ID:-rw_wbc_R}"

# Check if experiment IDs are provided as arguments
if [ $# -ge 4 ]; then
    R_F_EXP_ID="$1"
    R_R_EXP_ID="$2"
    RW_F_EXP_ID="$3"
    RW_R_EXP_ID="$4"
fi

# echo "=========================================="
# echo "RQ4 Communication Channel Visualization"
# echo "=========================================="
# echo "R_F Experiment: $R_F_EXP_ID"
# echo "R_R Experiment: $R_R_EXP_ID"
# echo "RW_F Experiment: $RW_F_EXP_ID"
# echo "RW_R Experiment: $RW_R_EXP_ID"
# echo ""

# # Check if analysis data exists
# for exp_id in "$R_F_EXP_ID" "$R_R_EXP_ID" "$RW_F_EXP_ID" "$RW_R_EXP_ID"; do
#     if [ ! -f "analysis/${exp_id}/aggregated/aggregated_statistics.json" ]; then
#         echo "Warning: Analysis data not found for $exp_id"
#         echo "Please run multi-run analysis first:"
#         echo "  python analysis/multi_run_analysis.py --experiment_id $exp_id"
#     fi
# done

# # Generate visualizations
# echo "Generating visualizations..."
# python visualization/scripts/rq4_visualization.py \
#     --r-f "$R_F_EXP_ID" \
#     --r-r "$R_R_EXP_ID" \
#     --rw-f "$RW_F_EXP_ID" \
#     --rw-r "$RW_R_EXP_ID"

# echo ""
# echo "=========================================="
# echo "Visualization complete!"
# echo "=========================================="


EXP_PREFIX="gpt-4o-mini/paper_largescale/rq4"

python visualization/scripts/bkp/rq4_visualization.py \
    --r-f "$EXP_PREFIX/$R_F_EXP_ID" \
    --r-r "$EXP_PREFIX/$R_R_EXP_ID" \
    --rw-f "$EXP_PREFIX/$RW_F_EXP_ID" \
    --rw-r "$EXP_PREFIX/$RW_R_EXP_ID"
