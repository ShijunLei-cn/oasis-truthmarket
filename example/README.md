# Market Simulation Examples

This folder contains ready-to-run experiment programs for the OASIS market simulation framework.

## Quick Start

### 1. Single Simulation Run

Run a single market simulation with specific parameters:

```bash
# Basic run with default settings
python ./example/run_market_simulation.py

# Specify database path only
python ./example/run_market_simulation.py my_test.db

# Use short options
python ./example/run_market_simulation.py test_buyer.db -m reputation_only -c buyer

# Use long options
python ./example/run_market_simulation.py test_seller.db --market-type reputation_and_warrant --communication seller

# Run with both-side communication
python ./example/run_market_simulation.py test_both.db -m reputation_only -c both

# View help information
python ./example/run_market_simulation.py --help
```

### 2. Batch Experiments

Run multiple experiments with different configurations:

```bash
# Run batch experiments with default settings
python ./example/run_batch_experiments.py

# Specify number of runs per configuration
python ./example/run_batch_experiments.py 5
```

## Available Scripts

### `run_market_simulation.py`

Universal simulation runner supporting all communication types.

**Parameters:**
- `db_path` (positional, optional): Database file path (default: `market_simulation.db`)
- `-m, --market-type` (optional): Market type - `reputation_only` or `reputation_and_warrant` (default: from config)
- `-c, --communication` (optional): Communication type - `none`, `seller`, `buyer`, or `both` (default: `none`)

**Examples:**
```bash
# No communication (use defaults)
python ./example/run_market_simulation.py

# Specify database only
python ./example/run_market_simulation.py test1.db

# Use short options
python ./example/run_market_simulation.py test2.db -m reputation_only -c buyer

# Use long options
python ./example/run_market_simulation.py test3.db --market-type reputation_and_warrant --communication seller

# Both-side communication
python ./example/run_market_simulation.py test4.db -m reputation_only -c both

# View help
python ./example/run_market_simulation.py --help
```

### `run_batch_experiments.py`

Automated batch runner for comprehensive experiments.

**Features:**
- Runs all combinations of market types and communication types
- Creates timestamped experiment directories
- Saves configuration and results
- Supports multiple runs per configuration

**Output Structure:**
```
experiments/
└── exp_20240101_120000/
    ├── experiment_config.json
    ├── results_summary.json
    ├── run_1_reputation_only_none.db
    ├── run_1_reputation_only_buyer.db
    ├── run_1_reputation_only_seller.db
    ├── run_1_reputation_only_both.db
    ├── run_1_reputation_and_warrant_none.db
    └── ...
```

## Configuration

All simulations use settings from `../config.py`:

- `NUM_SELLERS`: Number of seller agents
- `NUM_BUYERS`: Number of buyer agents
- `SIMULATION_ROUNDS`: Number of rounds per simulation
- `MARKET_TYPE`: Default market type
- `MODEL_PLATFORM`: LLM platform (e.g., "openai")
- `MODEL_TYPE`: LLM model (e.g., "gpt-4o-mini")

## Environment Variables

Create a `.env` file in the parent directory with:

```env
MODEL_API_KEY=your_api_key_here
MODEL_BASE_URL=your_base_url_here  # Optional
```

## Communication Types Explained

1. **`none`**: No communication between agents
   - Agents make decisions based only on market observations
   - Pure market dynamics without social influence

2. **`seller`**: Sellers can communicate with each other
   - Sellers share listing strategies and experiences
   - Enables seller coordination or competition

3. **`buyer`**: Buyers can communicate with each other
   - Buyers share purchase experiences and warnings
   - Enables reputation propagation among buyers

4. **`both`**: Both sellers and buyers can communicate
   - Full social interaction within each group
   - Most complex market dynamics

## Market Types Explained

1. **`reputation_only`**: 
   - Buyers rate sellers after transactions
   - No warranty system
   - Trust based on historical ratings

2. **`reputation_and_warrant`**:
   - Includes reputation system
   - Sellers can offer truth warrants
   - Buyers can challenge false warrants

## Tips for Running Experiments

1. **Test First**: Run a single simulation to verify setup
2. **Small Batches**: Start with fewer runs to test configurations
3. **Monitor Resources**: LLM API calls can be rate-limited
4. **Save Results**: Database files contain complete simulation data
5. **Document Settings**: Keep track of configuration changes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the `example` directory
2. **API Errors**: Check your `.env` file and API credentials
3. **Database Errors**: Ensure write permissions in the directory
4. **Memory Issues**: Reduce `NUM_SELLERS` and `NUM_BUYERS` for testing

### Getting Help

Check the parent directory's documentation:
- `../oasis_market/README.md` - Framework documentation
- `../config.py` - Configuration options
- `../utils.py` - Utility functions

## Example Workflow

```bash
# 1. Test single run
python ./example/run_market_simulation.py test.db -m reputation_only -c none

# 2. If successful, run small batch
python ./example/run_batch_experiments.py 2

# 3. Run full experiment
python ./example/run_batch_experiments.py 10
```
