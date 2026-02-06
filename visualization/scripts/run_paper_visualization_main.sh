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

# ==================== RQ1: Cognitive Probing Visualization ====================
echo ""
echo "=========================================="
echo "RQ1: Cognitive Probing Visualization"
echo "=========================================="

RQ1_R_INPUT_DIR="experiments/${EXPERIMENT_PREFIX}/rq1/r_wo"
RQ1_RW_INPUT_DIR="experiments/${EXPERIMENT_PREFIX}/rq1/rw_wo"
RQ1_OUTPUT_DIR="visualization/figs/${EXPERIMENT_PREFIX}/rq1_comparison"

# Check if RQ1 data exists
if [ -d "$RQ1_R_INPUT_DIR" ] || [ -d "$RQ1_RW_INPUT_DIR" ]; then
    echo "Generating RQ1 visualizations..."
    echo "  Input: $RQ1_R_INPUT_DIR, $RQ1_RW_INPUT_DIR"
    echo "  Output: $RQ1_OUTPUT_DIR"
    
    # Create output directory
    mkdir -p "$RQ1_OUTPUT_DIR"
    
    # Run RQ1 comparison visualization (generates both individual and comparison analyses)
    if [ -d "$RQ1_R_INPUT_DIR" ] && [ -d "$RQ1_RW_INPUT_DIR" ]; then
        echo "  Processing both market types with comparison analysis..."
        python3 visualization/scripts/rq1_visualization.py \
            --r-input-dir "$RQ1_R_INPUT_DIR" \
            --rw-input-dir "$RQ1_RW_INPUT_DIR" \
            --output-dir "$RQ1_OUTPUT_DIR" \
            --save-stats || echo "  Warning: RQ1 comparison visualization failed"
    elif [ -d "$RQ1_R_INPUT_DIR" ]; then
        echo "  Processing Reputation-Only experiments (single analysis)..."
        python3 visualization/scripts/rq1_visualization.py \
            --input-dir "$RQ1_R_INPUT_DIR" \
            --output-dir "$RQ1_OUTPUT_DIR/r_wo" \
            --save-stats || echo "  Warning: RQ1 R visualization failed"
    elif [ -d "$RQ1_RW_INPUT_DIR" ]; then
        echo "  Processing Reputation+Warrant experiments (single analysis)..."
        python3 visualization/scripts/rq1_visualization.py \
            --input-dir "$RQ1_RW_INPUT_DIR" \
            --output-dir "$RQ1_OUTPUT_DIR/rw_wo" \
            --save-stats || echo "  Warning: RQ1 RW visualization failed"
    fi
    
    echo "RQ1 visualization complete!"
else
    echo "Skipping RQ1: Data directories not found"
fi

# ==================== RQ2: Market Mechanism Comparison Visualization ====================
echo ""
echo "=========================================="
echo "RQ2: Market Mechanism Comparison Visualization"
echo "=========================================="

RQ2_R_EXP_ID="${EXPERIMENT_PREFIX}/rq1/r_wo"
RQ2_RW_EXP_ID="${EXPERIMENT_PREFIX}/rq1/rw_wo"

# Check if RQ2 experiments exist
if [ -d "experiments/$RQ2_R_EXP_ID" ] || [ -d "experiments/$RQ2_RW_EXP_ID" ]; then
    echo "Generating RQ2 visualizations..."
    echo "  Reputation-Only: $RQ2_R_EXP_ID"
    echo "  Reputation+Warrant: $RQ2_RW_EXP_ID"
    
    # Run multi-run analysis first
    if [ -d "experiments/$RQ2_R_EXP_ID" ]; then
        echo "  Running multi-run analysis for Reputation-Only..."
        python analysis/multi_run_analysis.py --experiment_id "$RQ2_R_EXP_ID" || echo "  Warning: RQ2 R analysis failed"
    fi
    
    if [ -d "experiments/$RQ2_RW_EXP_ID" ]; then
        echo "  Running multi-run analysis for Reputation+Warrant..."
        python analysis/multi_run_analysis.py --experiment_id "$RQ2_RW_EXP_ID" || echo "  Warning: RQ2 RW analysis failed"
    fi
    
    # Generate visualizations
    if [ -d "experiments/$RQ2_R_EXP_ID" ] && [ -d "experiments/$RQ2_RW_EXP_ID" ]; then
        echo "  Generating comparison visualizations..."
        python visualization/scripts/rq2_visualization.py \
            --r-exp "$RQ2_R_EXP_ID" \
            --rw-exp "$RQ2_RW_EXP_ID" || echo "  Warning: RQ2 visualization failed"
    else
        echo "  Warning: Both experiments required for RQ2 comparison visualization"
    fi
    
    echo "RQ2 visualization complete!"
else
    echo "Skipping RQ2: Experiment directories not found"
fi

# ==================== RQ3: Seller Communication Visualization ====================
echo ""
echo "=========================================="
echo "RQ3: Seller Communication Visualization"
echo "=========================================="

RQ3_R_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_F"
RQ3_R_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/r_wsc_R"
RQ3_RW_F_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_F"
RQ3_RW_R_EXP_ID="${EXPERIMENT_PREFIX}/rq3/rw_wsc_R"

# Check if RQ3 experiments exist
if [ -d "experiments/$RQ3_R_F_EXP_ID" ] || [ -d "experiments/$RQ3_R_R_EXP_ID" ] || \
   [ -d "experiments/$RQ3_RW_F_EXP_ID" ] || [ -d "experiments/$RQ3_RW_R_EXP_ID" ]; then
    echo "Generating RQ3 visualizations..."
    echo "  R_F: $RQ3_R_F_EXP_ID"
    echo "  R_R: $RQ3_R_R_EXP_ID"
    echo "  RW_F: $RQ3_RW_F_EXP_ID"
    echo "  RW_R: $RQ3_RW_R_EXP_ID"
    
    # Run multi-run analysis for all RQ3 experiments
    for exp_id in "$RQ3_R_F_EXP_ID" "$RQ3_R_R_EXP_ID" "$RQ3_RW_F_EXP_ID" "$RQ3_RW_R_EXP_ID"; do
        if [ -d "experiments/$exp_id" ]; then
            echo "  Running multi-run analysis for $exp_id..."
            python analysis/multi_run_analysis.py --experiment_id "$exp_id" || echo "  Warning: Analysis failed for $exp_id"
        fi
    done
    
    # Generate visualizations (only if all 4 experiments exist)
    if [ -d "experiments/$RQ3_R_F_EXP_ID" ] && [ -d "experiments/$RQ3_R_R_EXP_ID" ] && \
       [ -d "experiments/$RQ3_RW_F_EXP_ID" ] && [ -d "experiments/$RQ3_RW_R_EXP_ID" ]; then
        echo "  Generating comparison visualizations..."
        python visualization/scripts/rq3_visualization.py \
            --r-f "$RQ3_R_F_EXP_ID" \
            --r-r "$RQ3_R_R_EXP_ID" \
            --rw-f "$RQ3_RW_F_EXP_ID" \
            --rw-r "$RQ3_RW_R_EXP_ID" || echo "  Warning: RQ3 visualization failed"
    else
        echo "  Warning: All 4 experiments required for RQ3 comparison visualization"
        echo "  Missing experiments will be skipped"
    fi
    
    echo "RQ3 visualization complete!"
else
    echo "Skipping RQ3: Experiment directories not found"
fi

# ==================== RQ4: Buyer Communication Visualization ====================
echo ""
echo "=========================================="
echo "RQ4: Buyer Communication Visualization"
echo "=========================================="

RQ4_R_F_EXP_ID="${EXPERIMENT_PREFIX}/rq4/r_wbc_F"
RQ4_R_R_EXP_ID="${EXPERIMENT_PREFIX}/rq4/r_wbc_R"
RQ4_RW_F_EXP_ID="${EXPERIMENT_PREFIX}/rq4/rw_wbc_F"
RQ4_RW_R_EXP_ID="${EXPERIMENT_PREFIX}/rq4/rw_wbc_R"
RQ4_RW_BOTH_R_EXP_ID="${EXPERIMENT_PREFIX}/rq4/rw_wbsc_R"

# Check if RQ4 experiments exist
if [ -d "experiments/$RQ4_R_F_EXP_ID" ] || [ -d "experiments/$RQ4_R_R_EXP_ID" ] || \
   [ -d "experiments/$RQ4_RW_F_EXP_ID" ] || [ -d "experiments/$RQ4_RW_R_EXP_ID" ]; then
    echo "Generating RQ4 visualizations..."
    echo "  R_F: $RQ4_R_F_EXP_ID"
    echo "  R_R: $RQ4_R_R_EXP_ID"
    echo "  RW_F: $RQ4_RW_F_EXP_ID"
    echo "  RW_R: $RQ4_RW_R_EXP_ID"
    if [ -d "experiments/$RQ4_RW_BOTH_R_EXP_ID" ]; then
        echo "  RW_BOTH_R: $RQ4_RW_BOTH_R_EXP_ID"
    fi
    
    # Run multi-run analysis for all RQ4 experiments
    for exp_id in "$RQ4_R_F_EXP_ID" "$RQ4_R_R_EXP_ID" "$RQ4_RW_F_EXP_ID" "$RQ4_RW_R_EXP_ID" "$RQ4_RW_BOTH_R_EXP_ID"; do
        if [ -d "experiments/$exp_id" ]; then
            echo "  Running multi-run analysis for $exp_id..."
            python analysis/multi_run_analysis.py --experiment_id "$exp_id" || echo "  Warning: Analysis failed for $exp_id"
        fi
    done
    
    # Note: RQ4 visualization might use similar structure to RQ3
    # If a specific RQ4 visualization script exists, call it here
    # Otherwise, RQ4 can be analyzed using the same tools as RQ3
    if [ -f "visualization/scripts/rq4_visualization.py" ]; then
        echo "  Generating RQ4-specific visualizations..."
        python visualization/scripts/rq4_visualization.py \
            --r-f "$RQ4_R_F_EXP_ID" \
            --r-r "$RQ4_R_R_EXP_ID" \
            --rw-f "$RQ4_RW_F_EXP_ID" \
            --rw-r "$RQ4_RW_R_EXP_ID" || echo "  Warning: RQ4 visualization failed"
    else
        echo "  Note: RQ4-specific visualization script not found"
        echo "  RQ4 experiments can be analyzed using multi_run_analysis.py results"
    fi
    
    echo "RQ4 visualization complete!"
else
    echo "Skipping RQ4: Experiment directories not found"
fi

echo ""
echo "=========================================="
echo "All visualizations complete!"
echo "=========================================="
echo ""
echo "Results saved in:"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq1_comparison/ (RQ1)"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq2_comparison/ (RQ2)"
echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq3_comparison/ (RQ3)"
if [ -d "experiments/$RQ4_R_F_EXP_ID" ] || [ -d "experiments/$RQ4_R_R_EXP_ID" ]; then
    echo "  - visualization/figs/${EXPERIMENT_PREFIX}/rq4_comparison/ (RQ4, if available)"
fi
echo ""
