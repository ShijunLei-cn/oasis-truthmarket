#!/bin/bash
# ==========================================
# Paper Figure Generation Script
# ==========================================
# This script generates all figures for the paper from existing experiment results.
# It reads data from experiments/gpt-4o-mini/paper_largescale/ and generates visualizations.
# 
# Requires: Experiment results already exist in experiments/gpt-4o-mini/paper_largescale/
# ==========================================

set -e  # Exit on error

echo ""
echo "=========================================="
echo "Paper Figure Generation"
echo "=========================================="
echo "Generating visualizations from experiment results in:"
echo "experiments/gpt-4o-mini/paper_largescale/"
echo ""

# ==========================================
# RQ2: Market Mechanism Comparison (Reputation-Only vs Reputation+Warrant)
# ==========================================

echo "=========================================="
echo "Step 1: Generating RQ2 Comparison Figures"
echo "=========================================="
echo "Comparing: Reputation-Only vs Reputation+Warrant Markets"
echo ""

python visualization/scripts/figs4paper.py \
    --experiments "Reputation-Only:gpt-4o-mini/paper_largescale/rq2/r_wo" \
                  "Reputation+Warrant:gpt-4o-mini/paper_largescale/rq2/rw_wo" \
    --output-dir visualization/figs/gpt-4o-mini/paper/rq2

python visualization/scripts/figs4paper.py \
    --experiments "Reputation-Only:gpt-4o-mini/paper_largescale/rq3/r_wsc_R_pressure_quickprofits" \
                  "Reputation+Warrant:gpt-4o-mini/paper_largescale/rq3/rw_wsc_R_pressure_quickprofits" \
    --output-dir visualization/figs/gpt-4o-mini/paper/rq3

# ==========================================
# RQ3: Communication Channel Effects
# ==========================================

echo ""
echo "=========================================="
echo "Step 2: Generating RQ3 Figures"
echo "=========================================="
echo "Analyzing communication channel effects on market behavior"
echo ""

# RQ3 Figure 1: Policy Making Communication
echo "Generating RQ3 Figure (Policy Making)..."
python visualization/scripts/figs4paper.py \
    --rq3 \
    --initial-post-type policy_making \
    --r-r gpt-4o-mini/paper_largescale/rq3/r_wsc_R_policy_making \
    --rw-r gpt-4o-mini/paper_largescale/rq3/rw_wsc_R_policy_making \
    --r-f gpt-4o-mini/paper_largescale/rq3/r_wsc_F_policy_making \
    --rw-f gpt-4o-mini/paper_largescale/rq3/rw_wsc_F_policy_making \
    --output-dir visualization/figs/gpt-4o-mini/paper/rq3

# RQ3 Figure 2: Pressure & Quick Profits Communication
echo ""
echo "Generating RQ3 Figure (Pressure & Quick Profits)..."
python visualization/scripts/figs4paper.py \
    --rq3 \
    --initial-post-type pressure_quickprofits \
    --r-r gpt-4o-mini/paper_largescale/rq3/r_wsc_R_pressure_quickprofits \
    --rw-r gpt-4o-mini/paper_largescale/rq3/rw_wsc_R_pressure_quickprofits \
    --r-f gpt-4o-mini/paper_largescale/rq3/r_wsc_F_pressure_quickprofits \
    --rw-f gpt-4o-mini/paper_largescale/rq3/rw_wsc_F_pressure_quickprofits \
    --output-dir visualization/figs/gpt-4o-mini/paper/rq3

# RQ3 Figure 3: Psychological-Based Attack Communication
echo ""
echo "Generating RQ3 Figure (Psychological-Based Attack)..."
python visualization/scripts/figs4paper.py \
    --rq3 \
    --initial-post-type psychological-based-attack \
    --r-r gpt-4o-mini/paper_largescale/rq3/r_wsc_R_psychological-based-attack \
    --rw-r gpt-4o-mini/paper_largescale/rq3/rw_wsc_R_psychological-based-attack \
    --r-f gpt-4o-mini/paper_largescale/rq3/r_wsc_F_psychological-based-attack \
    --rw-f gpt-4o-mini/paper_largescale/rq3/rw_wsc_F_psychological-based-attack \
    --output-dir visualization/figs/gpt-4o-mini/paper/rq3

echo ""
echo "=========================================="
echo "All figures generated successfully!"
echo "=========================================="
echo ""
echo "Output locations:"
echo "  • RQ2 figures: visualization/figs/gpt-4o-mini/paper/rq2/"
echo "  • RQ3 figures: visualization/figs/gpt-4o-mini/paper/rq3/"
echo ""
echo "Generated files:"
echo "  • round_evolution_comparison.png"
echo "  • round_evolution_comparison_no_errorbars.png"
echo "  • rq3_policy_making_comparison.png"
echo "  • rq3_pressure_quickprofits_comparison.png"
echo "  • rq3_psychological-based-attack_comparison.png"
echo ""
echo "=========================================="
