# R Visualization Package for Oasis Truth Market

This directory contains R scripts for generating paper figures, providing an alternative to the Python visualization scripts.

## Files

| File | Description |
|------|-------------|
| [`utils.R`](utils.R) | Utility functions: color palette, data loading, statistical tests |
| [`generate_rq1_figures.R`](generate_rq1_figures.R) | RQ1 figures: Warrant vs. Reputation-Only |
| [`generate_rq2_figures.R`](generate_rq2_figures.R) | RQ2 figures: Seller Communication under Constraints |
| [`generate_rq3_figures.R`](generate_rq3_figures.R) | RQ3 figures: Buyer Communication & Collective Defense |
| [`run_paper_figures.R`](run_paper_figures.R) | Master script to generate all figures |

## Requirements

### R Packages

Required R packages (install via CRAN):
```r
install.packages(c("ggplot2", "dplyr", "tidyr", "jsonlite", "RSQLite"))
```

Or use the provided shell script which checks and installs packages automatically.

## Usage

### Option 1: Run All Figures

```bash
# From project root
cd /home/lsj/Projects/Gitself/oasis-truthmarket

# Run with default model (gpt-4o-mini)
bash visualization/R_visual/run_paper_figures.R

# Or run with R directly
Rscript visualization/R_visual/run_paper_figures.R
```

### Option 2: Run Individual RQ Figures

```bash
# RQ1
Rscript visualization/R_visual/generate_rq1_figures.R

# RQ2
Rscript visualization/R_visual/generate_rq2_figures.R

# RQ3
Rscript visualization/R_visual/generate_rq3_figures.R
```

### Option 3: Custom Model

```bash
MODEL_TYPE=gpt-4o Rscript visualization/R_visual/run_paper_figures.R
```

## Output

Generated figures are saved to:
```
visualization/figs/{MODEL_TYPE}/paper/
├── rq1/
│   ├── rq1_warrant_vs_rep_deception_and_profit.png
│   └── rq1_exit_loophole_vulnerability.png
├── rq2/
│   ├── rq2_seller_comm_deception_by_constraint.png
│   └── rq2_profit_decomposition_honest_vs_dishonest.png
└── rq3/
    ├── rq3_buyer_comm_market_outcomes.png
    └── rq3_round_adaptation_appendix.png
```

## Color Palette

The R version uses the same semantic color system as the Python version:

| Color Role | Hex | Usage |
|------------|-----|-------|
| `good_dark` | `#1D6B3A` | Rep+Warrant positive |
| `good_mid` | `#52B788` | Rep positive |
| `hq_auth` | `#2D6A4F` | HQ Authentic |
| `lq_auth` | `#74C69D` | LQ Authentic |
| `bad_dark` | `#AE2012` | Deception (Rep) |
| `bad_mid` | `#D4866A` | Deception (RW) |
| `counterfeit` | `#9B2226` | HQ Counterfeit |
| `rep_mid` | `#4caf72` | Rep mechanism |
| `warrant_mid` | `#64b5f6` | Rep+Warrant mechanism |

## Data Sources

The scripts read experiment data from:
- `experiments/{MODEL_TYPE}/paper/rq1/r_wo/` - Rep-only baseline
- `experiments/{MODEL_TYPE}/paper/rq1/rw_wo/` - Rep+Warrant
- `experiments/{MODEL_TYPE}/paper/rq2/` - RQ2 conditions
- `experiments/{MODEL_TYPE}/paper/rq3/` - RQ3 conditions

Each directory contains:
- `run_*_results.json` - Transaction results
- `run_*_cognitive_probes.json` - Cognitive probe responses
- `run_*.db` - SQLite database with detailed records
