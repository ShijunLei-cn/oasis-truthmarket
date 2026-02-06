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
# RQ2 has constraint-based experiments (policy, pressure, psychological)
RQ2_POLICY_R_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/policy_r_wo"
RQ2_POLICY_RW_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/policy_rw_wo"
RQ2_PRESSURE_R_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/pressure_r_wo"
RQ2_PRESSURE_RW_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/pressure_rw_wo"
RQ2_PSYCH_R_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/psychological_r_wo"
RQ2_PSYCH_RW_DIR="experiments/${EXPERIMENT_PREFIX}/rq2/psychological_rw_wo"

# Check if all RQ2 directories exist
if [ -d "$RQ2_POLICY_R_DIR" ] && [ -d "$RQ2_POLICY_RW_DIR" ] && \
   [ -d "$RQ2_PRESSURE_R_DIR" ] && [ -d "$RQ2_PRESSURE_RW_DIR" ] && \
   [ -d "$RQ2_PSYCH_R_DIR" ] && [ -d "$RQ2_PSYCH_RW_DIR" ]; then
    echo "  Generating RQ2 complete tables (Market Outcomes, Product Quality, Profit Decomposition)..."
    mkdir -p "$TABLE_OUTPUT_DIR/rq2"
    # Use complete RQ2 table generator
    python3 visualization/scripts/generate_rq2_paper_tables_complete.py \
        --experiment-dirs "$RQ2_POLICY_R_DIR" "$RQ2_POLICY_RW_DIR" \
                           "$RQ2_PRESSURE_R_DIR" "$RQ2_PRESSURE_RW_DIR" \
                           "$RQ2_PSYCH_R_DIR" "$RQ2_PSYCH_RW_DIR" \
        --output-dir "$TABLE_OUTPUT_DIR/rq2"
    echo "  ✓ RQ2 tables generated"
else
    echo "  ⚠ RQ2 data directories not found, skipping RQ2 tables"
    echo "  Expected: policy, pressure, and psychological directories with r_wo and rw_wo"
fi

# Generate RQ3 tables
echo ""
echo "Generating RQ3 tables..."
# RQ3 has communication experiments (Rep+Comm vs Rep+Warrant+Comm)
RQ3_REP_COMM_DIR="experiments/${EXPERIMENT_PREFIX}/rq3/r_wsc_R"
RQ3_RW_COMM_DIR="experiments/${EXPERIMENT_PREFIX}/rq3/rw_wsc_R"

if [ -d "$RQ3_REP_COMM_DIR" ] && [ -d "$RQ3_RW_COMM_DIR" ]; then
    echo "  Generating RQ3 complete tables (Summary with Deceptions, Product Quality)..."
    mkdir -p "$TABLE_OUTPUT_DIR/rq3"
    # Use complete RQ3 table generator
    python3 visualization/scripts/generate_rq3_paper_tables_complete.py \
        --rep-comm-dir "$RQ3_REP_COMM_DIR" \
        --rw-comm-dir "$RQ3_RW_COMM_DIR" \
        --output-dir "$TABLE_OUTPUT_DIR/rq3"
    echo "  ✓ RQ3 tables generated"
else
    echo "  ⚠ RQ3 data directories not found, skipping RQ3 tables"
    echo "  Expected: $RQ3_REP_COMM_DIR and $RQ3_RW_COMM_DIR"
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
echo ""
echo "Figures generated:"
[ -d "$FIG_OUTPUT_DIR" ] && echo "  - $FIG_OUTPUT_DIR/"
echo ""
echo "To include in your paper:"
echo "  1. Tables are in: $PAPER_SECTIONS_DIR"
echo "  2. Figures are in: $PAPER_FIGS_DIR"
echo "  3. Use \\input{} for tables and \\includegraphics{} for figures"
echo ""
