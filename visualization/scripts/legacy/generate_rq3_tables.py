#!/usr/bin/env python3
"""
Generate RQ3 LaTeX tables for paper.

Conditions:
  Baseline (from RQ2 seller-only + Real + PQP):
    Rep         → rq2/r_wsc_R_pressure_quickprofits
    Rep+Warrant → rq2/rw_wsc_R_pressure_quickprofits
  Treatment (RQ3 both-comm + Real + PQP):
    Rep, Comm         → rq3/r_both_R_pqp
    Rep+Warrant, Comm → rq3/rw_both_R_pqp

Outputs:
  visualization/table/paper/rq3/rq3_summary_stats.tex
  visualization/table/paper/rq3/rq3_product_quality.tex
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from paper_data_utils import (
    load_results,
    aggregate_by_run,
    market_run_stats_with_deceptions,
    product_quality_run_stats,
)
from paper_table_generator import (
    create_buyer_comm_table,
    create_buyer_comm_quality_table,
)


def main():
    parser = argparse.ArgumentParser(description="Generate RQ3 LaTeX tables")
    parser.add_argument(
        "--base-dir",
        default="experiments/gpt-4o-mini/paper",
        help="Base experiment directory (default: experiments/gpt-4o-mini/paper)",
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/table/paper/rq3",
        help="Output directory for .tex files",
    )
    args = parser.parse_args()

    base = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Condition label → data directory (relative to base)
    dirs = {
        "Rep":                base / "rq2/r_wsc_R_pressure_quickprofits",
        "Rep, Comm":          base / "rq3/r_both_R_pqp",
        "Rep+Warrant":        base / "rq2/rw_wsc_R_pressure_quickprofits",
        "Rep+Warrant, Comm":  base / "rq3/rw_both_R_pqp",
    }

    print("=" * 60)
    print("RQ3: Generating LaTeX Tables")
    print("=" * 60)

    stats_map = {}
    quality_map = {}

    for label, data_dir in dirs.items():
        print(f"\n[{label}] Loading from: {data_dir}")
        df = load_results(str(data_dir))
        if df.empty:
            print(f"  WARNING: no data found, skipping.")
            continue
        stats_map[label] = aggregate_by_run(df, market_run_stats_with_deceptions)
        quality_map[label] = aggregate_by_run(df, product_quality_run_stats)
        n_runs = df["run_id"].nunique()
        print(f"  Loaded {n_runs} runs, {len(df)} transactions.")

    if not stats_map:
        print("\nERROR: No data loaded. Check --base-dir path.")
        sys.exit(1)

    print("\n--- Generating tables ---")
    create_buyer_comm_table(stats_map, output_dir / "rq3_summary_stats.tex")
    create_buyer_comm_quality_table(quality_map, output_dir / "rq3_product_quality.tex")

    print(f"\n✅  RQ3 tables saved to: {output_dir}")


if __name__ == "__main__":
    main()
