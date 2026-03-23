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
                        communication_channel_type: str = "Fake",
                        posts4seller: str = ""):
    """
    Run a single experiment with specified parameters
    
    Args:
        experiment_id: Experiment identifier
        market_type: Type of market
        communication_type: Type of communication
        run_id: Run identifier
        communication_channel_type: Type of communication channel ("Fake" or "Real")
        posts4seller: Type of initial posts for sellers ('policy_making', 'pressure_quickprofits', 'psychological-based-attack')
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
    if posts4seller:
        print(f"  Posts4Seller Type: {posts4seller}")
    
    # Run simulation
    await run_single_simulation(
        db_path, 
        market_type=market_type, 
        communication_type=communication_type,
        communication_channel_type=communication_channel_type,
        posts4seller=posts4seller if posts4seller else None
    )
    
    return db_path


async def run_batch_experiment(experiment_id: str, market_type: str,
                               communication_type: str, 
                               communication_channel_type: str = "Fake",
                               num_runs: int = None,
                               posts4seller: str = ""):
    """
    Run batch experiments with specified configuration
    
    Args:
        experiment_id: Experiment identifier
        market_type: Type of market
        communication_type: Type of communication
        communication_channel_type: Type of communication channel ("Fake" or "Real")
        num_runs: Number of runs (default: from config)
        posts4seller: Type of initial posts for sellers ('policy_making', 'pressure_quickprofits', 'psychological-based-attack')
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
        "posts4seller": posts4seller,
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
    if posts4seller:
        print(f"Posts4Seller Type: {posts4seller}")
    print(f"Number of Runs: {num_runs}")
    print("=" * 60)
    
    # Run all experiments
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"\n[{run_id}/{num_runs}] Run {run_id}")
        
        db_path = await run_experiment(
            experiment_id, market_type, communication_type, 
            run_id, communication_channel_type, posts4seller
        )
        
        results.append({
            "run_id": run_id,
            "market_type": market_type,
            "communication_type": communication_type,
            "communication_channel_type": communication_channel_type,
            "posts4seller": posts4seller,
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
        default=None,
        help='Number of runs (default: value from loaded config)'
    )
    
    parser.add_argument(
        '--config',
        dest='config_file',
        type=str,
        default=None,
        help='Path to YAML configuration file (optional, overrides default config.py values)'
    )
    

    parser.add_argument(
        '--Posts4Seller',
        dest='posts4seller',
        choices=['policy_making', 'pressure_quickprofits', 'psychological-based-attack'],
        default='',
        help='Initial posts type for sellers: policy_making (government policy scenario), pressure_quickprofits (company pressure scenario), or psychological-based-attack (dark psychology scenario)'
    )

    parser.add_argument(
        '--Enhanced_seller_actions',
        dest='enhanced_seller_actions',
        choices=['reenter_support', 'free_price_support'], 
        default='',
        help='Enhanced seller actions type'
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

    # Respect YAML-configured runs unless explicitly overridden
    resolved_runs = args.num_runs if args.num_runs is not None else SimulationConfig.RUNS
    
    # Run batch experiment
    asyncio.run(run_batch_experiment(
        args.experiment_id,
        args.market_type,
        args.communication_type,
        args.communication_channel_type,
        resolved_runs,
        args.posts4seller
    ))


if __name__ == "__main__":
    main()
