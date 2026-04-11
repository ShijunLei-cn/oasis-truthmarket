#!/bin/bash
# =============================================================================
# Full Collusion Analysis Pipeline
# =============================================================================
# This script runs the complete collusion analysis pipeline:
# 1. Extract seller posts from experiment data
# 2. Annotate posts using LLM as judge
# 3. Aggregate results into analysis files
# 4. Generate visualizations
#
# Usage:
#   ./run_full_pipeline.sh --rq rq2
#   ./run_full_pipeline.sh --rq all --model gpt-4o
#   ./run_full_pipeline.sh --experiment-id r_wsc_R_policy_making --model mock
# =============================================================================

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default parameters
RQ="rq2"
MODEL="gpt-4o"  # Default to gpt-4o for real LLM annotation
EXPERIMENT_ID=""
DRY_RUN=false

# Default paths (newresults)
EXPERIMENTS_DIR_DEFAULT="${PROJECT_ROOT}/experiments/gpt-4o-mini/newresults"
OUTPUT_DIR_DEFAULT="${EXPERIMENTS_DIR_DEFAULT}/data/case_analysis"
VIZ_OUTPUT_DIR_DEFAULT="${PROJECT_ROOT}/figs/gpt-4o-mini/newresults/collusion_analysis"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rq)
            RQ="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --experiment-id)
            EXPERIMENT_ID="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --experiments-dir)
            EXPERIMENTS_DIR_DEFAULT="$2"
            OUTPUT_DIR_DEFAULT="${EXPERIMENTS_DIR_DEFAULT}/data/case_analysis"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR_DEFAULT="$2"
            shift 2
            ;;
        --viz-output-dir)
            VIZ_OUTPUT_DIR_DEFAULT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rq <rq1|rq2|rq3|all>   Which RQ to process (default: rq2)"
            echo "  --model <model>          LLM model to use (default: gpt-4o)"
            echo "                            Options: gpt-4o, gpt-4o-mini, claude-sonnet-4-20250514"
            echo "  --experiment-id <id>      Process specific experiment(s) only (comma-separated)"
            echo "  --experiments-dir <dir>   Experiments root (default: ${EXPERIMENTS_DIR_DEFAULT})"
            echo "  --output-dir <dir>        Output case_analysis dir (default: ${OUTPUT_DIR_DEFAULT})"
            echo "  --viz-output-dir <dir>    Visualization output dir (default: ${VIZ_OUTPUT_DIR_DEFAULT})"
            echo "  --dry-run                Show what would be done without running"
            echo "  --help                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --rq rq2                  # Process RQ2 with GPT-4o (default)"
            echo "  $0 --rq all --model gpt-4o-mini   # Process all RQs with GPT-4o-mini"
            echo "  $0 --experiment-id r_wsc_R_policy_making"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Paths
EXPERIMENTS_DIR="${EXPERIMENTS_DIR_DEFAULT}"
OUTPUT_DIR="${OUTPUT_DIR_DEFAULT}"
VIZ_OUTPUT_DIR="${VIZ_OUTPUT_DIR_DEFAULT}"
TEMP_DIR="${OUTPUT_DIR}/temp"

echo "============================================================================"
echo "COLLUSION ANALYSIS PIPELINE"
echo "============================================================================"
echo ""
echo "Project root: ${PROJECT_ROOT}"
echo "RQ to process: ${RQ}"
echo "LLM Model: ${MODEL}"
echo "Output directory: ${OUTPUT_DIR}"
echo "Visualization output: ${VIZ_OUTPUT_DIR}"
echo ""

# Show dry run info
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN MODE - No actual changes will be made"
    echo ""
fi

# Check Python environment
echo "Checking Python environment..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check required packages
REQUIRED_PACKAGES=("openai" "anthropic" "pandas" "numpy")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import ${package}" 2>/dev/null; then
        echo "  ✓ ${package}"
    else
        echo "  ✗ ${package} (will be skipped if not needed)"
    fi
done

echo ""

# =============================================================================
# Step 1: Extract Posts
# =============================================================================
echo "============================================================================"
echo "STEP 1: Extract Seller Posts from Experiments"
echo "============================================================================"
echo ""

EXTRACT_SCRIPT="${SCRIPT_DIR}/extract_posts.py"

if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run:"
    echo "  python3 ${EXTRACT_SCRIPT} \\"
    echo "    --experiments-dir ${EXPERIMENTS_DIR} \\"
    echo "    --rq ${RQ} \\"
    echo "    --output-dir ${OUTPUT_DIR}"
    if [ -n "$EXPERIMENT_ID" ]; then
        echo "    --experiment-id ${EXPERIMENT_ID}"
    fi
else
    EXTRACT_CMD="python3 ${EXTRACT_SCRIPT} --experiments-dir ${EXPERIMENTS_DIR} --rq ${RQ}"
    if [ -n "$EXPERIMENT_ID" ]; then
        EXTRACT_CMD="${EXTRACT_CMD} --experiment-id ${EXPERIMENT_ID}"
    fi
    
    ${EXTRACT_CMD}
fi

# Check if posts were extracted
EXTRACTED_POSTS="${OUTPUT_DIR}/posts_extracted.jsonl"
if [ ! -f "$EXTRACTED_POSTS" ]; then
    echo ""
    echo "ERROR: No posts extracted. Check if experiment data exists."
    exit 1
fi

POSTS_COUNT=$(wc -l < "$EXTRACTED_POSTS")
echo ""
echo "Extracted ${POSTS_COUNT} posts"

# =============================================================================
# Step 2: Annotate with LLM (Async Mode)
# =============================================================================
echo ""
echo "============================================================================"
echo "STEP 2: Annotate Posts Using LLM as Judge (Async Mode)"
echo "============================================================================"
echo ""

    ANNOTATE_SCRIPT="${SCRIPT_DIR}/annotate_with_llm.py"
    ANNOTATED_POSTS="${TEMP_DIR}/posts_labeled_${MODEL}.jsonl"

    # Use async mode with 20 concurrent requests for faster processing
    ANNOTATE_FLAGS="--max-concurrent 20 --rate-limit 0.05"
    echo "Using ASYNC mode with 20 concurrent requests"
    echo "This should be ~10-20x faster than sync mode"
    echo ""

if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run:"
    echo "  python3 ${ANNOTATE_SCRIPT} \\"
    echo "    --input ${EXTRACTED_POSTS} \\"
    echo "    --output ${ANNOTATED_POSTS} \\"
    echo "    --model ${MODEL} \\"
    echo "    ${ANNOTATE_FLAGS}"
else
    mkdir -p "${TEMP_DIR}"
    
    python3 "${ANNOTATE_SCRIPT}" \
        --input "${EXTRACTED_POSTS}" \
        --output "${ANNOTATED_POSTS}" \
        --model "${MODEL}" \
        ${ANNOTATE_FLAGS}
fi

# Check if annotations were created
if [ ! -f "$ANNOTATED_POSTS" ]; then
    echo ""
    echo "ERROR: Annotation failed. Check LLM API configuration."
    exit 1
fi

ANNOTATED_COUNT=$(wc -l < "$ANNOTATED_POSTS")
echo ""
echo "Annotated ${ANNOTATED_COUNT} posts"

# =============================================================================
# Step 3: Aggregate Results
# =============================================================================
echo ""
echo "============================================================================"
echo "STEP 3: Aggregate Results into Analysis Files"
echo "============================================================================"
echo ""

AGGREGATE_SCRIPT="${SCRIPT_DIR}/aggregate_results.py"

if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run:"
    echo "  python3 ${AGGREGATE_SCRIPT} \\"
    echo "    --input ${ANNOTATED_POSTS} \\"
    echo "    --output-dir ${OUTPUT_DIR}"
else
    python3 "${AGGREGATE_SCRIPT}" \
        --input "${ANNOTATED_POSTS}" \
        --output-dir "${OUTPUT_DIR}"
fi

# =============================================================================
# Step 4: Generate Visualizations
# =============================================================================
echo ""
echo "============================================================================"
echo "STEP 4: Generate Visualizations"
echo "============================================================================"
echo ""

VIZ_SCRIPT="${PROJECT_ROOT}/visualization/scripts/collusionanalysis/collusion_analysis.py"

# Note: OUTPUT_DIR is already the case_analysis directory, so for visualization
# we need to pass the parent directory and let the script append "case_analysis"
VIZ_DATA_DIR="$(cd "${OUTPUT_DIR}/.." && pwd)"

if [ -f "$VIZ_SCRIPT" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would run:"
        echo "  python3 ${VIZ_SCRIPT} \\"
        echo "    --data-dir ${VIZ_DATA_DIR} \\"
        echo "    --output-dir ${VIZ_OUTPUT_DIR}"
    else
        python3 "${VIZ_SCRIPT}" \
            --data-dir "${VIZ_DATA_DIR}" \
            --output-dir "${VIZ_OUTPUT_DIR}"
    fi
else
    echo "  Visualization script not found at: ${VIZ_SCRIPT}"
    echo "  Skipping visualization step."
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "============================================================================"
echo "PIPELINE COMPLETE!"
echo "============================================================================"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Output files in: ${OUTPUT_DIR}"
    echo ""
    echo "Generated files:"
    for file in "${OUTPUT_DIR}"/*; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" | cut -f1)
            ext="${file##*.}"
            case "$ext" in
                csv)  echo "  📊 $(basename $file) (${size})" ;;
                json) echo "  📋 $(basename $file) (${size})" ;;
                png)  echo "  🖼️  $(basename $file) (${size})" ;;
                md)   echo "  📝 $(basename $file) (${size})" ;;
                *)    echo "  📄 $(basename $file) (${size})" ;;
            esac
        fi
    done
    
    echo ""
    echo "These files are consistent with the original analysis in:"
    echo "  ${PROJECT_ROOT}/data/case_analysis/"
fi

echo ""
echo "Next steps:"
echo "  1. Review the generated qualitative_examples.json"
echo "  2. Check the visualization figures"
echo "  3. Run statistical tests on the aggregated data"
echo ""
