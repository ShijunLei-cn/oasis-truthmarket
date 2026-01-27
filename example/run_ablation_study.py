#!/usr/bin/env python3
"""
Ablation Study Runner
Runs all ablation experiments using existing infrastructure
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimulationConfig
from oasis_market.simulation import run_single_simulation


# Ablation study configurations
ABLATION_CONFIGS = {
    "temperature": {
        "configs": [
            ("temperature_0.0", "configs/ablation/temperature_0.0.yaml"),
            ("temperature_0.3", "configs/ablation/temperature_0.3.yaml"),
            ("temperature_0.7", "configs/ablation/temperature_0.7.yaml"),
            ("temperature_1.0", "configs/ablation/temperature_1.0.yaml"),
        ],
        "description": "LLM Temperature Ablation",
    },
    "market_params": {
        "configs": [
            ("baseline", "configs/ablation/temperature_0.0.yaml"),  # baseline
            ("high_budget", "configs/ablation/market_high_budget.yaml"),
            ("low_budget", "configs/ablation/market_low_budget.yaml"),
            ("narrow_cost", "configs/ablation/market_narrow_cost.yaml"),
            ("wide_cost", "configs/ablation/market_wide_cost.yaml"),
            ("high_escrow", "configs/ablation/market_high_escrow.yaml"),
            ("low_escrow", "configs/ablation/market_low_escrow.yaml"),
        ],
        "description": "Market Parameters Ablation",
    },
}


async def run_ablation_condition(
    condition_name: str, config_path: str, ablation_type: str, exp_base: str
):
    """Run a single ablation condition"""
    # Load config
    SimulationConfig.load_from_yaml(config_path)

    exp_id = f"{exp_base}/{condition_name}"
    exp_dir = f"experiments/{exp_id}"
    os.makedirs(exp_dir, exist_ok=True)

    num_runs = SimulationConfig.RUNS
    market_type = SimulationConfig.MARKET_TYPE
    comm_type = SimulationConfig.COMMUNICATION_TYPE

    print(f"\n{'='*60}")
    print(f"Condition: {condition_name}")
    print(f"  Config: {config_path}")
    print(f"  Market: {market_type}, Runs: {num_runs}")
    print(f"{'='*60}")

    for run_id in range(1, num_runs + 1):
        db_path = os.path.join(exp_dir, f"run_{run_id}.db")
        print(f"  Run {run_id}/{num_runs}...")

        try:
            await run_single_simulation(
                db_path, market_type=market_type, communication_type=comm_type
            )
        except Exception as e:
            print(f"    Error in run {run_id}: {e}")

    return exp_id


async def run_ablation_study(ablation_type: str, exp_base: str = None):
    """Run complete ablation study"""
    if ablation_type not in ABLATION_CONFIGS:
        print(f"Unknown ablation type: {ablation_type}")
        print(f"Available: {list(ABLATION_CONFIGS.keys())}")
        return

    config = ABLATION_CONFIGS[ablation_type]

    if exp_base is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_base = f"ablation/{ablation_type}_{timestamp}"

    print(f"\n{'#'*60}")
    print(f"# ABLATION STUDY: {config['description']}")
    print(f"# Output: experiments/{exp_base}")
    print(f"{'#'*60}")

    results = []
    for condition_name, config_path in config["configs"]:
        exp_id = await run_ablation_condition(
            condition_name, config_path, ablation_type, exp_base
        )
        results.append((condition_name, exp_id))

    # Save study metadata
    metadata = {
        "ablation_type": ablation_type,
        "description": config["description"],
        "conditions": [{"name": n, "exp_id": e} for n, e in results],
        "completed_at": datetime.now().isoformat(),
    }

    import json

    meta_path = f"experiments/{exp_base}/ablation_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'#'*60}")
    print(f"# ABLATION STUDY COMPLETE")
    print(f"# Results: experiments/{exp_base}")
    print(
        f"# Run visualization: python visualization/scripts/ablation_visualization.py {exp_base}"
    )
    print(f"{'#'*60}")

    return exp_base


def main():
    parser = argparse.ArgumentParser(description="Run Ablation Studies")
    parser.add_argument(
        "--type",
        choices=["temperature", "market_params", "all"],
        default="temperature",
        help="Ablation study type",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output experiment base path"
    )

    args = parser.parse_args()

    if args.type == "all":
        for abl_type in ABLATION_CONFIGS:
            asyncio.run(run_ablation_study(abl_type))
    else:
        asyncio.run(run_ablation_study(args.type, args.output))


if __name__ == "__main__":
    main()
