#!/usr/bin/env python3
"""
Run batch experiments for a single configuration
Supports running multiple runs with specific market type, communication type, and channel type
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Add parent directory to path for imports
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODEL_ENV_PATH = REPOSITORY_ROOT / ".env"
sys.path.insert(0, str(REPOSITORY_ROOT))

from config import SimulationConfig
from experiment_control import (
    apply_cli_overrides,
    build_execution_manifest,
    copy_file_exclusive,
    parse_seed_list,
    reserve_experiment_directory,
    safe_experiment_path,
    seed_simulator,
    write_json_exclusive,
    write_json_atomic,
)


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


async def run_experiment(exp_dir: Path, market_type: str,
                        communication_type: str, run_id: int,
                        seed: int,
                        agent_checkpoint_paths: Optional[dict[str, Path]] = None,
                        communication_channel_type: str = "Fake",
                        posts4seller: str = "",
                        enable_cognitive_probing: bool = False,
                        probe_interval: int = 1,
                        resume: bool = False):
    """
    Run a single experiment with specified parameters
    
    Args:
        exp_dir: Reserved experiment output directory
        market_type: Type of market
        communication_type: Type of communication
        run_id: Run identifier
        seed: Simulator-side random seed
        agent_checkpoint_paths: Per-run seller and buyer checkpoint snapshots
        communication_channel_type: Type of communication channel ("Fake" or "Real")
        posts4seller: Type of initial posts for sellers ('policy_making', 'pressure_quickprofits', 'psychological-based-attack')
        enable_cognitive_probing: Enable cognitive probing
        probe_interval: Probe every N rounds
    """
    # Generate database path
    # Simple format: run_i.db (detailed config is saved in config.json)
    db_filename = f"run_{run_id}.db"
    db_path = exp_dir / db_filename
    if db_path.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite existing database: {db_path}")
    seed_simulator(seed)
    
    print(f"\n--- Running {db_filename} ---")
    print(f"  Market Type: {market_type}")
    print(f"  Communication Type: {communication_type}")
    print(f"  Communication Channel Type: {communication_channel_type}")
    print(f"  Simulator Seed: {seed}")
    if posts4seller:
        print(f"  Posts4Seller Type: {posts4seller}")
    if enable_cognitive_probing:
        print(f"  Cognitive Probing: enabled (interval={probe_interval})")
    
    # Run simulation
    from oasis_market.simulation import run_single_simulation

    await run_single_simulation(
        str(db_path),
        market_type=market_type, 
        communication_type=communication_type,
        communication_channel_type=communication_channel_type,
        posts4seller=posts4seller if posts4seller else None,
        enable_cognitive_probing=enable_cognitive_probing,
        probe_interval=probe_interval,
        agent_checkpoint_paths=agent_checkpoint_paths,
        resume=resume,
        run_identity={
            "run_id": run_id,
            "seed": seed,
            "market_type": market_type,
            "communication_type": communication_type,
            "communication_channel_type": communication_channel_type,
            "posts4seller": posts4seller,
            "cognitive_probing_enabled": enable_cognitive_probing,
            "probe_interval": probe_interval,
        },
    )
    
    return str(db_path)


async def run_batch_experiment(experiment_id: str, market_type: str,
                               communication_type: str, 
                               communication_channel_type: str = "Fake",
                               num_runs: int = None,
                               seeds: Optional[list[int]] = None,
                               posts4seller: str = "",
                               enable_cognitive_probing: bool = False,
                               probe_interval: int = 1,
                               resume: bool = False):
    """
    Run batch experiments with specified configuration
    
    Args:
        experiment_id: Experiment identifier
        market_type: Type of market
        communication_type: Type of communication
        communication_channel_type: Type of communication channel ("Fake" or "Real")
        num_runs: Number of runs (default: from config)
        seeds: One simulator seed per run
        posts4seller: Type of initial posts for sellers ('policy_making', 'pressure_quickprofits', 'psychological-based-attack')
        enable_cognitive_probing: Enable cognitive probing
        probe_interval: Probe every N rounds
    """
    if num_runs is None:
        num_runs = SimulationConfig.RUNS
    if seeds is None or len(seeds) != num_runs:
        raise ValueError("one explicit simulator seed is required per run")
    
    exp_dir = safe_experiment_path(SimulationConfig.BASE_DATA_PATH, experiment_id)
    if resume:
        if not exp_dir.is_dir():
            raise FileNotFoundError(
                f"cannot resume missing experiment directory: {exp_dir}"
            )
        if not (exp_dir / "experiment_config.json").is_file():
            raise FileNotFoundError(
                f"cannot resume without experiment manifest: {exp_dir}"
            )
        profile_snapshots = {
            role: exp_dir / "inputs" / f"agent_checkpoint_{role}.json"
            for role in ("seller", "buyer")
        }
        for role, snapshot in profile_snapshots.items():
            if not snapshot.is_file():
                raise FileNotFoundError(
                    f"cannot resume without {role} profile snapshot: {snapshot}"
                )
    else:
        reserve_experiment_directory(exp_dir)

        config_data = build_execution_manifest(
            experiment_id=experiment_id,
            config=SimulationConfig,
            market_type=market_type,
            communication_type=communication_type,
            communication_channel_type=communication_channel_type,
            seeds=seeds,
            profile_paths={
                "seller": "data/agent_checkpoint_seller.json",
                "buyer": "data/agent_checkpoint_buyer.json",
            },
        )
        config_data.update({
            "posts4seller": posts4seller,
            "cognitive_probing_enabled": enable_cognitive_probing,
            "probe_interval": probe_interval,
            "runs": num_runs,
        })
        profile_sources = {
            "seller": Path("data/agent_checkpoint_seller.json"),
            "buyer": Path("data/agent_checkpoint_buyer.json"),
        }
        profile_snapshots = {}
        for role, source in profile_sources.items():
            snapshot = exp_dir / "inputs" / f"agent_checkpoint_{role}.json"
            copy_file_exclusive(source, snapshot)
            profile_snapshots[role] = snapshot
            config_data["profiles"][role]["snapshot_path"] = str(snapshot)
        write_json_exclusive(exp_dir / "experiment_config.json", config_data)
    
    print("=" * 60)
    print(f"Experiment: {experiment_id}")
    print("=" * 60)
    print(f"Market Type: {market_type}")
    print(f"Communication Type: {communication_type}")
    print(f"Communication Channel Type: {communication_channel_type}")
    if posts4seller:
        print(f"Posts4Seller Type: {posts4seller}")
    if enable_cognitive_probing:
        print(f"Cognitive Probing: enabled (interval={probe_interval})")
    print(f"Number of Runs: {num_runs}")
    print("=" * 60)
    
    # Run all experiments
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"\n[{run_id}/{num_runs}] Run {run_id}")
        
        db_path = await run_experiment(
            exp_dir=exp_dir,
            market_type=market_type,
            communication_type=communication_type,
            run_id=run_id,
            seed=seeds[run_id - 1],
            agent_checkpoint_paths=profile_snapshots,
            communication_channel_type=communication_channel_type,
            posts4seller=posts4seller,
            enable_cognitive_probing=enable_cognitive_probing,
            probe_interval=probe_interval,
            resume=resume,
        )
        
        results.append({
            "run_id": run_id,
            "seed": seeds[run_id - 1],
            "market_type": market_type,
            "communication_type": communication_type,
            "communication_channel_type": communication_channel_type,
            "posts4seller": posts4seller,
            "cognitive_probing_enabled": enable_cognitive_probing,
            "probe_interval": probe_interval,
            "resumed": resume,
            "database": db_path
        })
    
    # Save results summary
    summary_path = exp_dir / "results_summary.json"
    if resume:
        write_json_atomic(summary_path, results)
    else:
        write_json_exclusive(summary_path, results)
    
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
        default=None,
        help='Experiment identifier. With --config, defaults to <config-stem>/<market-type>.'
    )
    
    parser.add_argument(
        '--market-type',
        dest='market_type',
        default=None,
        choices=['reputation_only', 'reputation_and_warrant'],
        help='Market type; defaults to market_rules.market_type from YAML/config.py.'
    )
    
    parser.add_argument(
        '--communication',
        dest='communication_type',
        default=None,
        choices=['none', 'seller', 'buyer', 'both'],
        help='Communication type; defaults to market_rules.communication_type from YAML/config.py.'
    )
    
    parser.add_argument(
        '--communication-channel-type',
        dest='communication_channel_type',
        choices=['Fake', 'Real'],
        default=None,
        help='Communication channel type; defaults to YAML/config.py.'
    )
    
    parser.add_argument(
        '--runs',
        dest='num_runs',
        type=int,
        default=None,
        help='Number of runs (default: value from loaded config)'
    )

    parser.add_argument(
        '--seeds',
        default=None,
        help='Comma-separated simulator seeds; defaults to experiment.seeds in YAML.'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the resolved credential-free manifest without creating files or calling a model.'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help=(
            'Restore each run from its newest complete-round checkpoint. '
            'The resolved config, profile snapshots, seed, and condition '
            'must match the checkpoint.'
        ),
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
        choices=['platform_fee_pressure', 'price_war_pressure', 'financial_distress_pressure',
                 'policy_making', 'pressure_quickprofits', 'psychological-based-attack'],  # Legacy names for backward compatibility
        default='',
        help='Initial posts type for sellers: platform_fee_pressure (platform cost survival pressure), '
             'price_war_pressure (competitive pricing pressure), or financial_distress_pressure (post-pandemic debt crisis). '
             'Legacy names (policy_making, pressure_quickprofits, psychological-based-attack) are also supported.'
    )

    parser.add_argument(
        '--Enhanced_seller_actions',
        dest='enhanced_seller_actions',
        choices=['reenter_support', 'free_price_support'], 
        default='',
        help='Enhanced seller actions type'
    )

    parser.add_argument(
        '--enable-cognitive-probing',
        dest='enable_cognitive_probing',
        action='store_true',
        help='Enable cognitive probing interviews during simulation.'
    )

    parser.add_argument(
        '--probe-interval',
        dest='probe_interval',
        type=int,
        default=1,
        help='Probe every N rounds when cognitive probing is enabled (default: 1).'
    )

    parser.add_argument(
        '--reentry-allowed-round',
        dest='reentry_allowed_round',
        type=int,
        default=None,
        help='Enable reenter_market from this round (e.g., 5). If omitted, keep config value.'
    )

    parser.add_argument(
        '--disable-reentry',
        dest='disable_reentry',
        action='store_true',
        help='Disable reenter_market action regardless of config file.'
    )

    args = parser.parse_args()
    
    # Load YAML first, then apply documented CLI precedence.
    load_config_from_yaml(args.config_file)
    apply_cli_overrides(
        SimulationConfig,
        model_platform=args.model_platform,
        model_type=args.model_type,
        runs=args.num_runs,
    )
    args.market_type = args.market_type or SimulationConfig.MARKET_TYPE
    args.communication_type = (
        args.communication_type or SimulationConfig.COMMUNICATION_TYPE
    )
    args.communication_channel_type = (
        args.communication_channel_type
        or SimulationConfig.COMMUNICATION_CHANNEL_TYPE
    )
    if args.experiment_id is None:
        if args.config_file is None:
            parser.error("--experiment-id is required when --config is omitted")
        args.experiment_id = f"{Path(args.config_file).stem}/{args.market_type}"

    resolved_runs = SimulationConfig.RUNS
    configured_seeds = getattr(SimulationConfig, "SEEDS", [])
    raw_seeds = args.seeds
    if raw_seeds is None and configured_seeds:
        raw_seeds = ",".join(str(seed) for seed in configured_seeds)
    try:
        resolved_seeds = parse_seed_list(raw_seeds, resolved_runs)
    except ValueError as exc:
        parser.error(str(exc))
    SimulationConfig.MARKET_TYPE = args.market_type
    SimulationConfig.COMMUNICATION_TYPE = args.communication_type
    SimulationConfig.COMMUNICATION_CHANNEL_TYPE = args.communication_channel_type

    # Optional market-rule override for reentry action
    if args.disable_reentry:
        SimulationConfig.REENTRY_ALLOWED_ROUND = None
        print("Reentry action override: DISABLED")
    elif args.reentry_allowed_round is not None:
        SimulationConfig.REENTRY_ALLOWED_ROUND = args.reentry_allowed_round
        print(f"Reentry action override: enabled from round {args.reentry_allowed_round}")

    if args.enhanced_seller_actions:
        parser.error(
            "--Enhanced_seller_actions is not connected to simulation execution; "
            "the free-price pilot remains blocked until that path is tested."
        )

    if args.dry_run:
        manifest = build_execution_manifest(
            experiment_id=args.experiment_id,
            config=SimulationConfig,
            market_type=args.market_type,
            communication_type=args.communication_type,
            communication_channel_type=args.communication_channel_type,
            seeds=resolved_seeds,
            profile_paths={
                "seller": "data/agent_checkpoint_seller.json",
                "buyer": "data/agent_checkpoint_buyer.json",
            },
        )
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return

    # Credentials are loaded only at the execution boundary, never for dry
    # runs. Use an explicit repository-root path so invocation from another
    # working directory cannot silently select a different .env file.
    if not MODEL_ENV_PATH.is_file():
        parser.error(f"model credential file does not exist: {MODEL_ENV_PATH}")
    load_dotenv(dotenv_path=MODEL_ENV_PATH, override=True)
    missing_model_variables = [
        name
        for name in ("MODEL_API_KEY", "MODEL_BASE_URL")
        if not os.getenv(name)
    ]
    if missing_model_variables:
        parser.error(
            f"{MODEL_ENV_PATH} is missing required model variables: "
            + ", ".join(missing_model_variables)
        )
    
    # Run batch experiment
    asyncio.run(run_batch_experiment(
        args.experiment_id,
        args.market_type,
        args.communication_type,
        args.communication_channel_type,
        resolved_runs,
        resolved_seeds,
        args.posts4seller,
        args.enable_cognitive_probing,
        args.probe_interval,
        args.resume,
    ))


if __name__ == "__main__":
    main()
