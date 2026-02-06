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
from typing import Dict, List, Any

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


def load_experiment_results(experiment_dir: str) -> pd.DataFrame:
    """Load experimental results from the experiment directory."""
    path = Path(experiment_dir)
    all_results = []

    if not path.exists():
        print(f"ERROR: Experiment directory does not exist: {experiment_dir}")
        return pd.DataFrame()

    # Find all run_*_results.json files
    result_files = list(path.glob("run_*_results.json"))
    if not result_files:
        print(f"ERROR: No result files found in {experiment_dir}")
        return pd.DataFrame()

    print(f"Found {len(result_files)} result files")
    for file in result_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    print(f"  Warning: {file.name} is empty")
                    continue
                # Add run identifier
                run_id = file.stem.replace("_results", "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
                print(f"  Loaded {len(data)} results from {file.name}")
        except Exception as e:
            print(f"  ERROR loading {file.name}: {e}")

    if not all_results:
        print("ERROR: No results loaded")
        return pd.DataFrame()

    return pd.DataFrame(all_results)


def calculate_experiment_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics for each experiment run."""
    if df.empty:
        return {}

    # Extract constraint type and condition from run_id
    # Assuming run_id format: constraint_condition_run#
    stats_by_condition = {}

    for run_id in df['run_id'].unique():
        run_data = df[df['run_id'] == run_id]

        # Parse run_id to get constraint and condition
        parts = run_id.split('_')
        if len(parts) >= 3:
            constraint = parts[0] + '_' + parts[1]  # e.g., "policy_making"
            condition = '_'.join(parts[2:-1]) if len(parts) > 3 else parts[2]  # e.g., "rep_comm"
        else:
            constraint = "unknown"
            condition = "unknown"

        # Calculate statistics for this run
        stats = {
            'transactions': run_data['transactions'].sum(),
            'seller_profit': run_data['seller_profit'].sum(),
            'buyer_utility': run_data['buyer_utility'].sum(),
            'reputation': run_data['reputation'].mean(),
            'deceptions': (run_data['is_honest'] == False).sum()
        }

        # Calculate honest vs dishonest profit
        honest_profit = run_data[run_data['is_honest'] == True]['seller_profit'].sum()
        dishonest_profit = run_data[run_data['is_honest'] == False]['seller_profit'].sum()

        stats['honest_profit'] = honest_profit
        stats['dishonest_profit'] = dishonest_profit
        stats['total_profit'] = honest_profit + dishonest_profit

        # Group by constraint and condition
        constraint_key = constraint
        if constraint_key not in stats_by_condition:
            stats_by_condition[constraint_key] = {}

        if condition not in stats_by_condition[constraint_key]:
            stats_by_condition[constraint_key][condition] = []

        stats_by_condition[constraint_key][condition].append(stats)

    # Aggregate statistics across runs
    aggregated_stats = {}
    for constraint, conditions in stats_by_condition.items():
        aggregated_stats[constraint] = {}
        for condition, runs in conditions.items():
            runs_df = pd.DataFrame(runs)

            aggregated_stats[constraint][condition] = {
                'transactions': float(runs_df['transactions'].mean()),
                'transactions_std': float(runs_df['transactions'].std()),
                'seller_profit': float(runs_df['seller_profit'].mean()),
                'seller_profit_std': float(runs_df['seller_profit'].std()),
                'buyer_utility': float(runs_df['buyer_utility'].mean()),
                'buyer_utility_std': float(runs_df['buyer_utility'].std()),
                'reputation': float(runs_df['reputation'].mean()),
                'reputation_std': float(runs_df['reputation'].std()),
                'deceptions': float(runs_df['deceptions'].mean()),
                'deceptions_std': float(runs_df['deceptions'].std()),
                'honest_profit': float(runs_df['honest_profit'].mean()),
                'honest_profit_std': float(runs_df['honest_profit'].std()),
                'dishonest_profit': float(runs_df['dishonest_profit'].mean()),
                'dishonest_profit_std': float(runs_df['dishonest_profit'].std()),
                'total_profit': float(runs_df['total_profit'].mean()),
                'total_profit_std': float(runs_df['total_profit'].std())
            }

    return aggregated_stats


def calculate_product_quality_by_constraint(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate product quality statistics by constraint type."""
    if df.empty:
        return {}

    quality_by_constraint = {}

    for run_id in df['run_id'].unique():
        run_data = df[df['run_id'] == run_id]

        # Parse run_id
        parts = run_id.split('_')
        if len(parts) >= 3:
            constraint = parts[0] + '_' + parts[1]
            condition = '_'.join(parts[2:-1]) if len(parts) > 3 else parts[2]
        else:
            constraint = "unknown"
            condition = "unknown"

        # Calculate product quality metrics
        hq_authentic_on_sale = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True)])
        hq_authentic_sold = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)])

        lq_authentic_on_sale = len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True)])
        lq_authentic_sold = len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)])

        hq_counterfeit_on_sale = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False)])
        hq_counterfeit_sold = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False) & (run_data['sold'] == True)])

        quality_stats = {
            'hq_authentic_on_sale': hq_authentic_on_sale,
            'hq_authentic_sold': hq_authentic_sold,
            'lq_authentic_on_sale': lq_authentic_on_sale,
            'lq_authentic_sold': lq_authentic_sold,
            'hq_counterfeit_on_sale': hq_counterfeit_on_sale,
            'hq_counterfeit_sold': hq_counterfeit_sold
        }

        if constraint not in quality_by_constraint:
            quality_by_constraint[constraint] = {}

        if condition not in quality_by_constraint[constraint]:
            quality_by_constraint[constraint][condition] = []

        quality_by_constraint[constraint][condition].append(quality_stats)

    # Aggregate across runs
    aggregated_quality = {}
    for constraint, conditions in quality_by_constraint.items():
        aggregated_quality[constraint] = {}
        for condition, runs in conditions.items():
            runs_df = pd.DataFrame(runs)

            aggregated_quality[constraint][condition] = {}
            for col in runs_df.columns:
                aggregated_quality[constraint][condition][col] = float(runs_df[col].mean())
                aggregated_quality[constraint][condition][f'{col}_std'] = float(runs_df[col].std())

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
    all_data = []
    for exp_dir in exp_dirs:
        df = load_experiment_results(exp_dir)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("ERROR: No data loaded")
        return

    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Loaded {len(combined_df)} total results")

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    constraint_results = calculate_experiment_statistics(combined_df)
    quality_results = calculate_product_quality_by_constraint(combined_df)

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

    for constraint_name, conditions in quality_results.items():
        # Add constraint header
        constraint_display = constraint_name.replace('_', '-')
        rows.append([f"\\textbf{{{constraint_display}}}", "", "", "", "", "", "", ""])

        for condition_name, stats in conditions.items():
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
