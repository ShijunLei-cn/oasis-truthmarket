#!/usr/bin/env python3
"""
Generate RQ3 Paper Tables

This script generates LaTeX tables for RQ3 analysis in the format required for the ICML 2025 paper.
RQ3 analyzes the impact of buyer communication on collective defense against deceptive sellers.
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
    create_buyer_comm_table,
    create_buyer_comm_quality_table,
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


def calculate_communication_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics for communication experiments."""
    if df.empty:
        return {}

    # Separate Rep+Comm and Rep+Warrant+Comm conditions
    rep_comm_data = df[df['run_id'].str.contains('rep_comm', case=False, na=False)]
    rw_comm_data = df[df['run_id'].str.contains('rep.*warrant.*comm', case=False, na=False)]

    def calculate_condition_stats(condition_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics for a specific condition."""
        if condition_df.empty:
            return {}

        run_stats = []
        for run_id in condition_df['run_id'].unique():
            run_data = condition_df[condition_df['run_id'] == run_id]

            stats = {
                'transactions': run_data['transactions'].sum(),
                'seller_profit': run_data['seller_profit'].sum(),
                'buyer_utility': run_data['buyer_utility'].sum(),
                'reputation': run_data['reputation'].mean(),
                'deceptions': (run_data['is_honest'] == False).sum()
            }

            run_stats.append(stats)

        # Convert to DataFrame for aggregation
        stats_df = pd.DataFrame(run_stats)

        if stats_df.empty:
            return {}

        return {
            'transactions': float(stats_df['transactions'].mean()),
            'transactions_std': float(stats_df['transactions'].std()),
            'seller_profit': float(stats_df['seller_profit'].mean()),
            'seller_profit_std': float(stats_df['seller_profit'].std()),
            'buyer_utility': float(stats_df['buyer_utility'].mean()),
            'buyer_utility_std': float(stats_df['buyer_utility'].std()),
            'reputation': float(stats_df['reputation'].mean()),
            'reputation_std': float(stats_df['reputation'].std()),
            'deceptions': float(stats_df['deceptions'].mean()),
            'deceptions_std': float(stats_df['deceptions'].std())
        }

    return {
        'rep_comm': calculate_condition_stats(rep_comm_data),
        'rep_warrant_comm': calculate_condition_stats(rw_comm_data)
    }


def calculate_communication_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate product quality statistics for communication experiments."""
    if df.empty:
        return {}

    # Separate conditions
    rep_comm_data = df[df['run_id'].str.contains('rep_comm', case=False, na=False)]
    rw_comm_data = df[df['run_id'].str.contains('rep.*warrant.*comm', case=False, na=False)]

    def calculate_quality_stats(condition_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate product quality statistics for a condition."""
        if condition_df.empty:
            return {}

        run_quality_stats = []
        for run_id in condition_df['run_id'].unique():
            run_data = condition_df[condition_df['run_id'] == run_id]

            quality_stats = {
                'hq_authentic_on_sale': len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True)]),
                'hq_authentic_sold': len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)]),
                'lq_authentic_on_sale': len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True)]),
                'lq_authentic_sold': len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)]),
                'hq_counterfeit_on_sale': len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False)]),
                'hq_counterfeit_sold': len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False) & (run_data['sold'] == True)])
            }

            run_quality_stats.append(quality_stats)

        # Aggregate across runs
        quality_df = pd.DataFrame(run_quality_stats)

        if quality_df.empty:
            return {}

        aggregated = {}
        for col in quality_df.columns:
            aggregated[col] = float(quality_df[col].mean())
            aggregated[f'{col}_std'] = float(quality_df[col].std())

        return aggregated

    return {
        'rep_comm': calculate_quality_stats(rep_comm_data),
        'rep_warrant_comm': calculate_quality_stats(rw_comm_data)
    }


def generate_rq3_tables(
    rep_comm_dir: str,
    rw_comm_dir: str,
    output_dir: str
):
    """Generate all RQ3 paper tables."""

    print("=" * 70)
    print("RQ3: Generating Paper Tables")
    print("=" * 70)

    # Load data
    print("\n📊 Loading experimental data...")

    df_rep_comm = load_experiment_results(rep_comm_dir)
    df_rw_comm = load_experiment_results(rw_comm_dir)

    if df_rep_comm.empty or df_rw_comm.empty:
        print("ERROR: Required data not found")
        return

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    comm_stats = calculate_communication_statistics(pd.concat([df_rep_comm, df_rw_comm], ignore_index=True))
    quality_stats = calculate_communication_quality(pd.concat([df_rep_comm, df_rw_comm], ignore_index=True))

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate tables
    print("\n📄 Generating LaTeX tables...")

    # 1. Summary Statistics with Deceptions and Reputation (tab:rq3_summary_stats)
    create_buyer_comm_table(
        comm_stats['rep_comm'],
        comm_stats['rep_warrant_comm'],
        output_path / "rq3_summary_stats.tex"
    )

    # 2. Product Quality Statistics (tab:rq3_product_quality)
    create_buyer_comm_quality_table(
        quality_stats['rep_comm'],
        quality_stats['rep_warrant_comm'],
        output_path / "rq3_product_quality.tex"
    )

    print(f"\n✅ All RQ3 paper tables generated in: {output_path}")
    print("\nTables generated:")
    print("  - rq3_summary_stats.tex")
    print("  - rq3_product_quality.tex")


def main():
    parser = argparse.ArgumentParser(description="Generate RQ3 Paper Tables")
    parser.add_argument("--rep-comm-dir", type=str, required=True,
                       help="Reputation + Communication experiment directory")
    parser.add_argument("--rw-comm-dir", type=str, required=True,
                       help="Reputation + Warranty + Communication experiment directory")
    parser.add_argument("--output-dir", type=str, default="visualization/table/rq3",
                       help="Output directory for tables")

    args = parser.parse_args()

    generate_rq3_tables(
        args.rep_comm_dir,
        args.rw_comm_dir,
        args.output_dir
    )


if __name__ == "__main__":
    main()
