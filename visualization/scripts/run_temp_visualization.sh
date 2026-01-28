#!/bin/bash
# Temperature Comparison Visualization
# Generate academic-style visualizations comparing different temperature settings

set -e

echo "=========================================="
echo "Temperature Comparison Visualization"
echo "=========================================="
echo ""

# Temperature values to compare
TEMPERATURES=("0.0" "0.5" "1.0")
MARKET_TYPES=("r_wo" "rw_wo")

# Step 1: Run multi-run analysis for all temperature experiments
echo "Step 1: Running multi-run analysis for all temperature experiments..."
echo ""

for market_type in "${MARKET_TYPES[@]}"; do
    for temp in "${TEMPERATURES[@]}"; do
        EXP_ID="temperature/temp_${temp}/${market_type}"
        echo "Analyzing: ${EXP_ID}"
        python analysis/multi_run_analysis.py --experiment_id "${EXP_ID}"
    done
done

echo ""
echo "✓ Multi-run analysis completed"
echo ""

# Step 2: Generate temperature comparison visualizations
echo "Step 2: Generating temperature comparison visualizations..."
echo ""

for market_type in "${MARKET_TYPES[@]}"; do
    echo "Generating visualizations for ${market_type}..."
    python visualization/scripts/temp_visualization.py \
        --market-type "${market_type}" \
        --temps "${TEMPERATURES[@]}" \
        --exp-prefix "temperature/temp"
    echo ""
done

echo "=========================================="
echo "✓ All temperature comparison visualizations completed"
echo "=========================================="
