# Configuration Files

This directory contains YAML configuration files for market simulation experiments.

## Usage

### Using YAML Configuration Files

All experiment scripts now support loading configuration from YAML files using the `--config` parameter:

```bash
# Run with YAML config
python ./example/run_single_config_experiment.py \
    --experiment-id r_wo \
    --market-type reputation_only \
    --communication none \
    --communication-channel-type Fake \
    --runs 5 \
    --config configs/rq2_experiment.yaml

# Run without YAML config (uses default config.py)
python ./example/run_single_config_experiment.py \
    --experiment-id r_wo \
    --market-type reputation_only \
    --communication none \
    --runs 5
```

### Configuration File Structure

YAML configuration files should follow this structure:

```yaml
experiment:
  runs: 5
  num_sellers: 5
  num_buyers: 5
  simulation_rounds: 10

market_params:
  hq_cost: 4.0
  lq_cost: 2.0
  hq_price: 8.0
  lq_price: 3.0
  hq_utility: 12.0
  lq_utility: 4.0
  hq_warrant_escrow: 8.0
  lq_warrant_escrow: 2.0
  challenge_cost: 1.0
  seller_budget: 18.0
  buyer_budget: 60.0
  initial_seller_reputation: 0.0

market_rules:
  reputation_lag: null
  reentry_allowed_round: null
  initial_window_rounds: []
  exit_round: null
  market_type: reputation_only
  communication_type: none
  communication_channel_type: Fake

model:
  platform: openai
  type: gpt-4o-mini

paths:
  base_data_path: experiments
  base_analysis_path: analysis
```

### Available Configuration Files

- `default.yaml`: Default configuration matching config.py defaults
- `rq2_experiment.yaml`: Configuration for RQ2 experiments

### Notes

- If `--config` is not provided, the scripts will use default values from `config.py`
- YAML configuration values override default `config.py` values
- Command-line arguments (like `--market-type`, `--communication`) still override YAML values
- All sections in YAML are optional - missing sections will use defaults from `config.py`

