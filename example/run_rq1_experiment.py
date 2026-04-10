#!/usr/bin/env python3
"""
RQ1 Experiment Runner: Cognitive Probing for Reputation Manipulation

This script runs market simulations with cognitive probing to study
how agents exploit reputation mechanisms.

Usage:
    python example/run_rq1_experiment.py [OPTIONS]

Options:
    --runs N              Number of simulation runs (default: 5)
    --rounds N            Number of rounds per simulation (default: 10)
    --sellers N           Number of seller agents (default: 5)
    --buyers N            Number of buyer agents (default: 5)
    --market-type TYPE    Market type: reputation_only or reputation_and_warrant
    --output-dir DIR      Output directory for results
    --probe-interval N    Run probes every N rounds (default: 1 = every round)
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimulationConfig
from oasis_market.simulation import MarketSimulation


async def run_single_simulation_with_probing(
    run_id: int, db_path: str, config, probe_interval: int = 1
) -> dict:
    """
    Run a single simulation with cognitive probing

    Args:
        run_id: Run identifier
        db_path: Database path
        config: Simulation configuration
        probe_interval: Probe every N rounds

    Returns:
        Dictionary with simulation results and probe data
    """
    print(f"\n{'='*70}")
    print(f"RQ1 SIMULATION RUN {run_id}")
    print(f"Database: {db_path}")
    print(f"{'='*70}")

    # Initialize simulation and run probing inside the unified framework
    simulation = MarketSimulation(db_path, config)
    market_type = config.MARKET_TYPE
    await simulation.run(
        market_type=market_type,
        communication_type="none",
        enable_cognitive_probing=True,
        probe_interval=probe_interval,
    )

    # Run vulnerability detection
    from oasis.environment.processing.valunerability import run_detection

    run_detection(config.SIMULATION_ROUNDS, db_path)

    probe_output_path = simulation.cognitive_probe_output_path
    all_probe_results = simulation.cognitive_probe_results

    # Collect summary
    summary = {
        "run_id": run_id,
        "db_path": db_path,
        "probe_results_path": probe_output_path,
        "total_probes": len(all_probe_results),
        "manipulation_detected": sum(
            1 for p in all_probe_results if p.manipulation_detected
        ),
        "rounds": config.SIMULATION_ROUNDS,
        "sellers": config.NUM_SELLERS,
        "buyers": config.NUM_BUYERS,
        "market_type": market_type,
    }

    print(
        f"\n✓ Run {run_id} complete: {summary['manipulation_detected']}/{summary['total_probes']} manipulation indicators"
    )

    return summary


async def run_rq1_experiment(args):
    """Run the complete RQ1 experiment"""

    # Setup experiment
    experiment_id = datetime.now().strftime("rq1_%Y%m%d_%H%M%S")
    output_dir = args.output_dir or f"experiments/{experiment_id}"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'#'*70}")
    print(f"# RQ1 EXPERIMENT: Cognitive Probing for Reputation Manipulation")
    print(f"# Experiment ID: {experiment_id}")
    print(f"# Output: {output_dir}")
    print(f"{'#'*70}")

    # Configure simulation
    SimulationConfig.NUM_SELLERS = args.sellers
    SimulationConfig.NUM_BUYERS = args.buyers
    SimulationConfig.SIMULATION_ROUNDS = args.rounds
    SimulationConfig.MARKET_TYPE = args.market_type

    # Save experiment config
    experiment_config = {
        "experiment_id": experiment_id,
        "created_at": datetime.now().isoformat(),
        "runs": args.runs,
        "rounds": args.rounds,
        "sellers": args.sellers,
        "buyers": args.buyers,
        "market_type": args.market_type,
        "probe_interval": args.probe_interval,
        "market_params": SimulationConfig.MARKET_PARAMS,
    }

    config_path = os.path.join(output_dir, "experiment_config.json")
    with open(config_path, "w") as f:
        json.dump(experiment_config, f, indent=2)
    print(f"\nConfig saved to: {config_path}")

    # Run simulations
    all_summaries = []

    for run_id in range(1, args.runs + 1):
        db_path = os.path.join(output_dir, f"run_{run_id}.db")

        try:
            summary = await run_single_simulation_with_probing(
                run_id=run_id,
                db_path=db_path,
                config=SimulationConfig,
                probe_interval=args.probe_interval,
            )
            all_summaries.append(summary)
        except Exception as e:
            print(f"\n❌ Run {run_id} failed: {e}")
            import traceback

            traceback.print_exc()
            all_summaries.append({"run_id": run_id, "error": str(e)})

    # Save experiment summary
    experiment_summary = {
        "experiment_id": experiment_id,
        "completed_at": datetime.now().isoformat(),
        "total_runs": args.runs,
        "successful_runs": sum(1 for s in all_summaries if "error" not in s),
        "run_summaries": all_summaries,
    }

    summary_path = os.path.join(output_dir, "experiment_summary.json")
    with open(summary_path, "w") as f:
        json.dump(experiment_summary, f, indent=2, default=str)

    # Print final summary
    print(f"\n{'#'*70}")
    print(f"# EXPERIMENT COMPLETE")
    print(f"{'#'*70}")
    print(f"Total Runs: {experiment_summary['total_runs']}")
    print(f"Successful: {experiment_summary['successful_runs']}")
    print(f"Output Dir: {output_dir}")
    print(f"\nTo analyze results, run:")
    print(f"  python analysis/analyze_rq1.py {output_dir}")

    return experiment_summary


def main():
    parser = argparse.ArgumentParser(
        description="Run RQ1 Experiment: Cognitive Probing for Reputation Manipulation"
    )
    parser.add_argument(
        "--runs", type=int, default=None, help="Number of simulation runs (default: value from config)"
    )
    parser.add_argument(
        "--rounds", type=int, default=None, help="Rounds per simulation (default: value from config)"
    )
    parser.add_argument(
        "--sellers", type=int, default=None, help="Number of sellers (default: value from config)"
    )
    parser.add_argument(
        "--buyers", type=int, default=None, help="Number of buyers (default: value from config)"
    )
    parser.add_argument(
        "--market-type",
        type=str,
        default="reputation_only",
        choices=["reputation_only", "reputation_and_warrant"],
        help="Market type (default: reputation_only)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: experiments/rq1_TIMESTAMP)",
    )
    parser.add_argument(
        "--probe-interval",
        type=int,
        default=1,
        help="Probe every N rounds (default: 1)",
    )
    parser.add_argument(
        "--config",
        dest="config_file",
        type=str,
        default=None,
        help="Path to YAML configuration file (optional, overrides default config.py values)",
    )

    args = parser.parse_args()

    # Load configuration from YAML if provided
    if args.config_file:
        print(f"Loading configuration from {args.config_file}...")
        SimulationConfig.load_from_yaml(args.config_file)
        print("Configuration loaded from YAML.")
    else:
        print("No config file specified. Using default SimulationConfig.")

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Check for API key (support both naming conventions)
    api_key = os.getenv("MODEL_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: MODEL_API_KEY or OPENAI_API_KEY not set in environment or .env file"
        )
        sys.exit(1)

    # Set MODEL_API_KEY if only OPENAI_API_KEY is set
    if not os.getenv("MODEL_API_KEY") and os.getenv("OPENAI_API_KEY"):
        os.environ["MODEL_API_KEY"] = os.getenv("OPENAI_API_KEY")

    # Fill unresolved args from config (avoid overriding YAML with parser defaults)
    if args.runs is None:
        args.runs = SimulationConfig.RUNS
    if args.rounds is None:
        args.rounds = SimulationConfig.SIMULATION_ROUNDS
    if args.sellers is None:
        args.sellers = SimulationConfig.NUM_SELLERS
    if args.buyers is None:
        args.buyers = SimulationConfig.NUM_BUYERS

    # Run experiment
    asyncio.run(run_rq1_experiment(args))


if __name__ == "__main__":
    main()
