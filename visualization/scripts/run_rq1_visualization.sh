#!/bin/bash

# Default experiment directory for RQ1 (Reputation Only)
INPUT_DIR=${1:-"experiments/rq1_wo"}
OUTPUT_DIR=${2:-"visualization/figs/rq1_analysis"}

# Ensure PYTHONPATH includes the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Running RQ1 Visualization Analysis..."
echo "Input Directory: $INPUT_DIR"
echo "Output Directory: $OUTPUT_DIR"

python3 visualization/scripts/rq1_visualization.py \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR"

echo "Done."

