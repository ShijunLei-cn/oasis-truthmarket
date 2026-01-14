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
from oasis_market.phases import (
    SellerListingPhase,
    BuyerPurchasePhase,
    BuyerRatingPhase,
    CommunicationPhase,
)
from cognitive_probing import (
    RQ1CognitiveProbes,
    VulnerabilityType,
    run_cognitive_probes,
)


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

    # Initialize simulation
    simulation = MarketSimulation(db_path, config)
    simulation.setup_environment()

    # Create model
    from camel.models import ModelFactory

    model = ModelFactory.create(
        model_platform=config.MODEL_PLATFORM,
        model_type=config.MODEL_TYPE,
        api_key=os.getenv("MODEL_API_KEY"),
        url=os.getenv("MODEL_BASE_URL"),
    )

    # Initialize agents
    market_type = config.MARKET_TYPE
    agent_graph, env = await simulation.initialize_agents(model, market_type)
    simulation.agent_graph = agent_graph
    simulation.env = env
    simulation.model = model

    # Initialize probing system
    prober = RQ1CognitiveProbes(db_path, config)

    # Initialize seller history
    simulation.sellers_history = {i + 1: [] for i in range(config.NUM_SELLERS)}

    # Track all probe results
    all_probe_results = []

    # Run simulation with probing
    for round_num in range(1, config.SIMULATION_ROUNDS + 1):
        print(f"\n--- Round {round_num}/{config.SIMULATION_ROUNDS} ---")

        # Synchronize platform round counter
        env.platform.sandbox_clock.round_step = round_num
        env.current_round = round_num

        # ============ COGNITIVE PROBING PHASE ============
        if (
            round_num % probe_interval == 0 or round_num <= 2
        ):  # Always probe first 2 rounds
            print(f"  [Probing] Running cognitive probes for round {round_num}...")
            probe_results = await run_cognitive_probes(
                env, agent_graph, round_num, prober
            )
            all_probe_results.extend(probe_results)
            print(f"  [Probing] Round {round_num}: {len(probe_results)} probe results collected")
            print(f"  [Probing] Total probe results in prober: {len(prober.probe_results)}")

        # ============ NORMAL SIMULATION PHASES ============
        await simulation.run_round(round_num, market_type, "none")

    # Run vulnerability detection
    from oasis.environment.processing.valunerability import run_detection

    run_detection(config.SIMULATION_ROUNDS, db_path)

    # Save probe results
    print(f"\n[Probing] Preparing to save probe results...")
    print(f"  Total probe results collected: {len(all_probe_results)}")
    print(f"  Probe results in prober object: {len(prober.probe_results)}")
    try:
        probe_output_path = prober.save_results()
        print(f"  ✓ Probe results saved to: {probe_output_path}")
    except Exception as e:
        print(f"  ❌ Error saving probe results: {e}")
        import traceback
        traceback.print_exc()
        probe_output_path = None

    # Close environment
    await env.close()

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
        "--runs", type=int, default=5, help="Number of simulation runs (default: 5)"
    )
    parser.add_argument(
        "--rounds", type=int, default=10, help="Rounds per simulation (default: 10)"
    )
    parser.add_argument(
        "--sellers", type=int, default=5, help="Number of sellers (default: 5)"
    )
    parser.add_argument(
        "--buyers", type=int, default=5, help="Number of buyers (default: 5)"
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

    # Run experiment
    asyncio.run(run_rq1_experiment(args))


if __name__ == "__main__":
    main()
