# Collusion Analysis Module (Focused)

This module provides tools for analyzing and visualizing seller collusion behavior in the TruthMarketTwin marketplace experiments, with a focus on Rep vs Rep+Warrant comparisons.

## Overview

The collusion analysis is based on LLM-annotated results that categorize seller communication into 6 types:

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

- `posts_labeled.jsonl` - LLM-labeled seller posts (collusion types + deceptive listing)

## Visualizations Generated

This module generates a focused figure plus 5 expanded schemes:

```
collusion_consistency_rep_vs_warrant.png - Left: agent consistency boxplots, right: 4-way category heatmap
collusion_scheme1_time_lag.png - Round trends + lag correlation heatmap
collusion_scheme2_agent_scatter_quartile.png - Agent scatter + quartile boxplot
collusion_scheme3_keywords_embedding.png - Log-odds keywords + embedding map
collusion_scheme4_topics_fraud.png - Topic share + fraud rate
collusion_scheme5_mosaic.png - Mosaic plot (Rep / Rep+Warrant)
collusion_scheme5_sankey.png - Sankey plot (Rep / Rep+Warrant)
```

## Usage

```bash
cd /home/lsj/Projects/Gitself/oasis-truthmarket

# Run the analysis
bash visualization/scripts/collusionanalysis/run_collusion_analysis.sh

# Or run with custom paths
bash visualization/scripts/collusionanalysis/run_collusion_analysis.sh \
    --data-dir /path/to/data \
    --output-dir /path/to/output
```

## Output Files

All outputs are saved to `figs/gpt-4o-mini/newresults/collusion_analysis/`:

```
collusion_analysis/
└── collusion_consistency_rep_vs_warrant.png
```

## Requirements

```
- Python 3.8+
- matplotlib >= 3.5.0
- numpy >= 1.21.0
- pandas >= 1.3.0
```
