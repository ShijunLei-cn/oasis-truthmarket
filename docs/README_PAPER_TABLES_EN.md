# Paper Table Generation Scripts

This directory contains scripts to generate LaTeX tables in the exact format required for the ICML 2025 paper.

## Overview

The scripts generate publication-ready tables that can be directly included in the paper. All tables follow the ICML style guide with:
- Booktabs formatting (toprule, midrule, bottomrule)
- Centered alignment for all columns
- Bold formatting for significant results
- Proper spacing and formatting

## Scripts

### 1. `paper_table_generator.py`
**Core utility module**

Contains the `generate_latex_table()` function and all table generation functions:
- `create_summary_stats_table()` - Summary Statistics with Reputation
- `create_manipulation_detection_table()` - Manipulation Detection Rate by Vulnerability Type
- `create_product_quality_table()` - Product Quality Statistics
- `create_market_outcomes_table()` - Market Outcomes and Reputation Statistics by Constraints
- `create_profit_decomposition_table()` - Profit Decomposition by Constraints
- `create_buyer_comm_table()` - Summary Statistics with Deceptions and Reputation
- `create_buyer_comm_quality_table()` - Product Quality Statistics (Buyer Communication)

### 2. `generate_rq1_paper_tables.py`
**RQ1 Table Generation**

Generates 3 tables for Research Question 1 (Mechanism Effectiveness):
- `rq1_summary_stats.tex` - Summary Statistics with Reputation (tab:rq1_summary_stats)
- `rq1_summary_comparison.tex` - Manipulation Detection Rate by Vulnerability Type (tab:rq1_summary_comparison)
- `rq1_product_quality.tex` - Product Quality Statistics (tab:rq1_product_quality)

**Usage:**
```bash
python generate_rq1_paper_tables.py \
    --r-market-dir /path/to/rep_market_results \
    --r-probe-dir /path/to/rep_probe_results \
    --rw-market-dir /path/to/rep_warrant_market_results \
    --rw-probe-dir /path/to/rep_warrant_probe_results \
    --output-dir visualization/table/rq1
```

### 3. `generate_rq2_paper_tables.py`
**RQ2 Table Generation**

Generates 3 tables for Research Question 2 (Seller Communication and Group-Level Deception):
- `rq2_initial_posts.tex` - Market Outcomes and Reputation Statistics by Constraints (tab:rq2_initial_posts)
- `rq2_product_quality.tex` - Product Quality Statistics by Constraints (tab:rq2_product_quality)
- `rq2_profit_decomposition.tex` - Profit Decomposition by Constraints (tab:rq2_profit_decomposition)

**Usage:**
```bash
python generate_rq2_paper_tables.py \
    --experiment-dirs /path/to/policy_making_exp /path/to/pressure_quick_profits_exp /path/to/psychological_attack_exp \
    --output-dir visualization/table/rq2
```

### 4. `generate_rq3_paper_tables.py`
**RQ3 Table Generation**

Generates 2 tables for Research Question 3 (Buyer Communication and Collective Adaptation):
- `rq3_summary_stats.tex` - Summary Statistics with Deceptions and Reputation (tab:rq3_summary_stats)
- `rq3_product_quality.tex` - Product Quality Statistics (tab:rq3_product_quality)

**Usage:**
```bash
python generate_rq3_paper_tables.py \
    --rep-comm-dir /path/to/rep_comm_results \
    --rw-comm-dir /path/to/rep_warrant_comm_results \
    --output-dir visualization/table/rq3
```

### 5. `generate_all_paper_tables.py`
**Master Script**

Generates all paper tables for all RQs in one command.

**Usage:**
```bash
python generate_all_paper_tables.py \
    --rq1 r1_market r1_probe r2_market r2_probe \
    --rq2 dir1 dir2 dir3 \
    --rq3 dir1 dir2 \
    --output-dir visualization/table/paper
```

## Input Data Format

### For RQ1:
Each directory should contain files named `run_*_results.json` and `run_*_cognitive_probes.json`.

Example structure:
```
experiment_dir/
├── run_001_results.json
├── run_001_cognitive_probes.json
├── run_002_results.json
└── run_002_cognitive_probes.json
```

### For RQ2:
Each experiment directory should contain `run_*_results.json` files.

### For RQ3:
Each communication directory should contain `run_*_results.json` files.

## Output

All scripts generate LaTeX files (`.tex`) that can be directly included in the paper:

```latex
\input{sections/table_name.tex}
```

Or copy the table code directly into the paper.

## Table Labels

Tables are generated with the following labels (matching the paper):

- `tab:rq1_summary_stats`
- `tab:rq1_summary_comparison`
- `tab:rq1_product_quality`
- `tab:rq2_initial_posts`
- `tab:rq2_product_quality`
- `tab:rq2_profit_decomposition`
- `tab:rq3_summary_stats`
- `tab:rq3_product_quality`

## Customization

### Bold Formatting
Tables automatically apply bold formatting to:
- Rep+Warrant rows in comparison tables
- Best-performing results
- Significant findings

### Column Alignment
All columns are centered by default. To change alignment, modify the `alignment` parameter in `generate_latex_table()`.

### Multi-column Headers
Tables with multi-level headers (e.g., Product Quality tables) automatically generate the correct `\multicolumn` LaTeX code.

## Requirements

- Python 3.6+
- pandas
- numpy
- pathlib (standard library)
- json (standard library)

## Example Workflow

1. Run your experiments and save results to JSON files
2. Organize results into directories by condition:
   ```
   results/
   ├── rq1/
   │   ├── rep_market/
   │   ├── rep_probes/
   │   ├── rw_market/
   │   └── rw_probes/
   ```
3. Generate all tables:
   ```bash
   cd visualization/scripts
   python generate_all_paper_tables.py \
       --rq1 results/rq1/rep_market results/rq1/rep_probes results/rq1/rw_market results/rq1/rw_probes \
       --rq2 results/rq2/policy_making results/rq2/pressure_quick_profits results/rq2/psychological_attack \
       --rq3 results/rq3/rep_comm results/rq3/rw_comm \
       --output-dir ../../Papers/ICML-OASISxTruthmarket/visualization/table/paper
   ```
4. Copy generated tables to your paper directory:
   ```bash
   cp visualization/table/paper/rq1/*.tex ../../Papers/ICML-OASISxTruthmarket/sections/
   cp visualization/table/paper/rq2/*.tex ../../Papers/ICML-OASISxTruthmarket/sections/
   cp visualization/table/paper/rq3/*.tex ../../Papers/ICML-OASISxTruthmarket/sections/
   ```
5. Include in your paper:
   ```latex
   \input{rq1_summary_stats.tex}
   \input{rq1_summary_comparison.tex}
   % ... etc
   ```

## Troubleshooting

### "No data found" error
- Check that JSON files exist in the specified directories
- Verify file naming convention (`run_*_results.json`)
- Ensure JSON files are not empty

### "Extra alignment tab" error
- This is handled automatically by the scripts
- If manual editing is needed, check that the number of columns in `\begin{tabular}{...}` matches the data

### Bold formatting not appearing
- Check that the data contains the expected values
- Bold formatting is applied based on specific conditions in each table type

## Support

For issues or questions, check the table generation logs for detailed error messages.
