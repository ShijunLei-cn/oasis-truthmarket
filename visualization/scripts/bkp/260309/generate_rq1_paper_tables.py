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
from paper_data_utils import (
    aggregate_by_run,
    load_results,
    market_run_stats,
    product_quality_run_stats,
)


def load_market_results(experiment_dir: str) -> pd.DataFrame:
    """Load market results from the experiment directory."""
    return load_results(
        experiment_dir,
        pattern="run_*_results.json",
        run_id_suffix="_results",
        description="market result"
    )


def load_probe_results(experiment_dir: str) -> pd.DataFrame:
    """Load cognitive probe results from the experiment directory."""
    return load_results(
        experiment_dir,
        pattern="run_*_cognitive_probes.json",
        run_id_suffix="_cognitive_probes",
        description="cognitive probe result"
    )


def calculate_market_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate aggregate statistics from market results."""
    return aggregate_by_run(df, market_run_stats)


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
    return aggregate_by_run(df, product_quality_run_stats)


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
