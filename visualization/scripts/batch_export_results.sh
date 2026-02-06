#!/bin/bash
# Batch Export Results from Database
# This script exports market results from all experiment directories

set -e

# Default experiment prefix
EXPERIMENT_PREFIX="${EXPERIMENT_PREFIX:-gpt-4o-mini/paper}"

echo "=========================================="
echo "Batch Export Market Results from DB"
echo "=========================================="
echo "Experiment Prefix: $EXPERIMENT_PREFIX"
echo ""

# Python command
PYTHON_CMD="python3"

# Export script
EXPORT_SCRIPT="visualization/scripts/export_results_from_db.py"

if [ ! -f "$EXPORT_SCRIPT" ]; then
    echo "ERROR: Export script not found: $EXPORT_SCRIPT"
    exit 1
fi

# Function to export results from a directory
export_directory() {
    local dir=$1
    local name=$2

    if [ -d "$dir" ]; then
        echo "Exporting: $name"
        echo "  Directory: $dir"
        $PYTHON_CMD "$EXPORT_SCRIPT" "$dir"
        echo ""
    else
        echo "  ⚠ Directory not found: $dir"
        echo ""
    fi
}

# Export RQ1 results
echo "=========================================="
echo "RQ1: Reputation Only vs Reputation+Warrant"
echo "=========================================="
export_directory "experiments/${EXPERIMENT_PREFIX}/rq1/r_wo" "RQ1 - Reputation Only"
export_directory "experiments/${EXPERIMENT_PREFIX}/rq1/rw_wo" "RQ1 - Reputation+Warrant"

# Export RQ2 results
echo "=========================================="
echo "RQ2: Seller Communication with Constraints"
echo "=========================================="
export_directory "experiments/${EXPERIMENT_PREFIX}/rq2/r_wo" "RQ2 - Reputation Only"
export_directory "experiments/${EXPERIMENT_PREFIX}/rq2/rw_wo" "RQ2 - Reputation+Warrant"

# Export RQ3 results (multiple conditions)
echo "=========================================="
echo "RQ3: Seller Communication Conditions"
echo "=========================================="

RQ3_DIRS=(
    "r_wsc_F"
    "r_wsc_R"
    "rw_wsc_F"
    "rw_wsc_R"
    "r_wsc_F_policy_making"
    "r_wsc_R_policy_making"
    "rw_wsc_F_policy_making"
    "rw_wsc_R_policy_making"
    "r_wsc_F_pressure_quickprofits"
    "r_wsc_R_pressure_quickprofits"
    "rw_wsc_F_pressure_quickprofits"
    "rw_wsc_R_pressure_quickprofits"
    "r_wsc_F_psychological-based-attack"
    "r_wsc_R_psychological-based-attack"
    "rw_wsc_F_psychological-based-attack"
    "rw_wsc_R_psychological-based-attack"
)

for dir_name in "${RQ3_DIRS[@]}"; do
    export_directory "experiments/${EXPERIMENT_PREFIX}/rq3/${dir_name}" "RQ3 - ${dir_name}"
done

# Export RQ4 results (Buyer-Seller Communication)
echo "=========================================="
echo "RQ4: Buyer-Seller Communication"
echo "=========================================="

RQ4_DIRS=(
    "r_wbc_F"
    "r_wbc_R"
    "rw_wbc_F"
    "rw_wbc_R"
)

for dir_name in "${RQ4_DIRS[@]}"; do
    export_directory "experiments/${EXPERIMENT_PREFIX}/rq4/${dir_name}" "RQ4 - ${dir_name}"
done

echo "=========================================="
echo "Batch Export Complete!"
echo "=========================================="
echo ""
echo "All results have been exported to *_results.json files"
echo "in their respective experiment directories."
echo ""
echo "Next steps:"
echo "  1. Run visualization scripts to generate tables and figures"
echo "  2. Use: ./visualization/scripts/run_paper_visualization_main.sh"
echo ""
