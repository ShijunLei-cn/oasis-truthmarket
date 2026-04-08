#!/bin/bash
# ============================================================
# run_paper_figures.R
# R version: One-command script to generate all paper figures (RQ1/2/3)
# Run from the project root directory
# ============================================================

set -e

MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"

echo "=========================================="
echo "Paper Figure Generation (R version)"
echo "Model   : ${MODEL_TYPE}"
echo "=========================================="

# Check for R and required packages
echo ""
echo "Checking R installation..."
if ! command -v Rscript &> /dev/null; then
    echo "Error: Rscript not found. Please install R."
    exit 1
fi

# Install required packages if missing
echo "Checking R packages..."
Rscript -e '
packages <- c("ggplot2", "dplyr", "tidyr", "jsonlite", "RSQLite")
missing <- packages[!packages %in% installed.packages()[,"Package"]]
if (length(missing) > 0) {
    message("Installing missing packages: ", paste(missing, collapse = ", "))
    install.packages(missing, repos = "https://cloud.r-project.org/", quiet = TRUE)
}
'

# ── RQ1 ──────────────────────────────────────────────────────
echo ""
echo "── RQ1: Warrant vs. Reputation-Only ──────────────────"
Rscript visualization/R_visual/generate_rq1_figures.R

# ── RQ2 ──────────────────────────────────────────────────────
echo ""
echo "── RQ2: Seller Communication under Constraints ───────"
Rscript visualization/R_visual/generate_rq2_figures.R

# ── RQ3 ──────────────────────────────────────────────────────
echo ""
echo "── RQ3: Buyer Communication & Collective Defense ─────"
Rscript visualization/R_visual/generate_rq3_figures.R

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "All R figures generated!"
echo "=========================================="
echo ""
echo "Output directory: visualization/figs/${MODEL_TYPE}/paper/"
