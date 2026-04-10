# Visualization Module

Modular visualization analysis tools for analyzing market simulation results.

## Directory Structure

```
visualization/
├── core/                      # Core modules
│   ├── __init__.py           # Module exports
│   ├── utils.py              # Utility functions
│   ├── data_loader.py        # Data loading module
│   ├── statistics.py         # Statistics calculation module
│   ├── plotters.py           # Plotting module
│   ├── single_run_analysis.py  # Single run analysis
│   ├── multi_run_analysis.py   # Multi-run analysis
│   └── comparison_analysis.py  # Comparison analysis
├── analyze_single.py         # Single run analysis CLI
├── analyze_multi.py          # Multi-run analysis CLI
├── compare_experiments.py    # Comparison analysis CLI
├── plot_communication_effects.py  # Communication effects visualization CLI
└── run_visul.sh              # Convenience script
```

## Usage

### 1. Using Convenience Script (Recommended)

```bash
# Analyze single run
./visualization/run_visul.sh single experiments/exp_123/run_1.db

# Analyze multi-run experiment
./visualization/run_visul.sh multi exp_20251216_120000

# Compare two experiments
./visualization/run_visul.sh compare reputation_only:exp_123 reputation_warrant:exp_456

# Compare using configuration file
./visualization/run_visul.sh compare-config comparison_config.json
```

### 2. Using Python Command-Line Interface

```bash
# Analyze single run
python3 visualization/analyze_single.py experiments/exp_123/run_1.db

# Analyze multi-run experiment
python3 visualization/analyze_multi.py --experiment-id exp_20251216_120000

# Compare experiments
python3 visualization/compare_experiments.py \
    --exp reputation_only:exp_123 \
    --exp reputation_warrant:exp_456

# Visualize communication effects (rep-only market)
python3 visualization/plot_communication_effects.py \
    --experiments-dir experiments \
    --output experiments/communication_effects_rep_only.png

# RQ3: Buyer communication effects (Fake vs Real channels)
python3 visualization/RQ3_figs.py \
    --experiments-dir experiments \
    --output experiments/RQ3_buyer_communication_effects.png

# RQ4: Seller communication effects (Fake vs Real channels)
python3 visualization/RQ4_figs.py \
    --experiments-dir experiments \
    --output experiments/RQ4_seller_communication_effects.png
```

### 3. Using Python API

```python
from visualization.core import (
    analyze_single_run,
    MultiRunAnalyzer,
    ComparisonAnalyzer
)

# Analyze single run
analyze_single_run('experiments/exp_123/run_1.db')

# Analyze multi-run experiment
analyzer = MultiRunAnalyzer('exp_20251216_120000')
analyzer.load_data()
stats = analyzer.generate_aggregated_statistics()
analyzer.save_aggregated_results()

# Compare experiments
from visualization.core.comparison_analysis import compare_experiments
compare_experiments({
    'reputation_only': 'exp_123',
    'reputation_warrant': 'exp_456'
})
```

## Functional Modules

### Data Loading (`data_loader.py`)

- `DataLoader`: Load single database file
- `ExperimentDataLoader`: Load multi-run experiment data

### Statistics Calculation (`statistics.py`)

- `StatisticsCalculator`: Calculate aggregated statistics, deception behavior statistics, etc.

### Plotting (`plotters.py`)

- `ReputationPlotter`: Reputation-related charts
- `PricePlotter`: Price-related charts
- `ActionPlotter`: Action-related charts
- `ManipulationPlotter`: Manipulation behavior charts

### Single Run Analysis (`single_run_analysis.py`)

- `SingleRunAnalyzer`: Analyze single simulation run
- `analyze_single_run()`: Convenience function

### Multi-Run Analysis (`multi_run_analysis.py`)

- `MultiRunAnalyzer`: Analyze multi-run experiments
- Generate aggregated statistics and visualizations

### Comparison Analysis (`comparison_analysis.py`)

- `ComparisonAnalyzer`: Compare results from different experiments
- `compare_experiments()`: Convenience function

### Communication Effects Visualization (`communication_effects.py`)

- `create_communication_effects_plot()`: Create communication effects comparison chart
- Compare 4 communication conditions (no communication, buyer communication, seller communication, both-way communication)
- Generate 6 subplots: seller profit, buyer utility, dishonest product count, transaction rating, transaction count, total revenue
- Use line charts with shaded areas to show mean ± standard deviation

### RQ3 Visualization (`RQ3_figs.py`)

- `create_rq3_plot()`: Create buyer communication effects visualization
- Compare Fake vs Real communication channels for buyer communication
- Compare across both market types (reputation_only and reputation_and_warrant)
- Generate 6 subplots with mean ± std visualization

### RQ4 Visualization (`RQ4_figs.py`)

- `create_rq4_plot()`: Create seller communication effects visualization
- Compare Fake vs Real communication channels for seller communication
- Compare across both market types (reputation_only and reputation_and_warrant)
- Generate 6 subplots with mean ± std visualization

## Configuration File Format

Comparison analysis configuration file (JSON):

```json
{
  "reputation_only": "exp_20251216_120000",
  "reputation_warrant": "exp_20251216_130000"
}
```

## Output Directories

- Single run analysis: `analysis/outputs/<timestamp>/`
- Multi-run analysis: `experiments/<experiment_id>/analysis/aggregated/`
- Comparison analysis: `analysis/comparison_<timestamp>/`

## Dependencies

- pandas
- numpy
- matplotlib
- seaborn

## Notes

1. Ensure database file paths are correct
2. Experiment ID format should be: `exp_YYYYMMDD_HHMMSS`
3. Configuration files use UTF-8 encoding
