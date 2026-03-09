#!/bin/bash
# Comprehensive visualization script for paper experiments
# Generates visualizations for RQ1, RQ2, RQ3, and RQ4
# Adapts to the experiment structure from run_exp4paper.sh

set -e

# Default experiment prefix (matches run_exp4paper.sh)
EXPERIMENT_PREFIX="${EXPERIMENT_PREFIX:-gpt-4o-mini/paper_largescale}"

# Ensure PYTHONPATH includes the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "=========================================="
echo "Paper Experiments Visualization"
echo "=========================================="
echo "Experiment Prefix: $EXPERIMENT_PREFIX"
echo ""


# ==================== RQ3: Seller Communication Visualization ====================
echo ""
echo "=========================================="
echo "RQ3: Group-Level Deception Dynamics (Seller Communication)"
echo "=========================================="

RQ3_R_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_R_policy_making"
RQ3_RW_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_R_policy_making"
RQ3_R_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_F_policy_making"
RQ3_RW_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_F_policy_making"

# Check if RQ3 experiments exist
if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
    echo "Generating RQ3 visualizations..."
    echo "  R_R: $RQ3_R_R_EXP_ID"
    echo "  RW_R: $RQ3_RW_R_EXP_ID"
    echo "  R_F: $RQ3_R_F_EXP_ID"
    echo "  RW_F: $RQ3_RW_F_EXP_ID"
    
    # Run multi-run analysis for all RQ3 experiments
    for exp_id in "$RQ3_R_R_EXP_ID" "$RQ3_RW_R_EXP_ID" "$RQ3_R_F_EXP_ID" "$RQ3_RW_F_EXP_ID"; do
        if [ -d "experiments/$exp_id" ]; then
            echo "  Running multi-run analysis for $exp_id..."
            python analysis/multi_run_analysis.py --experiment_id "$exp_id" || echo "  Warning: Analysis failed for $exp_id"
        fi
    done
    
    # Generate visualizations (only need R_R and RW_R for ablation study)
    if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
        echo "  Generating comparison visualizations..."
        python visualization/scripts/rq3_visualization.py \
            --r-r "$RQ3_R_R_EXP_ID" \
            --rw-r "$RQ3_RW_R_EXP_ID" \
            --r-f "$RQ3_R_F_EXP_ID" \
            --rw-f "$RQ3_RW_F_EXP_ID" || echo "  Warning: RQ3 visualization failed"
    else
        echo "  Warning: At least one experiment required for RQ3 visualization"
        echo "  Missing experiments will be skipped"
    fi
    
    echo "RQ3 visualization complete!"
else
    echo "Skipping RQ3: Experiment directories not found"
fi


RQ3_R_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_R_pressure_quickprofits"
RQ3_RW_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_R_pressure_quickprofits"
RQ3_R_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_F_pressure_quickprofits"
RQ3_RW_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_F_pressure_quickprofits"
if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
    echo "Generating RQ3 visualizations..."
    echo "  R_R: $RQ3_R_R_EXP_ID"
    echo "  RW_R: $RQ3_RW_R_EXP_ID"
    echo "  R_F: $RQ3_R_F_EXP_ID"
    echo "  RW_F: $RQ3_RW_F_EXP_ID"
    
    # Run multi-run analysis for all RQ3 experiments
    for exp_id in "$RQ3_R_R_EXP_ID" "$RQ3_RW_R_EXP_ID" "$RQ3_R_F_EXP_ID" "$RQ3_RW_F_EXP_ID"; do
        if [ -d "experiments/$exp_id" ]; then
            echo "  Running multi-run analysis for $exp_id..."
            python analysis/multi_run_analysis.py --experiment_id "$exp_id" || echo "  Warning: Analysis failed for $exp_id"
        fi
    done
    
    # Generate visualizations (only need R_R and RW_R for ablation study)
    if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
        echo "  Generating comparison visualizations..."
        python visualization/scripts/rq3_visualization.py \
            --r-r "$RQ3_R_R_EXP_ID" \
            --rw-r "$RQ3_RW_R_EXP_ID" \
            --r-f "$RQ3_R_F_EXP_ID" \
            --rw-f "$RQ3_RW_F_EXP_ID" || echo "  Warning: RQ3 visualization failed"
    else
        echo "  Warning: At least one experiment required for RQ3 visualization"
        echo "  Missing experiments will be skipped"
    fi
    
    echo "RQ3 visualization complete!"
else
    echo "Skipping RQ3: Experiment directories not found"
fi


RQ3_R_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_R_psychological-based-attack"
RQ3_RW_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_R_psychological-based-attack"
RQ3_R_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_F_psychological-based-attack"
RQ3_RW_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_F_psychological-based-attack"
if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
    echo "Generating RQ3 visualizations..."
    echo "  R_R: $RQ3_R_R_EXP_ID"
    echo "  RW_R: $RQ3_RW_R_EXP_ID"
    echo "  R_F: $RQ3_R_F_EXP_ID"
    echo "  RW_F: $RQ3_RW_F_EXP_ID"
    
    # Run multi-run analysis for all RQ3 experiments
    for exp_id in "$RQ3_R_R_EXP_ID" "$RQ3_RW_R_EXP_ID" "$RQ3_R_F_EXP_ID" "$RQ3_RW_F_EXP_ID"; do
        if [ -d "experiments/$exp_id" ]; then
            echo "  Running multi-run analysis for $exp_id..."
            python analysis/multi_run_analysis.py --experiment_id "$exp_id" || echo "  Warning: Analysis failed for $exp_id"
        fi
    done
    
    # Generate visualizations (only need R_R and RW_R for ablation study)
    if [ -d "experiments/$RQ3_R_R_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ] || [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_F_EXP_ID" ]; then
        echo "  Generating comparison visualizations..."
        python visualization/scripts/rq3_visualization.py \
            --r-r "$RQ3_R_R_EXP_ID" \
            --rw-r "$RQ3_RW_R_EXP_ID" \
            --r-f "$RQ3_R_F_EXP_ID" \
            --rw-f "$RQ3_RW_F_EXP_ID" || echo "  Warning: RQ3 visualization failed"
    else
        echo "  Warning: At least one experiment required for RQ3 visualization"
        echo "  Missing experiments will be skipped"
    fi
    
    echo "RQ3 visualization complete!"
else
    echo "Skipping RQ3: Experiment directories not found"
fi


echo ""
echo "=========================================="
echo "All visualizations complete!"
echo "=========================================="
echo ""
echo "Results saved in:"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq1_analysis/ (RQ1)"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq2_comparison/ (RQ2)"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq3_comparison/ (RQ3)"
if [ -d "experiments/$RQ4_R_F_EXP_ID" ] || [ -d "experiments/$RQ4_R_R_EXP_ID" ]; then
    echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq4_comparison/ (RQ4, if available)"
fi
echo ""
