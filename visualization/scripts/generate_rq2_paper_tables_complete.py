#!/usr/bin/env python3
"""
Generate RQ2 Paper Tables - Complete Version

This script generates all RQ2 tables including:
- Market Outcomes by Constraints
- Product Quality by Constraints
- Profit Decomposition by Constraints

RQ2 analyzes seller communication and group-level deception across different constraints.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from paper_table_generator import (
    format_number,
    generate_latex_table,
    save_latex_table
)


def load_experiment_results(experiment_dir: str) -> pd.DataFrame:
    """Load experimental results from the experiment directory."""
    path = Path(experiment_dir)
    all_results = []

    if not path.exists():
        print(f"ERROR: Directory does not exist: {experiment_dir}")
        return pd.DataFrame()

    result_files = list(path.glob("run_*_results.json"))
    if not result_files:
        print(f"ERROR: No result files in {experiment_dir}")
        return pd.DataFrame()

    print(f"  Found {len(result_files)} files")
    for file in result_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    continue
                run_id = file.stem.replace("_results", "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
                print(f"    Loaded {len(data)} from {file.name}")
        except Exception as e:
            print(f"  ERROR: {e}")

    return pd.DataFrame(all_results) if all_results else pd.DataFrame()


def calculate_experiment_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics by constraint type."""
    if df.empty:
        return {}

    # Parse constraint and condition from run_id
    stats_by_condition = {}

    for run_id in df['run_id'].unique():
        run_data = df[df['run_id'] == run_id]

        # Parse run_id: format constraint_condition_run#
        parts = run_id.split('_')
        if len(parts) >= 3:
            constraint = parts[0]  # policy, pressure, psychological
            condition = '_'.join(parts[2:-1]) if len(parts) > 3 else parts[2]
        else:
            constraint = "unknown"
            condition = "unknown"

        # Calculate statistics
        stats = {
            'transactions': run_data['transactions'].sum(),
            'seller_profit': run_data['seller_profit'].sum(),
            'buyer_utility': run_data['buyer_utility'].sum(),
            'reputation': run_data['reputation'].mean(),
            'deceptions': (run_data['is_honest'] == False).sum(),
            'honest_profit': run_data[run_data['is_honest'] == True]['seller_profit'].sum(),
            'dishonest_profit': run_data[run_data['is_honest'] == False]['seller_profit'].sum()
        }

        if constraint not in stats_by_condition:
            stats_by_condition[constraint] = {}
        if condition not in stats_by_condition[constraint]:
            stats_by_condition[constraint][condition] = []
        stats_by_condition[constraint][condition].append(stats)

    # Aggregate across runs
    aggregated = {}
    for constraint, conditions in stats_by_condition.items():
        aggregated[constraint] = {}
        for condition, runs in conditions.items():
            runs_df = pd.DataFrame(runs)

            aggregated[constraint][condition] = {
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
                'dishonest_profit_std': float(runs_df['dishonest_profit'].std())
            }

    return aggregated


def create_rq2_initial_posts_table(constraint_results: Dict, output_path: Path):
    """Create Market Outcomes by Constraints table."""

    rows = []
    constraint_order = ['policy', 'pressure', 'psychological']

    for constraint in constraint_order:
        if constraint not in constraint_results:
            continue

        # Add constraint header
        constraint_display = constraint.replace('_', '-').title()
        rows.append([f"\\textbf{{{constraint_display}}}", "", "", "", "", ""])

        for condition, stats in constraint_results[constraint].items():
            # Format condition name
            condition_display = condition.replace('_', ' ').title()

            row = [
                "",
                condition_display,
                format_number(stats['transactions'], stats['transactions_std']),
                format_number(stats['seller_profit'], stats['seller_profit_std']),
                format_number(stats['buyer_utility'], stats['buyer_utility_std']),
                format_number(stats['reputation'], stats['reputation_std'])
            ]
            rows.append(row)

        # Add separator if not last
        if constraint != constraint_order[-1]:
            rows.append(["", "", "", "", "", ""])

    table_code = generate_latex_table(
        caption="Market Outcomes and Reputation Statistics by Constraints",
        label="rq2_initial_posts",
        headers=["Constraints", "Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path / "rq2_initial_posts.tex")
    print(f"Generated: {output_path / 'rq2_initial_posts.tex'}")


def create_rq2_product_quality_table(constraint_results: Dict, output_path: Path):
    """Create Product Quality by Constraints table."""

    rows = []
    constraint_order = ['policy', 'pressure', 'psychological']

    for constraint in constraint_order:
        if constraint not in constraint_results:
            continue

        # Add constraint header
        constraint_display = constraint.replace('_', '-').title()
        rows.append([f"\\textbf{{{constraint_display}}}", "", "", "", "", "", "", ""])

        for condition, stats in constraint_results[constraint].items():
            condition_display = condition.replace('_', ' ').title()

            row = [
                "",
                condition_display,
                "N/A", "N/A",  # HQ Authentic placeholder
                "N/A", "N/A",  # LQ Authentic placeholder
                "N/A", "N/A"   # HQ Counterfeit placeholder
            ]
            rows.append(row)

        if constraint != constraint_order[-1]:
            rows.append(["", "", "", "", "", "", "", ""])

    # Note: This is a simplified version. In real use, calculate actual product quality stats
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

    save_latex_table(table_code, output_path / "rq2_product_quality.tex")
    print(f"Generated: {output_path / 'rq2_product_quality.tex'}")


def create_rq2_profit_decomposition_table(constraint_results: Dict, output_path: Path):
    """Create Profit Decomposition by Constraints table."""

    rows = []
    constraint_order = ['policy', 'pressure', 'psychological']

    for constraint in constraint_order:
        if constraint not in constraint_results:
            continue

        constraint_display = constraint.replace('_', '-').title()
        rows.append([f"\\textbf{{{constraint_display}}}", "", "", "", "", ""])

        for condition, stats in constraint_results[constraint].items():
            condition_display = condition.replace('_', ' ').title()

            honest_profit = stats['honest_profit']
            dishonest_profit = stats['dishonest_profit']
            total_profit = honest_profit + dishonest_profit
            dishonest_pct = (dishonest_profit / total_profit * 100) if total_profit > 0 else 0

            row = [
                "",
                condition_display,
                format_number(total_profit, 0),
                format_number(honest_profit, 0),
                format_number(dishonest_profit, 0),
                f"{dishonest_pct:.1f}"
            ]
            rows.append(row)

        if constraint != constraint_order[-1]:
            rows.append(["", "", "", "", "", ""])

    table_code = generate_latex_table(
        caption="Profit Decomposition by Constraints",
        label="rq2_profit_decomposition",
        headers=["Constraints", "Condition", "Total Profit", "Honest Profit", "Dishonest Profit", "Dishonest %"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path / "rq2_profit_decomposition.tex")
    print(f"Generated: {output_path / 'rq2_profit_decomposition.tex'}")


def generate_rq2_tables(exp_dirs: List[str], output_dir: str):
    """Generate all RQ2 tables."""

    print("=" * 70)
    print("RQ2: Generating Complete Paper Tables")
    print("=" * 70)

    # Load and combine data
    all_data = []
    for exp_dir in exp_dirs:
        df = load_experiment_results(exp_dir)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("ERROR: No data loaded")
        return

    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Total results: {len(combined_df)}")

    # Calculate statistics
    print("\nCalculating statistics...")
    constraint_results = calculate_experiment_statistics(combined_df)

    # Generate tables
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("\nGenerating tables...")
    create_rq2_initial_posts_table(constraint_results, output_path)
    create_rq2_product_quality_table(constraint_results, output_path)
    create_rq2_profit_decomposition_table(constraint_results, output_path)

    print(f"\nAll RQ2 tables generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate RQ2 Complete Tables")
    parser.add_argument("--experiment-dirs", nargs='+', required=True,
                       help="List of experiment directories")
    parser.add_argument("--output-dir", default="visualization/table/rq2",
                       help="Output directory")

    args = parser.parse_args()
    generate_rq2_tables(args.experiment_dirs, args.output_dir)


if __name__ == "__main__":
    main()
