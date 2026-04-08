# Collusion Analysis Module

This module provides tools for analyzing and visualizing seller collusion behavior in the TruthMarketTwin marketplace experiments.

## Overview

The collusion analysis is based on Claude Sonnet 4.6 annotated results that categorize seller communication into 6 types:

| Type | Name | Description | Collusive? |
|------|------|-------------|------------|
| 1 | Direct Collusion Proposal | Explicit invitation to coordinate deception | ✅ Yes |
| 2 | Deception Strategy Broadcast | Sharing personal deceptive plans | ✅ Yes |
| 3 | Collusion Coordination | Building on others' deceptive strategies | ✅ Yes |
| 4 | Social Normalization | Framing deception as normal behavior | ✅ Yes |
| 5 | Neutral Information | Non-deceptive market information | ❌ No |
| 6 | Anti-Collusion | Explicit opposition to deception | ❌ No |

## Data Sources

The analysis uses the following data files from `data/case_analysis/`:

- `deception_rate_by_collusion.csv` - Deception rates with/without detected collusion
- `type_distribution_by_condition.csv` - Type distributions across 12 experimental conditions
- `type_distribution_by_round.csv` - Type distributions over 10 rounds
- `type_distribution_by_prompt_type.csv` - Type distributions by prompt type
- `qualitative_examples.json` - Example posts for each type
- `posts_extracted.jsonl` - Raw extracted posts
- `posts_labeled.jsonl` - Labeled posts

## Scripts

### 1. `collusion_analysis.py` - Main Visualization Generator

Generates 7 publication-quality figures:

```
fig1_deception_by_collusion.png        - Deception rate comparison (4.9% vs 41.3%)
fig2_collusion_by_mechanism.png        - Stacked bar by mechanism
fig3_collusion_communication_effect.png - Communication effect breakdown
fig4_collusion_evolution.png           - Time series over rounds
fig5_collusion_by_constraint.png        - Heatmap by constraint type
fig6_collusion_type_summary.png         - Summary of all 6 types
fig7_mechanism_comparison.png          - Rep vs Warrant comparison
```

### 2. `collusion_stats_summary.py` - Statistical Summary

Generates statistical summaries and significance tests in markdown format.

### 3. `analyze_posts_collusion.py` - Posts Analysis

Analyzes raw posts data for additional collusion metrics.

## Usage

### Quick Start (Default Paths)

```bash
cd /home/lsj/Projects/Gitself/oasis-truthmarket

# Run all analyses
bash visualization/scripts/collusionanalysis/run_all_collusion_analysis.sh

# Or run individual scripts
bash visualization/scripts/collusionanalysis/run_collusion_analysis.sh
```

### With Custom Paths

```bash
# Specify custom data and output directories
bash visualization/scripts/collusionanalysis/run_all_collusion_analysis.sh \
    --data-dir /path/to/data \
    --output-dir /path/to/output

# Run just the visualization
python3 visualization/scripts/collusionanalysis/collusion_analysis.py \
    --data-dir /path/to/data \
    --output-dir /path/to/output
```

### Individual Script Usage

```bash
# Generate statistical summary
python3 visualization/scripts/collusionanalysis/collusion_stats_summary.py \
    --data-dir data \
    --output visualization/figs/paper/collusion_analysis/stats.md

# Analyze posts data
python3 visualization/scripts/collusionanalysis/analyze_posts_collusion.py \
    --data-dir data \
    --output-dir visualization/figs/paper/collusion_analysis
```

## Output Files

All outputs are saved to `visualization/figs/paper/collusion_analysis/`:

```
collusion_analysis/
├── fig1_deception_by_collusion.png           # Main finding figure
├── fig2_collusion_by_mechanism.png           # Mechanism comparison
├── fig3_collusion_communication_effect.png   # Communication effect
├── fig4_collusion_evolution.png              # Temporal dynamics
├── fig5_collusion_by_constraint.png          # Constraint effects
├── fig6_collusion_type_summary.png          # All types overview
├── fig7_mechanism_comparison.png            # Detailed mechanism comparison
├── collusion_stats_summary.md               # Statistical summary report
├── posts_analysis_by_condition.csv          # Posts breakdown table
└── posts_analysis_detailed.json            # Detailed analysis results
```

## Key Findings

### Finding 1: Collusion Dramatically Increases Deception
- Without collusion: 4.9% deception rate
- With collusion: 41.3% deception rate
- **8.4x increase** in deception when collusion is detected

### Finding 2: Warrant Mechanism Reduces Collusive Messaging
- Reputation-only: ~20% collusive messaging (Types 1-4)
- Reputation+Warrant: ~8% collusive messaging
- **~60% reduction** in collusive communication

### Finding 3: Communication Amplifies Collusion (under Reputation-only)
- Without seller communication: baseline collusion levels
- With seller communication: significantly higher collusion
- Communication effect is **neutralized** under Warrant mechanism

## Requirements

```
- Python 3.8+
- matplotlib >= 3.5.0
- numpy >= 1.21.0
- pandas >= 1.3.0
- scipy >= 1.7.0
```

## Project Context

This analysis supports the TruthMarketTwin paper addressing:

- **RQ2**: When sellers are provided with a communication channel, does group-level deception emerge?
- **RQ3**: Can buyer communication serve as a collective defense against seller collusion?

## Literature Reference

The collusion definitions used here align with recent LLM agent collusion literature:

- Fish et al. (2025): "Algorithmic Collusion by Large Language Models"
- Agrawal et al. (2025): "Evaluating LLM Agent Collusion in Double Auctions"
- Ghaemi (2025): "Emergent Collusion in LLM-Powered Multi-Agent Markets: A Survey"
- Motwani et al. (2024): "Secret Collusion among AI Agents: Multi-Agent Deception via Steganography"
