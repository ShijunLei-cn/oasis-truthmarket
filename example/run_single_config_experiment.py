#!/usr/bin/env python3
"""
Run batch experiments for a single configuration
Supports running multiple runs with specific market type, communication type, and channel type
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
import json
from dotenv import load_dotenv
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.simulation import run_single_simulation
from config import SimulationConfig

load_dotenv(override=True)


def load_config_from_yaml(yaml_path: Optional[str] = None):
    """
    Load configuration from YAML file if provided
    
    Args:
        yaml_path: Path to YAML configuration file (optional)
    """
    if yaml_path:
        print(f"Loading configuration from: {yaml_path}")
        SimulationConfig.load_from_yaml(yaml_path)
        print("Configuration loaded successfully.")
    else:
        print("Using default configuration from config.py")


async def run_experiment(experiment_id: str, market_type: str, 
                        communication_type: str, run_id: int,
                        communication_channel_type: str = "Fake"):
    """
    Run a single experiment with specified parameters
    
    Args:
        experiment_id: Experiment identifier
        market_type: Type of market
        communication_type: Type of communication
        run_id: Run identifier
        communication_channel_type: Type of communication channel ("Fake" or "Real")
    """
    # Create experiment directory
    exp_dir = f"experiments/{experiment_id}"
    os.makedirs(exp_dir, exist_ok=True)
    
    # Generate database path
    # Simple format: run_i.db (detailed config is saved in config.json)
    db_filename = f"run_{run_id}.db"
    db_path = os.path.join(exp_dir, db_filename)
    
    print(f"\n--- Running {db_filename} ---")
    print(f"  Market Type: {market_type}")
    print(f"  Communication Type: {communication_type}")
    print(f"  Communication Channel Type: {communication_channel_type}")
    
    # Run simulation
    await run_single_simulation(
        db_path, 
        market_type=market_type, 
        communication_type=communication_type,
        communication_channel_type=communication_channel_type
    )
    
    return db_path


async def run_batch_experiment(experiment_id: str, market_type: str,
                               communication_type: str, 
                               communication_channel_type: str = "Fake",
                               num_runs: int = None):
    """
    Run batch experiments with specified configuration
    
    Args:
        experiment_id: Experiment identifier
        market_type: Type of market
        communication_type: Type of communication
        communication_channel_type: Type of communication channel ("Fake" or "Real")
        num_runs: Number of runs (default: from config)
    """
    if num_runs is None:
        num_runs = SimulationConfig.RUNS
    
    # Create experiment directory
    exp_dir = f"experiments/{experiment_id}"
    os.makedirs(exp_dir, exist_ok=True)
    
    # Save experiment configuration
    config_data = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "market_type": market_type,
        "communication_type": communication_type,
        "communication_channel_type": communication_channel_type,
        "runs": num_runs,
        "simulation_config": SimulationConfig.to_dict()
    }
    
    with open(f"{exp_dir}/experiment_config.json", "w") as f:
        json.dump(config_data, f, indent=2)
    
    print("=" * 60)
    print(f"Experiment: {experiment_id}")
    print("=" * 60)
    print(f"Market Type: {market_type}")
    print(f"Communication Type: {communication_type}")
    print(f"Communication Channel Type: {communication_channel_type}")
    print(f"Number of Runs: {num_runs}")
    print("=" * 60)
    
    # Run all experiments
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"\n[{run_id}/{num_runs}] Run {run_id}")
        
        db_path = await run_experiment(
            experiment_id, market_type, communication_type, 
            run_id, communication_channel_type
        )
        
        results.append({
            "run_id": run_id,
            "market_type": market_type,
            "communication_type": communication_type,
            "communication_channel_type": communication_channel_type,
            "database": db_path
        })
    
    # Save results summary
    with open(f"{exp_dir}/results_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Experiment completed!")
    print(f"Results saved in: {exp_dir}/")
    print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run batch experiments for a single configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --experiment-id r_wbc --market-type reputation_only --communication buyer
  %(prog)s --experiment-id rw_wsc --market-type reputation_and_warrant --communication seller --communication-channel-type Real --runs 5
        """
    )
    
    # Model configuration arguments (must be set first before loading config)
    parser.add_argument(
        '--model-platform',
        dest='model_platform',
        type=str,
        default=None,
        help='Model platform (e.g., openai, anthropic). Overrides config if provided.'
    )
    
    parser.add_argument(
        '--model-type',
        dest='model_type',
        type=str,
        default=None,
        help='Model type (e.g., gpt-4o-mini, claude-3-5-sonnet). Overrides config if provided.'
    )
    
    parser.add_argument(
        '--experiment-id',
        dest='experiment_id',
        required=True,
        help='Experiment identifier (e.g., r_wbc, rw_wsc)'
    )
    
    parser.add_argument(
        '--market-type',
        dest='market_type',
        required=True,
        choices=['reputation_only', 'reputation_and_warrant'],
        help='Market type: reputation_only or reputation_and_warrant'
    )
    
    parser.add_argument(
        '--communication',
        dest='communication_type',
        required=True,
        choices=['none', 'seller', 'buyer', 'both'],
        help='Communication type: none, seller, buyer, or both'
    )
    
    parser.add_argument(
        '--communication-channel-type',
        dest='communication_channel_type',
        choices=['Fake', 'Real'],
        default='Fake',
        help='Communication channel type: Fake or Real (default: Fake)'
    )
    
    parser.add_argument(
        '--runs',
        dest='num_runs',
        type=int,
        default=1,
        help=f'Number of runs (default: {SimulationConfig.RUNS} from config)'
    )
    
    parser.add_argument(
        '--config',
        dest='config_file',
        type=str,
        default=None,
        help='Path to YAML configuration file (optional, overrides default config.py values)'
    )
    
    args = parser.parse_args()
    
    # Set model platform and type BEFORE loading config (so they can override config values)
    if args.model_platform:
        SimulationConfig.MODEL_PLATFORM = args.model_platform
        print(f"Using model platform from command line: {args.model_platform}")
    
    if args.model_type:
        SimulationConfig.MODEL_TYPE = args.model_type
        print(f"Using model type from command line: {args.model_type}")
    
    # Load configuration from YAML if provided
    load_config_from_yaml(args.config_file)
    
    # Run batch experiment
    asyncio.run(run_batch_experiment(
        args.experiment_id,
        args.market_type,
        args.communication_type,
        args.communication_channel_type,
        args.num_runs
    ))


if __name__ == "__main__":
    main()
    # asyncio.run(run_experiment(
    #     "gpt-4o/paper/rq2/rw_wo",
    #     "reputation_and_warrant",
    #     None,
    #     5,
    #     "Fake"
    # ))

