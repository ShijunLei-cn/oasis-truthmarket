# Collusion Analysis Module (RQ2)

This module provides tools for analyzing and visualizing seller collusion behavior in the TruthMarketTwin marketplace experiments, specifically for RQ2 research question.

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
- `qualitative_examples.json` - Example posts for each type

## Visualizations Generated

This module generates 1 RQ2-relevant figure:

```
fig1_deception_by_collusion.png - Deception rate comparison (4.9% vs 41.3%)
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

All outputs are saved to `visualization/figs/paper/collusion_analysis/`:

```
collusion_analysis/
└── fig1_deception_by_collusion.png    # Main finding figure
```

## Key Findings (RQ2)

### Finding: Collusion Dramatically Increases Deception
- Without collusion: 4.9% deception rate
- With collusion: 41.3% deception rate
- **8.4x increase** in deception when collusion is detected

## Requirements

```
- Python 3.8+
- matplotlib >= 3.5.0
- numpy >= 1.21.0
- pandas >= 1.3.0
- scipy >= 1.7.0
```
