#!/usr/bin/env python3
"""
Generate RQ3 Paper Tables - Complete Version

This script generates all RQ3 tables including:
- Summary Statistics with Deceptions and Reputation
- Product Quality Statistics

RQ3 analyzes buyer communication and collective adaptation against deceptive sellers.
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
    """Load experimental results from directory."""
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


def calculate_communication_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics for communication experiments."""
    if df.empty:
        return {}

    # Separate by condition based on run_id
    rep_comm_data = df[df['run_id'].str.contains('rep.*comm', case=False, na=False)]
    rw_comm_data = df[df['run_id'].str.contains('rep.*warrant.*comm', case=False, na=False)]

    def calc_condition_stats(condition_df: pd.DataFrame) -> Dict[str, Any]:
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
        'rep_comm': calc_condition_stats(rep_comm_data),
        'rw_comm': calc_condition_stats(rw_comm_data)
    }


def create_rq3_summary_table(comm_stats: Dict, output_path: Path):
    """Create Summary Statistics with Deceptions and Reputation table."""

    if not comm_stats.get('rep_comm') or not comm_stats.get('rw_comm'):
        print("ERROR: Missing data for RQ3 summary table")
        return

    rep_comm = comm_stats['rep_comm']
    rw_comm = comm_stats['rw_comm']

    rows = [
        [
            "Rep, Comm",
            format_number(rep_comm['transactions'], rep_comm['transactions_std']),
            format_number(rep_comm['seller_profit'], rep_comm['seller_profit_std']),
            format_number(rep_comm['buyer_utility'], rep_comm['buyer_utility_std']),
            format_number(rep_comm['deceptions'], rep_comm['deceptions_std']),
            format_number(rep_comm['reputation'], rep_comm['reputation_std'])
        ],
        [
            "Rep+Warrant, Comm",
            format_number(rw_comm['transactions'], rw_comm['transactions_std']),
            f"\\textbf{{{format_number(rw_comm['seller_profit'], rw_comm['seller_profit_std'])}}}",
            f"\\textbf{{{format_number(rw_comm['buyer_utility'], rw_comm['buyer_utility_std'])}}}",
            f"\\textbf{{{format_number(rw_comm['deceptions'], rw_comm['deceptions_std'])}}}",
            format_number(rw_comm['reputation'], rw_comm['reputation_std'])
        ]
    ]

    table_code = generate_latex_table(
        caption="Summary Statistics with Deceptions and Reputation",
        label="rq3_summary_stats",
        headers=["Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Deceptions", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path / "rq3_summary_stats.tex")
    print(f"Generated: {output_path / 'rq3_summary_stats.tex'}")


def create_rq3_product_quality_table(df: pd.DataFrame, output_path: Path):
    """Create Product Quality Statistics table for RQ3."""

    if df.empty:
        print("WARNING: No data for product quality table")
        return

    # Separate conditions
    rep_comm_data = df[df['run_id'].str.contains('rep.*comm', case=False, na=False)]
    rw_comm_data = df[df['run_id'].str.contains('rep.*warrant.*comm', case=False, na=False)]

    def calc_quality_stats(condition_df: pd.DataFrame) -> Dict[str, Any]:
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

        quality_df = pd.DataFrame(run_quality_stats)
        if quality_df.empty:
            return {}

        aggregated = {}
        for col in quality_df.columns:
            aggregated[col] = float(quality_df[col].mean())
            aggregated[f'{col}_std'] = float(quality_df[col].std())

        return aggregated

    rep_comm_quality = calc_quality_stats(rep_comm_data)
    rw_comm_quality = calc_quality_stats(rw_comm_data)

    if not rep_comm_quality or not rw_comm_quality:
        print("WARNING: Missing quality data")
        return

    rows = [
        [
            "Rep, Comm",
            format_number(rep_comm_quality.get('hq_authentic_on_sale', 0), rep_comm_quality.get('hq_authentic_on_sale_std', 0)),
            format_number(rep_comm_quality.get('hq_authentic_sold', 0), rep_comm_quality.get('hq_authentic_sold_std', 0)),
            format_number(rep_comm_quality.get('lq_authentic_on_sale', 0), rep_comm_quality.get('lq_authentic_on_sale_std', 0)),
            format_number(rep_comm_quality.get('lq_authentic_sold', 0), rep_comm_quality.get('lq_authentic_sold_std', 0)),
            format_number(rep_comm_quality.get('hq_counterfeit_on_sale', 0), rep_comm_quality.get('hq_counterfeit_on_sale_std', 0)),
            format_number(rep_comm_quality.get('hq_counterfeit_sold', 0), rep_comm_quality.get('hq_counterfeit_sold_std', 0))
        ],
        [
            "Rep+Warrant, Comm",
            f"\\textbf{{{format_number(rw_comm_quality.get('hq_authentic_on_sale', 0), rw_comm_quality.get('hq_authentic_on_sale_std', 0))}}}",
            f"\\textbf{{{format_number(rw_comm_quality.get('hq_authentic_sold', 0), rw_comm_quality.get('hq_authentic_sold_std', 0))}}}",
            f"\\textbf{{{format_number(rw_comm_quality.get('lq_authentic_on_sale', 0), rw_comm_quality.get('lq_authentic_on_sale_std', 0))}}}",
            f"\\textbf{{{format_number(rw_comm_quality.get('lq_authentic_sold', 0), rw_comm_quality.get('lq_authentic_sold_std', 0))}}}",
            f"\\textbf{{{format_number(rw_comm_quality.get('hq_counterfeit_on_sale', 0), rw_comm_quality.get('hq_counterfeit_on_sale_std', 0))}}}",
            f"\\textbf{{{format_number(rw_comm_quality.get('hq_counterfeit_sold', 0), rw_comm_quality.get('hq_counterfeit_sold_std', 0))}}}"
        ]
    ]

    table_code = generate_latex_table(
        caption="Product Quality Statistics",
        label="rq3_product_quality",
        headers=["Condition", "On sale", "Sold", "On sale", "Sold", "On sale", "Sold"],
        rows=rows,
        table_type="table*",
        position="t",
        multicolumn_headers={
            1: (2, "HQ Authentic"),
            3: (2, "LQ Authentic"),
            5: (2, "HQ Counterfeit")
        }
    )

    save_latex_table(table_code, output_path / "rq3_product_quality.tex")
    print(f"Generated: {output_path / 'rq3_product_quality.tex'}")


def generate_rq3_tables(rep_comm_dir: str, rw_comm_dir: str, output_dir: str):
    """Generate all RQ3 tables."""

    print("=" * 70)
    print("RQ3: Generating Complete Paper Tables")
    print("=" * 70)

    # Load data
    print("\nLoading experimental data...")
    df_rep_comm = load_experiment_results(rep_comm_dir)
    df_rw_comm = load_experiment_results(rw_comm_dir)

    if df_rep_comm.empty or df_rw_comm.empty:
        print("ERROR: Missing data")
        return

    # Combine data
    combined_df = pd.concat([df_rep_comm, df_rw_comm], ignore_index=True)
    print(f"Total results: {len(combined_df)}")

    # Calculate statistics
    print("\nCalculating statistics...")
    comm_stats = calculate_communication_statistics(combined_df)

    # Generate tables
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("\nGenerating tables...")
    create_rq3_summary_table(comm_stats, output_path)
    create_rq3_product_quality_table(combined_df, output_path)

    print(f"\nAll RQ3 tables generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate RQ3 Complete Tables")
    parser.add_argument("--rep-comm-dir", type=str, required=True,
                       help="Reputation + Communication directory")
    parser.add_argument("--rw-comm-dir", type=str, required=True,
                       help="Reputation + Warranty + Communication directory")
    parser.add_argument("--output-dir", type=str, default="visualization/table/rq3",
                       help="Output directory")

    args = parser.parse_args()

    generate_rq3_tables(
        args.rep_comm_dir,
        args.rw_comm_dir,
        args.output_dir
    )


if __name__ == "__main__":
    main()
