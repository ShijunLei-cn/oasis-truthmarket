#!/usr/bin/env python3
"""
Generate RQ2 Paper Tables

This script generates LaTeX tables for RQ2 analysis in the format required for the ICML 2025 paper.
RQ2 analyzes the impact of communication channels on seller behavior under different constraint types.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from typing import Dict, List, Any, Tuple

# Add parent directory to path to import the paper table generator
sys.path.append(str(Path(__file__).parent))
from paper_table_generator import (
    create_market_outcomes_table,
    create_product_quality_table,
    create_profit_decomposition_table,
    generate_latex_table,
    save_latex_table,
    format_number
)
from paper_data_utils import (
    aggregate_by_run,
    aggregate_stats,
    load_results,
    market_run_stats_with_breakdown,
    product_quality_run_stats,
)


def load_experiment_results(experiment_dir: str) -> pd.DataFrame:
    """Load experimental results from the experiment directory."""
    return load_results(
        experiment_dir,
        pattern="run_*_results.json",
        run_id_suffix="_results",
        description="experiment result"
    )


def _condition_from_config(config: Dict[str, Any]) -> str:
    """Derive condition label from config, matching the paper labels."""
    market_type = config.get("market_type", "")
    comm_type = config.get("communication_type", "")
    comm_channel = config.get("communication_channel_type", "")

    base_is_warrant = market_type == "reputation_and_warrant"
    has_comm = comm_type == "seller" and comm_channel.lower() == "real"

    if base_is_warrant and has_comm:
        return "Rep+Warrant, Comm"
    if base_is_warrant:
        return "Rep+Warrant"
    if has_comm:
        return "Rep, Comm"
    return "Rep"


def _constraint_from_config(config: Dict[str, Any]) -> str:
    """Extract constraint name from config (posts4seller) and map to paper label."""
    raw = config.get("posts4seller") or config.get("constraint") or "unknown"
    mapping = {
        "policy_making": "Policy-Making",
        "pressure_quickprofits": "Pressure-Quick-Profits",
        "psychological-based-attack": "Psychological-Attack",
    }
    return mapping.get(raw, raw.replace("_", "-"))


def calculate_experiment_statistics(datasets: List[Tuple[str, str, pd.DataFrame]]) -> Dict[str, Any]:
    """Calculate statistics for each experiment run."""
    stats_by_condition: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for constraint, condition, df in datasets:
        if df.empty:
            continue
        stats = aggregate_by_run(df, market_run_stats_with_breakdown)
        if not stats:
            continue
        stats_by_condition.setdefault(constraint, {}).setdefault(condition, []).append(stats)

    aggregated_stats: Dict[str, Dict[str, Dict[str, float]]] = {}
    for constraint, conditions in stats_by_condition.items():
        aggregated_stats[constraint] = {}
        for condition, runs in conditions.items():
            aggregated_stats[constraint][condition] = aggregate_stats(runs)

    return aggregated_stats


def calculate_product_quality_by_constraint(datasets: List[Tuple[str, str, pd.DataFrame]]) -> Dict[str, Any]:
    """Calculate product quality statistics by constraint type."""
    quality_by_constraint: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for constraint, condition, df in datasets:
        if df.empty:
            continue
        stats = aggregate_by_run(df, product_quality_run_stats)
        if not stats:
            continue
        quality_by_constraint.setdefault(constraint, {}).setdefault(condition, []).append(stats)

    aggregated_quality: Dict[str, Dict[str, Dict[str, float]]] = {}
    for constraint, conditions in quality_by_constraint.items():
        aggregated_quality[constraint] = {}
        for condition, runs in conditions.items():
            aggregated_quality[constraint][condition] = aggregate_stats(runs)

    return aggregated_quality


def generate_rq2_tables(
    exp_dirs: List[str],
    output_dir: str
):
    """Generate all RQ2 paper tables."""

    print("=" * 70)
    print("RQ2: Generating Paper Tables")
    print("=" * 70)

    # Load and combine all experimental data
    print("\n📊 Loading experimental data...")
    datasets: List[Tuple[str, str, pd.DataFrame]] = []
    for exp_dir in exp_dirs:
        config_path = Path(exp_dir) / "experiment_config.json"
        if not config_path.exists():
            print(f"  ⚠ Missing config for {exp_dir}, skipping")
            continue
        try:
            config = json.loads(config_path.read_text())
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  ⚠ Failed to read config {config_path}: {exc}")
            continue

        constraint = _constraint_from_config(config)
        condition = _condition_from_config(config)

        df = load_experiment_results(exp_dir)
        if df.empty:
            print(f"  ⚠ No results in {exp_dir}")
            continue
        datasets.append((constraint, condition, df))

    if not datasets:
        print("ERROR: No data loaded")
        return

    total_rows = sum(len(df) for _, _, df in datasets)
    print(f"Loaded {total_rows} total results")

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    constraint_results = calculate_experiment_statistics(datasets)
    quality_results = calculate_product_quality_by_constraint(datasets)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate tables
    print("\n📄 Generating LaTeX tables...")

    # 1. Market Outcomes and Reputation Statistics by Constraints (tab:rq2_initial_posts)
    create_market_outcomes_table(
        constraint_results,
        output_path / "rq2_initial_posts.tex"
    )

    # 2. Product Quality Statistics by Constraints (tab:rq2_product_quality)
    # This requires a custom function for the complex structure
    create_rq2_product_quality_table(
        quality_results,
        output_path / "rq2_product_quality.tex"
    )

    # 3. Profit Decomposition by Constraints (tab:rq2_profit_decomposition)
    create_profit_decomposition_table(
        constraint_results,
        output_path / "rq2_profit_decomposition.tex"
    )

    print(f"\n✅ All RQ2 paper tables generated in: {output_path}")
    print("\nTables generated:")
    print("  - rq2_initial_posts.tex")
    print("  - rq2_product_quality.tex")
    print("  - rq2_profit_decomposition.tex")


def create_rq2_product_quality_table(
    quality_results: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Create the Product Quality Statistics by Constraints table (tab:rq2_product_quality)."""

    rows = []
    condition_order = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]

    for constraint_name, conditions in quality_results.items():
        # Add constraint header
        constraint_display = constraint_name.replace('_', '-')
        rows.append([f"\\textbf{{{constraint_display}}}", "", "", "", "", "", "", ""])

        for condition_name in condition_order:
            if condition_name not in conditions:
                continue
            stats = conditions[condition_name]
            row = [
                "",
                condition_name,
                format_number(stats.get('hq_authentic_on_sale', 0), stats.get('hq_authentic_on_sale_std', 0)),
                format_number(stats.get('hq_authentic_sold', 0), stats.get('hq_authentic_sold_std', 0)),
                format_number(stats.get('lq_authentic_on_sale', 0), stats.get('lq_authentic_on_sale_std', 0)),
                format_number(stats.get('lq_authentic_sold', 0), stats.get('lq_authentic_sold_std', 0)),
                format_number(stats.get('hq_counterfeit_on_sale', 0), stats.get('hq_counterfeit_on_sale_std', 0)),
                format_number(stats.get('hq_counterfeit_sold', 0), stats.get('hq_counterfeit_sold_std', 0))
            ]
            rows.append(row)

        # Add separator line
        if constraint_name != list(quality_results.keys())[-1]:
            rows.append(["", "", "", "", "", "", "", ""])

    table_code = generate_latex_table(
        caption="Product Quality Statistics by Constraints",
        label="rq2_product_quality",
        headers=["Constraints", "Condition", "On sale", "Sold", "On sale", "Sold", "On sale", "Sold"],
        rows=rows,
        table_type="table*",
        position="t",
        multicolumn_headers={
            2: (2, "HQ Authentic"),
            4: (2, "LQ Authentic"),
            6: (2, "HQ Counterfeit")
        }
    )

    save_latex_table(table_code, output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate RQ2 Paper Tables")
    parser.add_argument("--experiment-dirs", type=str, nargs='+', required=True,
                       help="List of experiment directories to analyze")
    parser.add_argument("--output-dir", type=str, default="visualization/table/rq2",
                       help="Output directory for tables")

    args = parser.parse_args()

    generate_rq2_tables(
        args.experiment_dirs,
        args.output_dir
    )


if __name__ == "__main__":
    main()
