#!/bin/bash
# =============================================================================
# Setup and Test Collusion Analysis Module
# =============================================================================
# This script checks the environment and runs a quick test to ensure
# all components are properly configured.
# =============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "Collusion Analysis Module - Setup & Test"
echo "============================================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "Project root: ${PROJECT_ROOT}"
echo "Script directory: ${SCRIPT_DIR}"
echo ""

# =============================================================================
# Check Python environment
# =============================================================================
echo "Checking Python environment..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

echo "  ✓ Python: $(python3 --version)"
echo ""

# Check required packages
echo "Checking required Python packages..."
echo ""

REQUIRED_PACKAGES=("matplotlib" "numpy" "pandas" "scipy")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import ${package}" 2>/dev/null; then
        version=$(python3 -c "import ${package}; print(${package}.__version__)")
        echo "  ✓ ${package}: ${version}"
    else
        echo "  ✗ ${package}: NOT INSTALLED"
        MISSING_PACKAGES+=("${package}")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo "Installing missing packages..."
    pip install "${MISSING_PACKAGES[@]}" --quiet
    echo "Done!"
fi

echo ""

# =============================================================================
# Check data files
# =============================================================================
echo "Checking data files..."
echo ""

DATA_DIR="${PROJECT_ROOT}/data"
CASE_DIR="${DATA_DIR}/case_analysis"

if [ ! -d "${DATA_DIR}" ]; then
    echo "  ✗ Data directory not found: ${DATA_DIR}"
    exit 1
fi

echo "  ✓ Data directory: ${DATA_DIR}"

if [ ! -d "${CASE_DIR}" ]; then
    echo "  ✗ Case analysis directory not found: ${CASE_DIR}"
    exit 1
fi

echo "  ✓ Case analysis directory: ${CASE_DIR}"

REQUIRED_FILES=(
    "deception_rate_by_collusion.csv"
    "type_distribution_by_condition.csv"
    "type_distribution_by_round.csv"
    "type_distribution_by_prompt_type.csv"
    "qualitative_examples.json"
)

echo ""
echo "Checking required data files:"
echo ""

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${CASE_DIR}/${file}" ]; then
        size=$(du -h "${CASE_DIR}/${file}" | cut -f1)
        echo "  ✓ ${file} (${size})"
    else
        echo "  ✗ ${file}: NOT FOUND"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo ""
    echo "WARNING: Some required data files are missing."
    echo "The analysis may not run correctly."
    echo ""
fi

# =============================================================================
# Make scripts executable
# =============================================================================
echo ""
echo "Making scripts executable..."
echo ""

chmod +x "${SCRIPT_DIR}"/*.py
chmod +x "${SCRIPT_DIR}"/*.sh

echo "  ✓ Scripts are now executable"

# =============================================================================
# Test imports
# =============================================================================
echo ""
echo "Testing Python imports..."
echo ""

cd "${PROJECT_ROOT}"

if python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
sys.path.insert(0, '${SCRIPT_DIR}/..')
import fig_utils
print('  ✓ fig_utils imported successfully')
" 2>/dev/null; then
    echo "  ✓ Shared utilities loaded correctly"
else
    echo "  ✗ Failed to import shared utilities"
fi

# =============================================================================
# List available scripts
# =============================================================================
echo ""
echo "Available scripts:"
echo ""

echo "  Python scripts:"
for script in "${SCRIPT_DIR}"/*.py; do
    if [ -f "$script" ]; then
        echo "    - $(basename ${script})"
    fi
done

echo ""
echo "  Shell scripts:"
for script in "${SCRIPT_DIR}"/*.sh; do
    if [ -f "$script" ]; then
        echo "    - $(basename ${script})"
    fi
done

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "============================================================================"
echo "Setup Complete!"
echo "============================================================================"
echo ""
echo "To run the collusion analysis:"
echo ""
echo "  1. Quick test (generate all figures):"
echo "     cd ${PROJECT_ROOT}"
echo "     bash ${SCRIPT_DIR}/run_all_collusion_analysis.sh"
echo ""
echo "  2. Just visualizations:"
echo "     bash ${SCRIPT_DIR}/run_collusion_analysis.sh"
echo ""
echo "  3. Python directly:"
echo "     python3 ${SCRIPT_DIR}/collusion_analysis.py"
echo ""
echo "============================================================================"
