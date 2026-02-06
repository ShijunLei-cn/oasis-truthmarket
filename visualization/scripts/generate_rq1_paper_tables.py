#!/usr/bin/env python3
"""
Generate RQ1 Paper Tables

This script generates LaTeX tables in the format required for the ICML 2025 paper.
It processes experimental results and creates publication-ready tables.
"""

import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import numpy as np
import os
from collections import defaultdict
from typing import Dict, List, Any, Tuple
import sys

# Add parent directory to path to import the paper table generator
sys.path.append(str(Path(__file__).parent))
from paper_table_generator import (
    create_summary_stats_table,
    create_manipulation_detection_table,
    create_product_quality_table,
    format_number
)


def load_market_results(experiment_dir: str) -> pd.DataFrame:
    """Load market results from the experiment directory."""
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


def load_probe_results(experiment_dir: str) -> pd.DataFrame:
    """Load cognitive probe results from the experiment directory."""
    path = Path(experiment_dir)
    all_results = []

    if not path.exists():
        print(f"ERROR: Experiment directory does not exist: {experiment_dir}")
        return pd.DataFrame()

    # Find all run_*_cognitive_probes.json files
    probe_files = list(path.glob("run_*_cognitive_probes.json"))
    if not probe_files:
        print(f"ERROR: No cognitive probe result files found in {experiment_dir}")
        return pd.DataFrame()

    print(f"Found {len(probe_files)} cognitive probe files")
    for file in probe_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    print(f"  Warning: {file.name} is empty")
                    continue
                # Add run identifier
                run_id = file.stem.replace("_cognitive_probes", "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
                print(f"  Loaded {len(data)} probes from {file.name}")
        except Exception as e:
            print(f"  ERROR loading {file.name}: {e}")

    if not all_results:
        print("ERROR: No probes loaded")
        return pd.DataFrame()

    return pd.DataFrame(all_results)


def calculate_market_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate aggregate statistics from market results."""
    if df.empty:
        return {"error": "No results found"}

    stats = {}

    # Group by run_id and calculate statistics for each run
    run_stats = []
    for run_id in df['run_id'].unique():
        run_data = df[df['run_id'] == run_id]

        # Calculate totals for this run
        total_transactions = run_data['transactions'].sum()
        total_seller_profit = run_data['seller_profit'].sum()
        total_buyer_utility = run_data['buyer_utility'].sum()
        avg_reputation = run_data['reputation'].mean()

        run_stats.append({
            'transactions': total_transactions,
            'seller_profit': total_seller_profit,
            'buyer_utility': total_buyer_utility,
            'reputation': avg_reputation
        })

    # Convert to DataFrame for easier calculation
    stats_df = pd.DataFrame(run_stats)

    # Calculate mean and std
    stats['transactions'] = float(stats_df['transactions'].mean())
    stats['transactions_std'] = float(stats_df['transactions'].std())

    stats['seller_profit'] = float(stats_df['seller_profit'].mean())
    stats['seller_profit_std'] = float(stats_df['seller_profit'].std())

    stats['buyer_utility'] = float(stats_df['buyer_utility'].mean())
    stats['buyer_utility_std'] = float(stats_df['buyer_utility'].std())

    stats['reputation'] = float(stats_df['reputation'].mean())
    stats['reputation_std'] = float(stats_df['reputation'].std())

    return stats


def calculate_manipulation_detection(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate manipulation detection rates by vulnerability type."""
    if df.empty:
        return {}

    detection_rates = {}

    # Map vulnerability types to match paper format
    vuln_mapping = {
        'initial_window': 'IW',
        'reputation_lag': 'RL',
        'value_imbalance': 'VI',
        'reentry': 'RE',
        'exit_strategy': 'ES'
    }

    for vuln_type, paper_code in vuln_mapping.items():
        subset = df[df['vulnerability_type'] == vuln_type]
        if len(subset) > 0:
            # Calculate detection rate as percentage
            detection_rate = subset['manipulation_detected'].mean() * 100
            detection_rates[paper_code] = float(detection_rate)
        else:
            detection_rates[paper_code] = 0.0

    return detection_rates


def calculate_product_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate product quality statistics."""
    if df.empty:
        return {}

    # Calculate totals for each run
    run_stats = []
    for run_id in df['run_id'].unique():
        run_data = df[df['run_id'] == run_id]

        # Aggregate by product quality
        hq_authentic_on_sale = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True)])
        hq_authentic_sold = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)])

        lq_authentic_on_sale = len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True)])
        lq_authentic_sold = len(run_data[(run_data['quality'] == 'LQ') & (run_data['is_authentic'] == True) & (run_data['sold'] == True)])

        hq_counterfeit_on_sale = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False)])
        hq_counterfeit_sold = len(run_data[(run_data['quality'] == 'HQ') & (run_data['is_authentic'] == False) & (run_data['sold'] == True)])

        run_stats.append({
            'hq_authentic_on_sale': hq_authentic_on_sale,
            'hq_authentic_sold': hq_authentic_sold,
            'lq_authentic_on_sale': lq_authentic_on_sale,
            'lq_authentic_sold': lq_authentic_sold,
            'hq_counterfeit_on_sale': hq_counterfeit_on_sale,
            'hq_counterfeit_sold': hq_counterfeit_sold
        })

    # Convert to DataFrame for easier calculation
    quality_df = pd.DataFrame(run_stats)

    # Calculate mean and std for each metric
    stats = {}
    for col in quality_df.columns:
        stats[col] = float(quality_df[col].mean())
        stats[f'{col}_std'] = float(quality_df[col].std())

    return stats


def generate_rq1_tables(
    r_market_dir: str,
    r_probe_dir: str,
    rw_market_dir: str,
    rw_probe_dir: str,
    output_dir: str
):
    """Generate all RQ1 paper tables."""

    print("=" * 70)
    print("RQ1: Generating Paper Tables")
    print("=" * 70)

    # Load data
    print("\n📊 Loading experimental data...")

    # Reputation Only
    df_r_market = load_market_results(r_market_dir)
    df_r_probes = load_probe_results(r_probe_dir)

    # Reputation + Warranty
    df_rw_market = load_market_results(rw_market_dir)
    df_rw_probes = load_probe_results(rw_probe_dir)

    if df_r_market.empty or df_rw_market.empty:
        print("ERROR: Market data not found")
        return

    if df_r_probes.empty or df_rw_probes.empty:
        print("ERROR: Probe data not found")
        return

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    r_market_stats = calculate_market_statistics(df_r_market)
    rw_market_stats = calculate_market_statistics(df_rw_market)

    r_detection = calculate_manipulation_detection(df_r_probes)
    rw_detection = calculate_manipulation_detection(df_rw_probes)

    r_quality = calculate_product_quality(df_r_market)
    rw_quality = calculate_product_quality(df_rw_market)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate tables
    print("\n📄 Generating LaTeX tables...")

    # 1. Summary Statistics (tab:rq1_summary_stats)
    create_summary_stats_table(
        r_market_stats,
        rw_market_stats,
        output_path / "rq1_summary_stats.tex"
    )

    # 2. Manipulation Detection (tab:rq1_summary_comparison)
    create_manipulation_detection_table(
        r_detection,
        rw_detection,
        output_path / "rq1_summary_comparison.tex"
    )

    # 3. Product Quality (tab:rq1_product_quality)
    create_product_quality_table(
        r_quality,
        rw_quality,
        output_path / "rq1_product_quality.tex"
    )

    print(f"\n✅ All RQ1 paper tables generated in: {output_path}")
    print("\nTables generated:")
    print("  - rq1_summary_stats.tex")
    print("  - rq1_summary_comparison.tex")
    print("  - rq1_product_quality.tex")


def main():
    parser = argparse.ArgumentParser(description="Generate RQ1 Paper Tables")
    parser.add_argument("--r-market-dir", type=str, required=True, help="Reputation Only market results directory")
    parser.add_argument("--r-probe-dir", type=str, required=True, help="Reputation Only probe results directory")
    parser.add_argument("--rw-market-dir", type=str, required=True, help="Reputation + Warranty market results directory")
    parser.add_argument("--rw-probe-dir", type=str, required=True, help="Reputation + Warranty probe results directory")
    parser.add_argument("--output-dir", type=str, default="visualization/table/rq1", help="Output directory for tables")

    args = parser.parse_args()

    generate_rq1_tables(
        args.r_market_dir,
        args.r_probe_dir,
        args.rw_market_dir,
        args.rw_probe_dir,
        args.output_dir
    )


if __name__ == "__main__":
    main()
