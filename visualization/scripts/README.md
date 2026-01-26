# RQ2 Market Mechanism Visualization

Academic-style visualizations for comparing Reputation-Only vs Reputation+Warrant market mechanisms.

## Prerequisites

1. Run experiments and generate aggregated statistics:
   ```bash
   python analysis/multi_run_analysis.py --experiment_id r_wo
   python analysis/multi_run_analysis.py --experiment_id rw_wo
   ```

2. Ensure experiment directories exist in `experiments/` with database files.

## Usage

### Quick Start

```bash
./visualization/scripts/run_rq2_visualization.sh r_wo rw_wo
```

### Using Python Directly

```bash
python visualization/scripts/rq2_visualization.py \
    --r-exp r_wo \
    --rw-exp rw_wo \
    --out visualization/figs/rq2_custom
```

### Environment Variables

```bash
export R_EXP_ID=r_wo
export RW_EXP_ID=rw_wo
./visualization/scripts/run_rq2_visualization.sh
```

## Output

Generates 5 academic-style figures:

1. **1_price_evolution.png** - Price trajectories for HQ/LQ products over rounds
2. **2_seller_profit.png** - Seller profit progression and KDE distribution comparison
3. **3_buyer_utility.png** - Buyer utility progression and KDE distribution comparison
4. **4_reputation.png** - Reputation score evolution and heatmap
5. **5_total_market_metrics.png** - Cross-run comparison with stacked bars (seller profits, buyer utilities, transaction counts, profit vs utility scatter)

All figures are saved in `visualization/figs/rq2_comparison/` with 300 DPI resolution.

## Visualization Features

- **Academic Style**: Serif fonts, professional color schemes, clear labels
- **Statistical Rigor**: Error bars, standard deviations, box plots
- **Comparative Layout**: Side-by-side R vs RW comparisons
- **Publication Ready**: High-resolution (300 DPI) PNG output

## Color Scheme

- Reputation-Only: Red tones (#d62728)
- Reputation+Warrant: Green tones (#2ca02c)
- Honest: Green (#2ca02c)
- Dishonest: Red (#d62728)

