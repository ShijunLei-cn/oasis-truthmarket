#!/usr/bin/env python3
"""
Generate Basic Comparison Tables (No Probes Required)

This script generates basic market comparison tables when cognitive probe data is not available.
It's used for RQ2, RQ3, and RQ4 where only market results are needed.
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
from paper_table_generator import format_number, save_latex_table
from paper_data_utils import aggregate_by_run, load_results


def load_market_results(experiment_dir: str) -> pd.DataFrame:
    """Load market results from the experiment directory."""
    return load_results(
        experiment_dir,
        pattern="run_*_results.json",
        run_id_suffix="_results",
        description="market result"
    )


def calculate_market_statistics(df: pd.DataFrame, condition_name: str) -> Dict[str, Any]:
    """Calculate aggregate statistics from market results."""
    if df.empty:
        return {"condition": condition_name, "error": "No results found"}

    def _run_stats(run_data: pd.DataFrame) -> Dict[str, float]:
        total_transactions = run_data['transactions'].sum()
        total_seller_profit = run_data['seller_profit'].sum()
        total_buyer_utility = run_data['buyer_utility'].sum()
        avg_reputation = run_data.groupby('seller_id')['reputation'].last().mean()

        total_products = len(run_data)
        honest_products = run_data['is_honest'].sum()
        dishonest_products = total_products - honest_products

        return {
            'transactions': total_transactions,
            'seller_profit': total_seller_profit,
            'buyer_utility': total_buyer_utility,
            'reputation': avg_reputation,
            'honest_products': honest_products,
            'dishonest_products': dishonest_products,
            'total_products': total_products
        }

    stats = aggregate_by_run(df, _run_stats)
    if not stats:
        return {"condition": condition_name, "error": "No results found"}

    stats['condition'] = condition_name
    return stats


def create_basic_comparison_table(
    r_stats: Dict[str, Any],
    rw_stats: Dict[str, Any],
    output_file: Path
):
    """Create a basic comparison table."""

    latex_content = r"""\begin{table*}[t]
    \centering
    \caption{Market Outcomes Comparison}
    \label{tab:market_comparison}
    \begin{tabular}{lcccc}
    \toprule
    \textbf{Condition} & \textbf{Transactions} & \textbf{Profit (Seller)} & \textbf{Utility (Buyer)} & \textbf{Reputation} \\
    \midrule
"""

    # Reputation Only row
    latex_content += f"    Rep & "
    latex_content += f"{format_number(r_stats['transactions'], r_stats['transactions_std'])} & "
    latex_content += f"{format_number(r_stats['seller_profit'], r_stats['seller_profit_std'])} & "
    latex_content += f"{format_number(r_stats['buyer_utility'], r_stats['buyer_utility_std'])} & "
    latex_content += f"{format_number(r_stats['reputation'], r_stats['reputation_std'])} \\\\\n"

    # Reputation+Warrant row (bold for better performance)
    latex_content += f"    \\textbf{{Rep+Warrant}} & "
    latex_content += f"\\textbf{{{format_number(rw_stats['transactions'], rw_stats['transactions_std'])}}} & "
    latex_content += f"\\textbf{{{format_number(rw_stats['seller_profit'], rw_stats['seller_profit_std'])}}} & "
    latex_content += f"\\textbf{{{format_number(rw_stats['buyer_utility'], rw_stats['buyer_utility_std'])}}} & "
    latex_content += f"\\textbf{{{format_number(rw_stats['reputation'], rw_stats['reputation_std'])}}} \\\\\n"

    latex_content += r"""    \bottomrule
    \end{tabular}
\end{table*}
"""

    save_latex_table(latex_content, output_file)


def generate_basic_comparison_tables(
    r_market_dir: str,
    rw_market_dir: str,
    output_dir: str,
    table_prefix: str = "comparison"
):
    """Generate basic comparison tables without probe data."""

    print("=" * 70)
    print(f"Generating Basic Comparison Tables - {table_prefix.upper()}")
    print("=" * 70)

    # Load data
    print("\n📊 Loading experimental data...")

    print(f"\nLoading Reputation Only data from {r_market_dir}...")
    df_r_market = load_market_results(r_market_dir)

    print(f"\nLoading Reputation+Warrant data from {rw_market_dir}...")
    df_rw_market = load_market_results(rw_market_dir)

    if df_r_market.empty or df_rw_market.empty:
        print("ERROR: Market data not found or empty")
        return

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    r_stats = calculate_market_statistics(df_r_market, "Reputation Only")
    rw_stats = calculate_market_statistics(df_rw_market, "Reputation+Warrant")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate tables
    print("\n📄 Generating LaTeX tables...")

    output_file = output_path / f"{table_prefix}_market_comparison.tex"
    create_basic_comparison_table(r_stats, rw_stats, output_file)

    print(f"\n✅ Tables generated in: {output_path}")
    print(f"\nGenerated files:")
    print(f"  - {table_prefix}_market_comparison.tex")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Basic Comparison Tables (No Probes Required)"
    )
    parser.add_argument(
        "--r-market-dir", type=str, required=True,
        help="Reputation Only market results directory"
    )
    parser.add_argument(
        "--rw-market-dir", type=str, required=True,
        help="Reputation+Warrant market results directory"
    )
    parser.add_argument(
        "--output-dir", type=str, default="visualization/table/paper",
        help="Output directory for tables"
    )
    parser.add_argument(
        "--table-prefix", type=str, default="comparison",
        help="Prefix for table filenames (e.g., rq2, rq3, rq4)"
    )

    args = parser.parse_args()

    generate_basic_comparison_tables(
        args.r_market_dir,
        args.rw_market_dir,
        args.output_dir,
        args.table_prefix
    )


if __name__ == "__main__":
    main()
