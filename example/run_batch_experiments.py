"""
Batch experiment runner for multiple market simulations
Runs experiments with different configurations
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.simulation import run_single_simulation
from config import SimulationConfig
from dotenv import load_dotenv
from typing import Optional

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


async def run_experiment(experiment_name: str, market_type: str, 
                        communication_type: str, run_id: int,
                        communication_channel_type: str = "Fake"):
    """
    Run a single experiment with specified parameters
    
    Args:
        experiment_name: Name of the experiment group
        market_type: Type of market
        communication_type: Type of communication
        run_id: Run identifier
        communication_channel_type: Type of communication channel ("Fake" or "Real")
    """
    # Create experiment directory
    exp_dir = f"experiments/{experiment_name}"
    os.makedirs(exp_dir, exist_ok=True)
    
    # Generate database path
    # Simple format: run_i.db (detailed config is saved in config.json)
    db_filename = f"run_{run_id}.db"
    db_path = os.path.join(exp_dir, db_filename)
    
    print(f"\n--- Running {db_filename} ---")
    print(f"  Communication Channel Type: {communication_channel_type}")
    
    # Run simulation
    await run_single_simulation(
        db_path, 
        market_type=market_type, 
        communication_type=communication_type,
        communication_channel_type=communication_channel_type
    )
    
    return db_path


async def run_batch_experiments():
    """
    Run batch experiments with different configurations
    """
    # Experiment configurations
    experiments = [
        # Reputation only market
        ("reputation_only", "none"),
        ("reputation_only", "buyer"),
        ("reputation_only", "seller"),
        ("reputation_only", "both"),
        
        # Reputation and warrant market
        ("reputation_and_warrant", "none"),
        ("reputation_and_warrant", "buyer"),
        ("reputation_and_warrant", "seller"),
        ("reputation_and_warrant", "both"),
    ]
    
    # Create experiment name with timestamp
    experiment_name = datetime.now().strftime("exp_%Y%m%d_%H%M%S")
    
    print("=" * 60)
    print(f"Batch Experiment: {experiment_name}")
    print("=" * 60)
    print(f"Total configurations: {len(experiments)}")
    print(f"Runs per configuration: {SimulationConfig.RUNS}")
    print(f"Total simulations: {len(experiments) * SimulationConfig.RUNS}")
    print("=" * 60)
    
    # Save experiment configuration
    exp_dir = f"experiments/{experiment_name}"
    os.makedirs(exp_dir, exist_ok=True)
    
    config_data = {
        "experiment_name": experiment_name,
        "timestamp": datetime.now().isoformat(),
        "configurations": experiments,
        "runs_per_config": SimulationConfig.RUNS,
        "simulation_config": SimulationConfig.to_dict()
    }
    
    with open(f"{exp_dir}/experiment_config.json", "w") as f:
        json.dump(config_data, f, indent=2)
    
    # Run all experiments
    results = []
    total_runs = 0
    
    for market_type, comm_type in experiments:
        for run_id in range(1, SimulationConfig.RUNS + 1):
            total_runs += 1
            print(f"\n[{total_runs}/{len(experiments) * SimulationConfig.RUNS}] "
                  f"Market: {market_type}, Communication: {comm_type}, Run: {run_id}")
            
            db_path = await run_experiment(
                experiment_name, market_type, comm_type, run_id,
                communication_channel_type="Fake"
            )
            
            results.append({
                "run_id": run_id,
                "market_type": market_type,
                "communication_type": comm_type,
                "database": db_path
            })
    
    # Save results summary
    with open(f"{exp_dir}/results_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Batch experiment completed!")
    print(f"Results saved in: experiments/{experiment_name}/")
    print("=" * 60)


async def main():
    """
    Main entry point for batch experiments
    
    Usage:
        python run_batch_experiments.py [num_runs] [--config config.yaml]
        
    Args:
        num_runs: Number of runs per configuration (default: from config)
        --config: Path to YAML configuration file (optional)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run batch experiments with different configurations')
    parser.add_argument(
        'num_runs',
        nargs='?',
        type=int,
        default=None,
        help='Number of runs per configuration (default: from config)'
    )
    parser.add_argument(
        '--config',
        dest='config_file',
        type=str,
        default=None,
        help='Path to YAML configuration file (optional, overrides default config.py values)'
    )
    
    args = parser.parse_args()
    
    # Load configuration from YAML if provided
    load_config_from_yaml(args.config_file)
    
    # Override number of runs if specified
    if args.num_runs is not None:
        SimulationConfig.RUNS = args.num_runs
    
    await run_batch_experiments()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(main.__doc__)
    else:
        asyncio.run(main())
