# OASIS Truth Market Simulation

A multi-agent online market simulation system built on the [OASIS](https://github.com/camel-ai/oasis) framework, designed to study agent behavior patterns in realistic market environments, with a particular focus on information asymmetry, reputation mechanisms, and warranty systems' impact on market efficiency.

## 🎯 Overview

This project implements a multi-agent online market simulation environment featuring:

- **Seller Agents**: Can list high or low quality products, choose whether to offer warranties
- **Buyer Agents**: Make purchasing decisions based on seller reputation and product information
- **Market Mechanisms**: Include reputation systems, warranty institutions, and transaction tracking

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+ (< 3.12)
- OpenAI API Key

### 2. Install Dependencies

#### Install OASIS Framework

According to the [OASIS official documentation](https://github.com/camel-ai/oasis), first install the OASIS package:

```bash
pip install camel-oasis
```

#### Install Project Dependencies

```bash
pip install -r requirement.txt
```

### 3. Environment Configuration

#### Create Environment Variables File

The project provides an `env.template` file as a configuration template. Please follow these steps:

1. Copy the template file:
```bash
cp env.template .env
```

2. Edit the `.env` file with your actual configuration:
```bash
# Edit .env file
nano .env  # or use your preferred editor
```

3. At minimum, configure the following required items:
```bash
# Model API Configuration (Required)
MODEL_API_KEY=your_api_key_here
MODEL_BASE_URL=https://api.openai.com/v1  # Optional, for OpenAI or compatible APIs

# Optional: Database path
MARKET_DB_PATH=market_sim.db
```

#### Environment Variables Reference

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `MODEL_API_KEY` | API key for the model provider (OpenAI or vLLM) | - | ✓ Yes |
| `MODEL_BASE_URL` | Base URL for API endpoint (for custom endpoints) | - | Optional |
| `MARKET_DB_PATH` | Database file path for market simulation | `market_sim.db` | Optional |

#### Configuration via config.py

The simulation parameters are configured in `config.py`:

```python
class SimulationConfig:
    RUNS = 50                          # Total number of independent simulation runs
    NUM_SELLERS = 10                   # Number of seller agents per run
    NUM_BUYERS = 10                    # Number of buyer agents per run
    SIMULATION_ROUNDS = 7              # Number of trading rounds per run
    
    # Market mechanism parameters
    REPUTATION_LAG = 1                 # Rounds of delay in reputation display
    REENTRY_ALLOWED_ROUND = 5          # Round when low-reputation sellers can re-enter
    EXIT_ROUND = 7                     # Round when sellers can choose to exit
    MARKET_TYPE = 'reputation_and_warrant'  # Market mechanism type
    
    # Model configuration
    MODEL_PLATFORM = "openai"          # "openai" or "vllm"
    MODEL_TYPE = "gpt-4o"              # Model identifier
```

To modify simulation parameters, edit these values in `config.py` before running.

### 4. Run Simulation

For detailed instructions on running simulations, please refer to the [Example Documentation](./example/README.md).

The `example/` folder contains streamlined runners:
- **Intent Probe Runner**: `run_intent_probe_experiment.py` - Run intent-focused probing experiments
- **Condition Batch Runner**: `run_market_condition_experiment.py` - Run market-condition batch experiments

Quick start examples:

```bash
# Run intent probing experiment
python ./example/run_intent_probe_experiment.py --market-type reputation_only

# Run condition batch experiment
python ./example/run_market_condition_experiment.py --experiment-id demo --market-type reputation_only --communication none
```

See [example/README.md](./example/README.md) for comprehensive documentation on:
- Available command-line options
- Configuration parameters
- Communication types and market types

## 🛠️ Customization

### Modify Simulation Parameters

Edit values in `config.py`:

```python
class SimulationConfig:
    RUNS = 50                          # Total number of independent simulation runs
    NUM_SELLERS = 10                   # Number of seller agents per run
    NUM_BUYERS = 10                    # Number of buyer agents per run
    SIMULATION_ROUNDS = 7              # Number of trading rounds per run
    
    # Market mechanism parameters
    REPUTATION_LAG = 1                 # Rounds of delay in reputation display
    REENTRY_ALLOWED_ROUND = 5          # Round when low-reputation sellers can re-enter
    EXIT_ROUND = 7                     # Round when sellers can choose to exit
    MARKET_TYPE = 'reputation_and_warrant'  # Market mechanism type
    
    # Model configuration
    MODEL_PLATFORM = "openai"          # "openai" or "vllm"
    MODEL_TYPE = "gpt-4o"              # Model identifier
```

### Customize Agent Characteristics

Modify prompt templates in `prompt.py`:

- `SELLER_GENERATION_SYS_PROMPT`: System prompt for seller agent generation
- `SELLER_GENERATION_USER_PROMPT`: User prompt for seller agent generation
- `BUYER_GENERATION_SYS_PROMPT`: System prompt for buyer agent generation
- `BUYER_GENERATION_USER_PROMPT`: User prompt for buyer agent generation
- `SELLER_ROUND_PROMPT`: Dynamic prompt for sellers during each round
- `BUYER_ROUND_PROMPT`: Dynamic prompt for buyers during each round

### Adjust Market Parameters

## 📚 Related Resources

- [OASIS Official Documentation](https://docs.oasis.camel-ai.org/)
- [OASIS GitHub Repository](https://github.com/camel-ai/oasis)
- [CAMEL-AI Project](https://github.com/camel-ai/camel)

## 🙏 Acknowledgments

Thanks to the [OASIS](https://github.com/camel-ai/oasis) project for providing an excellent multi-agent simulation framework, and to the [CAMEL-AI](https://github.com/camel-ai/camel) team for their important contributions in the AI agent field.
