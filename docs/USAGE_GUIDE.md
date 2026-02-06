# Quick Start Guide: Paper Table Generation

## What This System Does

Generates LaTeX tables in the exact format required for your ICML 2025 paper. Simply provide your experimental data directories, and the scripts will generate publication-ready tables.

## Quick Example

```bash
# Navigate to scripts directory
cd oasis-truthmarket/visualization/scripts

# Generate all tables at once
python generate_all_paper_tables.py \
    --rq1 /data/rep_market /data/rep_probes /data/rw_market /data/rw_probes \
    --rq2 /data/policy_making /data/pressure_quick /data/psychological \
    --rq3 /data/rep_comm /data/rw_comm \
    --output-dir ../../Papers/ICML-OASISxTruthmarket/visualization/table/paper

# Copy tables to paper
cp -r ../../Papers/ICML-OASISxTruthmarket/visualization/table/paper/rq1/*.tex \
      ../../Papers/ICML-OASISxTruthmarket/visualization/table/paper/rq2/*.tex \
      ../../Papers/ICML-OASISxTruthmarket/visualization/table/paper/rq3/*.tex \
      ../../Papers/ICML-OASISxTruthmarket/sections/
```

## File Structure

```
oasis-truthmarket/visualization/scripts/
├── paper_table_generator.py          # Core table generation functions
├── generate_rq1_paper_tables.py      # RQ1 table generator
├── generate_rq2_paper_tables.py      # RQ2 table generator
├── generate_rq3_paper_tables.py      # RQ3 table generator
├── generate_all_paper_tables.py      # Generate all tables at once
├── test_table_generation.py          # Test the system
├── README_PAPER_TABLES.md            # Detailed documentation
├── SUMMARY_PAPER_TABLES.md           # Implementation summary
└── USAGE_GUIDE.md                    # This file
```

## Required Data Format

Each directory should contain JSON files with specific naming patterns:

### For RQ1 (4 directories needed):
```
rep_market/          # Market results for Reputation Only
├── run_001_results.json
├── run_002_results.json
└── ...

rep_probes/         # Cognitive probe results for Reputation Only
├── run_001_cognitive_probes.json
├── run_002_cognitive_probes.json
└── ...

rw_market/          # Market results for Reputation + Warranty
└── ...

rw_probes/          # Cognitive probe results for Reputation + Warranty
└── ...
```

### For RQ2 (3 directories needed):
```
policy_making/      # Policy-Making constraint experiments
├── run_001_results.json
└── ...

pressure_quick/     # Pressure-Quick-Profits constraint experiments
└── ...

psychological/      # Psychological-Attack constraint experiments
└── ...
```

### For RQ3 (2 directories needed):
```
rep_comm/          # Reputation + Communication experiments
├── run_001_results.json
└── ...

rw_comm/           # Reputation + Warranty + Communication experiments
└── ...
```

## Generated Tables

After running, you'll get these files in your output directory:

### RQ1 (3 tables):
- `rq1_summary_stats.tex` - Summary statistics with reputation
- `rq1_summary_comparison.tex` - Manipulation detection by vulnerability
- `rq1_product_quality.tex` - Product quality statistics

### RQ2 (3 tables):
- `rq2_initial_posts.tex` - Market outcomes by constraints
- `rq2_product_quality.tex` - Product quality by constraints
- `rq2_profit_decomposition.tex` - Profit decomposition

### RQ3 (2 tables):
- `rq3_summary_stats.tex` - Summary with deceptions
- `rq3_product_quality.tex` - Product quality (buyer comm)

## Including in Your Paper

1. Copy the generated `.tex` files to your paper's sections directory:
   ```bash
   cp visualization/table/paper/rq1/*.tex /path/to/paper/sections/
   cp visualization/table/paper/rq2/*.tex /path/to/paper/sections/
   cp visualization/table/paper/rq3/*.tex /path/to/paper/sections/
   ```

2. Include them in your paper (e.g., in `sections/04_experiments.tex`):
   ```latex
   % RQ1 Tables
   \input{rq1_summary_stats.tex}
   \input{rq1_summary_comparison.tex}
   \input{rq1_product_quality.tex}

   % RQ2 Tables
   \input{rq2_initial_posts.tex}
   \input{rq2_product_quality.tex}
   \input{rq2_profit_decomposition.tex}

   % RQ3 Tables
   \input{rq3_summary_stats.tex}
   \input{rq3_product_quality.tex}
   ```

3. The tables will compile directly into your paper!

## Troubleshooting

### "No data found" error
- Check that JSON files exist in the directories you specified
- Verify file naming: `run_*_results.json` or `run_*_cognitive_probes.json`
- Make sure directories are not empty

### Tables look wrong
- Check the generated `.tex` files manually
- Compare with paper examples in `sections/04_experiments.tex`
- Run `test_table_generation.py` to verify the system works

### Need help with specific RQ
- RQ1: See `generate_rq1_paper_tables.py --help`
- RQ2: See `generate_rq2_paper_tables.py --help`
- RQ3: See `generate_rq3_paper_tables.py --help`

## Key Features

✓ **Automatic LaTeX formatting** - No manual editing needed
✓ **Bold formatting** - Automatically highlights significant results
✓ **Multi-column headers** - Properly formatted product quality tables
✓ **Booktabs style** - Professional academic formatting
✓ **Error checking** - Validates data before generation
✓ **Modular** - Generate individual RQs or all at once

## Test First

Run the test script to verify everything works:

```bash
python test_table_generation.py
```

Expected output: All 6 tests should pass.

## Example Commands

### Generate only RQ1 tables:
```bash
python generate_rq1_paper_tables.py \
    --r-market-dir /data/experiment_1 \
    --r-probe-dir /data/experiment_2 \
    --rw-market-dir /data/experiment_3 \
    --rw-probe-dir /data/experiment_4 \
    --output-dir my_output
```

### Generate only RQ2 tables:
```bash
python generate_rq2_paper_tables.py \
    --experiment-dirs /data/constraint1 /data/constraint2 /data/constraint3 \
    --output-dir my_output
```

### Generate only RQ3 tables:
```bash
python generate_rq3_paper_tables.py \
    --rep-comm-dir /data/condition1 \
    --rw-comm-dir /data/condition2 \
    --output-dir my_output
```

## Need More Details?

See `README_PAPER_TABLES.md` for comprehensive documentation.

## Summary

1. Organize your experimental data into directories
2. Run `python generate_all_paper_tables.py` with your directories
3. Copy the generated `.tex` files to your paper
4. Include them with `\input{}` commands
5. Done!

The tables will match the format in your paper exactly.
