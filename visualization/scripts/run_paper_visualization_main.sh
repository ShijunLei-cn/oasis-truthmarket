#!/bin/bash
# Main visualization script for paper experiments
# Generates tables and figures for ICML 2025 paper

set -e

# Default experiment prefix (matches run_exp4paper.sh)
EXPERIMENT_PREFIX="${EXPERIMENT_PREFIX:-gpt-4o-mini/paper}"

# Ensure PYTHONPATH includes the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "=========================================="
echo "Paper Experiments Visualization"
echo "=========================================="
echo "Experiment Prefix: $EXPERIMENT_PREFIX"
echo ""

# ==================== Generate Paper Tables ====================
echo ""
echo "=========================================="
echo "Generating Paper Tables"
echo "=========================================="

# Create table output directory
TABLE_OUTPUT_DIR="visualization/table/paper"
mkdir -p "$TABLE_OUTPUT_DIR"

# Generate RQ1 tables
echo ""
echo "Generating RQ1 tables..."
RQ1_R_MARKET="experiments/${EXPERIMENT_PREFIX}/rq1/r_wo"
RQ1_R_PROBE="experiments/${EXPERIMENT_PREFIX}/rq1/r_wo"
RQ1_RW_MARKET="experiments/${EXPERIMENT_PREFIX}/rq1/rw_wo"
RQ1_RW_PROBE="experiments/${EXPERIMENT_PREFIX}/rq1/rw_wo"

if [ -d "$RQ1_R_MARKET" ] && [ -d "$RQ1_R_PROBE" ] && [ -d "$RQ1_RW_MARKET" ] && [ -d "$RQ1_RW_PROBE" ]; then
    echo "  Generating RQ1 tables..."
    mkdir -p "$TABLE_OUTPUT_DIR/rq1"
    python3 visualization/scripts/generate_rq1_paper_tables.py \
        --r-market-dir "$RQ1_R_MARKET" \
        --r-probe-dir "$RQ1_R_PROBE" \
        --rw-market-dir "$RQ1_RW_MARKET" \
        --rw-probe-dir "$RQ1_RW_PROBE" \
        --output-dir "$TABLE_OUTPUT_DIR/rq1"
    echo "  ✓ RQ1 tables generated"
else
    echo "  ⚠ RQ1 data directories not found, skipping RQ1 tables"
fi

# Generate RQ2 tables
echo ""
echo "Generating RQ2 tables..."
RQ2_R_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/r_wo"
RQ2_RW_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/rw_wo"

if [ -d "$RQ2_R_DIR" ] && [ -d "$RQ2_RW_DIR" ]; then
    echo "  Generating RQ2 tables..."
    mkdir -p "$TABLE_OUTPUT_DIR/rq2"
    # Use basic comparison table generator (no probes required)
    python3 visualization/scripts/generate_basic_comparison_tables.py \
        --r-market-dir "$RQ2_R_DIR" \
        --rw-market-dir "$RQ2_RW_DIR" \
        --output-dir "$TABLE_OUTPUT_DIR/rq2" \
        --table-prefix "rq2"
    echo "  ✓ RQ2 tables generated"
else
    echo "  ⚠ RQ2 data directories not found, skipping RQ2 tables"
    echo "  Expected: $RQ2_R_DIR and $RQ2_RW_DIR"
fi

# Generate RQ3 tables
echo ""
echo "Generating RQ3 tables..."
# RQ3 has multiple seller communication conditions
RQ3_BASE_DIR="experiments/${EXPERIMENT_PREFIX}/rq3"

# Check if RQ3 directory exists and has subdirectories
if [ -d "$RQ3_BASE_DIR" ]; then
    echo "  Found RQ3 experiment directory"

    # List available conditions
    echo "  Available RQ3 conditions:"
    for dir in "$RQ3_BASE_DIR"/*; do
        if [ -d "$dir" ]; then
            echo "    - $(basename "$dir")"
        fi
    done

    # Generate tables for specific conditions or all conditions
    # For baseline: r_wsc_R vs rw_wsc_R
    RQ3_R_BASE="$RQ3_BASE_DIR/r_wsc_R"
    RQ3_RW_BASE="$RQ3_BASE_DIR/rw_wsc_R"

    if [ -d "$RQ3_R_BASE" ] && [ -d "$RQ3_RW_BASE" ]; then
        echo "  Generating RQ3 baseline tables (Rational sellers)..."
        mkdir -p "$TABLE_OUTPUT_DIR/rq3"
        # Use basic comparison table generator
        python3 visualization/scripts/generate_basic_comparison_tables.py \
            --r-market-dir "$RQ3_R_BASE" \
            --rw-market-dir "$RQ3_RW_BASE" \
            --output-dir "$TABLE_OUTPUT_DIR/rq3" \
            --table-prefix "rq3"
        echo "  ✓ RQ3 tables generated"
    else
        echo "  ⚠ RQ3 baseline directories not found"
        echo "  Expected: $RQ3_R_BASE and $RQ3_RW_BASE"
    fi
else
    echo "  ⚠ RQ3 data directories not found, skipping RQ3 tables"
fi

# Generate RQ4 tables
echo ""
echo "Generating RQ4 tables..."
# RQ4 has buyer-seller communication conditions
RQ4_BASE_DIR="experiments/${EXPERIMENT_PREFIX}/rq4"

if [ -d "$RQ4_BASE_DIR" ]; then
    echo "  Found RQ4 experiment directory"

    # List available conditions
    echo "  Available RQ4 conditions:"
    for dir in "$RQ4_BASE_DIR"/*; do
        if [ -d "$dir" ]; then
            echo "    - $(basename "$dir")"
        fi
    done

    # For baseline: r_wbc_R vs rw_wbc_R (Rational buyers)
    RQ4_R_BASE="$RQ4_BASE_DIR/r_wbc_R"
    RQ4_RW_BASE="$RQ4_BASE_DIR/rw_wbc_R"

    if [ -d "$RQ4_R_BASE" ] && [ -d "$RQ4_RW_BASE" ]; then
        echo "  Generating RQ4 baseline tables (Rational buyers)..."
        mkdir -p "$TABLE_OUTPUT_DIR/rq4"
        # Use basic comparison table generator
        python3 visualization/scripts/generate_basic_comparison_tables.py \
            --r-market-dir "$RQ4_R_BASE" \
            --rw-market-dir "$RQ4_RW_BASE" \
            --output-dir "$TABLE_OUTPUT_DIR/rq4" \
            --table-prefix "rq4"
        echo "  ✓ RQ4 tables generated"
    else
        echo "  ⚠ RQ4 baseline directories not found"
        echo "  Expected: $RQ4_R_BASE and $RQ4_RW_BASE"
    fi
else
    echo "  ⚠ RQ4 data directories not found, skipping RQ4 tables"
fi

# Copy tables to paper sections directory
echo ""
echo "Copying tables to paper directory..."
PAPER_SECTIONS_DIR="../../Papers/ICML-OASISxTruthmarket/sections"
if [ -d "$PAPER_SECTIONS_DIR" ]; then
    mkdir -p "$PAPER_SECTIONS_DIR"
    if [ -d "$TABLE_OUTPUT_DIR/rq1" ]; then
        cp "$TABLE_OUTPUT_DIR/rq1/"*.tex "$PAPER_SECTIONS_DIR/" 2>/dev/null || true
        echo "  ✓ Copied RQ1 tables to paper"
    fi
    if [ -d "$TABLE_OUTPUT_DIR/rq2" ]; then
        cp "$TABLE_OUTPUT_DIR/rq2/"*.tex "$PAPER_SECTIONS_DIR/" 2>/dev/null || true
        echo "  ✓ Copied RQ2 tables to paper"
    fi
    if [ -d "$TABLE_OUTPUT_DIR/rq3" ]; then
        cp "$TABLE_OUTPUT_DIR/rq3/"*.tex "$PAPER_SECTIONS_DIR/" 2>/dev/null || true
        echo "  ✓ Copied RQ3 tables to paper"
    fi
else
    echo "  ⚠ Paper sections directory not found at $PAPER_SECTIONS_DIR"
    echo "  Tables are available at: $TABLE_OUTPUT_DIR"
fi

# ==================== Generate Paper Figures ====================
echo ""
echo "=========================================="
echo "Generating Paper Figures"
echo "=========================================="

# Generate round evolution comparison figure (used in paper)
echo ""
echo "Generating round evolution comparison figure..."
FIG_OUTPUT_DIR="visualization/figs/${EXPERIMENT_PREFIX}"
mkdir -p "$FIG_OUTPUT_DIR"

# Generate figures for RQ1
RQ1_R_MARKET="experiments/${EXPERIMENT_PREFIX}/rq1/r_wo"
RQ1_RW_MARKET="experiments/${EXPERIMENT_PREFIX}/rq1/rw_wo"

if [ -d "$RQ1_R_MARKET" ] && [ -d "$RQ1_RW_MARKET" ]; then
    echo "  Generating RQ1 comparison figures..."
    python3 visualization/scripts/generate_paper_figures.py \
        --r-dir "$RQ1_R_MARKET" \
        --rw-dir "$RQ1_RW_MARKET" \
        --output-dir "$FIG_OUTPUT_DIR"
    echo "  ✓ RQ1 figures generated"
else
    echo "  ⚠ RQ1 directories not found for figure generation"
fi

# Copy figures to paper directory
echo ""
echo "Copying figures to paper directory..."
PAPER_FIGS_DIR="../../Papers/ICML-OASISxTruthmarket/figs"
if [ -d "$PAPER_FIGS_DIR" ]; then
    cp "$FIG_OUTPUT_DIR"/*.png "$PAPER_FIGS_DIR/" 2>/dev/null || true
    echo "  ✓ Copied figures to paper"
else
    echo "  ⚠ Paper figs directory not found at $PAPER_FIGS_DIR"
    echo "  Figures are available at: $FIG_OUTPUT_DIR"
fi

# ==================== Summary ====================
echo ""
echo "=========================================="
echo "Visualization Complete!"
echo "=========================================="
echo ""
echo "Tables generated:"
[ -d "$TABLE_OUTPUT_DIR/rq1" ] && echo "  - RQ1: $TABLE_OUTPUT_DIR/rq1/"
[ -d "$TABLE_OUTPUT_DIR/rq2" ] && echo "  - RQ2: $TABLE_OUTPUT_DIR/rq2/"
[ -d "$TABLE_OUTPUT_DIR/rq3" ] && echo "  - RQ3: $TABLE_OUTPUT_DIR/rq3/"
[ -d "$TABLE_OUTPUT_DIR/rq4" ] && echo "  - RQ4: $TABLE_OUTPUT_DIR/rq4/"
echo ""
echo "Figures generated:"
[ -d "$FIG_OUTPUT_DIR" ] && echo "  - $FIG_OUTPUT_DIR/"
echo ""
echo "To include in your paper:"
echo "  1. Tables are in: $PAPER_SECTIONS_DIR"
echo "  2. Figures are in: $PAPER_FIGS_DIR"
echo "  3. Use \\input{} for tables and \\includegraphics{} for figures"
echo ""
