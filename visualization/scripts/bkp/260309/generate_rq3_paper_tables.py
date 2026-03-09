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
from paper_data_utils import (
    aggregate_by_run,
    load_results,
    market_run_stats_with_deceptions,
    product_quality_run_stats,
)


def load_experiment_results(experiment_dir: str) -> pd.DataFrame:
    """Load experimental results from the experiment directory."""
    return load_results(
        experiment_dir,
        pattern="run_*_results.json",
        run_id_suffix="_results",
        description="communication result"
    )


def calculate_communication_statistics(replicas: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Calculate statistics for communication experiments."""
    return {
        label: aggregate_by_run(df, market_run_stats_with_deceptions)
        for label, df in replicas.items()
        if not df.empty
    }


def calculate_communication_quality(replicas: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Calculate product quality statistics for communication experiments."""
    return {
        label: aggregate_by_run(df, product_quality_run_stats)
        for label, df in replicas.items()
        if not df.empty
    }


def generate_rq3_tables(
    rep_comm_dir: str,
    rw_comm_dir: str,
    rep_no_comm_dir: str,
    rw_no_comm_dir: str,
    output_dir: str
):
    """Generate all RQ3 paper tables."""

    print("=" * 70)
    print("RQ3: Generating Paper Tables")
    print("=" * 70)

    # Load data
    print("\n📊 Loading experimental data...")

    df_map = {
        "Rep": load_experiment_results(rep_no_comm_dir),
        "Rep, Comm": load_experiment_results(rep_comm_dir),
        "Rep+Warrant": load_experiment_results(rw_no_comm_dir),
        "Rep+Warrant, Comm": load_experiment_results(rw_comm_dir),
    }

    if all(df.empty for df in df_map.values()):
        print("ERROR: Required data not found")
        return

    # Calculate statistics
    print("\n📈 Calculating statistics...")
    comm_stats = calculate_communication_statistics(df_map)
    quality_stats = calculate_communication_quality(df_map)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate tables
    print("\n📄 Generating LaTeX tables...")

    # 1. Summary Statistics with Deceptions and Reputation (tab:rq3_summary_stats)
    create_buyer_comm_table(
        comm_stats,
        output_path / "rq3_summary_stats.tex"
    )

    # 2. Product Quality Statistics (tab:rq3_product_quality)
    create_buyer_comm_quality_table(
        quality_stats,
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
    parser.add_argument("--rep-no-comm-dir", type=str, required=True,
                       help="Reputation only (no communication) experiment directory")
    parser.add_argument("--rw-no-comm-dir", type=str, required=True,
                       help="Reputation + Warranty (no communication) experiment directory")
    parser.add_argument("--output-dir", type=str, default="visualization/table/rq3",
                       help="Output directory for tables")

    args = parser.parse_args()

    generate_rq3_tables(
        args.rep_comm_dir,
        args.rw_comm_dir,
        args.rep_no_comm_dir,
        args.rw_no_comm_dir,
        args.output_dir
    )


if __name__ == "__main__":
    main()
