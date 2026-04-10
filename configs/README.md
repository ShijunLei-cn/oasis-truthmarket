# Configuration Files

This directory contains YAML configuration files for market simulation experiments.
File names are organized by **configuration semantics** (model + scale + key parameter profile),
not by RQ number.

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
    --config configs/sim_gpt4omini_5s_5b_10r_runs5_base.yaml

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

### Naming Convention

Config files follow this pattern:

`sim_<model>_<Ns>s_<Nb>b_<Nr>r_runs<R>_<profile>.yaml`

Examples:
- `sim_gpt4omini_5s_5b_10r_runs5_base.yaml`
- `sim_gpt4omini_5s_5b_10r_runs5_sellerbudget30.yaml`
- `sim_gpt4omini_5s_5b_10r_runs5_altpayoff.yaml`
- `sim_gpt4omini_20s_20b_20r_runs3_base.yaml`

### Available Configuration Files

- `default.yaml`: baseline config matching `config.py`
- `sim_gpt4omini_5s_5b_10r_runs10_base.yaml`: 5x5x10, 10 runs (probe-heavy baseline)
- `sim_gpt4omini_5s_5b_10r_runs5_base.yaml`: 5x5x10, 5 runs baseline
- `sim_gpt4omini_5s_5b_10r_runs5_sellerbudget30.yaml`: same as baseline, seller budget = 30
- `sim_gpt4omini_5s_5b_10r_runs5_altpayoff.yaml`: alternate payoff/cost matrix
- `sim_gpt4omini_10s_10b_10r_runs5_base.yaml`: medium scale baseline for gpt-4o-mini
- `sim_gpt4o_10s_10b_10r_runs5_base.yaml`: medium scale baseline for gpt-4o
- `sim_gpt4omini_20s_20b_20r_runs3_base.yaml`: large-scale baseline
- `sim_gpt4omini_50s_50b_10r_runs5_base.yaml`: very large population baseline

### Notes

- If `--config` is not provided, the scripts will use default values from `config.py`
- YAML configuration values override default `config.py` values
- Command-line arguments (like `--market-type`, `--communication`) still override YAML values
- All sections in YAML are optional - missing sections will use defaults from `config.py`
