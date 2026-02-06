#!/usr/bin/env python3
"""
Generate All Paper Tables

This script generates all LaTeX tables required for the ICML 2025 paper
in the correct format for direct inclusion in the paper.

Usage:
    python generate_all_paper_tables.py --rq1 r1_dir r2_dir r3_dir r4_dir --rq2 dir1 dir2 ... --rq3 dir1 dir2

Each research question requires different directories:
- RQ1: Requires 4 directories (Rep market, Rep probes, RW market, RW probes)
- RQ2: Requires experiment directories for different constraint types
- RQ3: Requires 2 directories (Rep+Comm, RW+Comm)
"""

import argparse
import sys
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Generate all paper tables for ICML 2025")

    # RQ1 arguments
    parser.add_argument("--rq1", nargs=4, metavar=('R_MARKET', 'R_PROBE', 'RW_MARKET', 'RW_PROBE'),
                       help="RQ1 directories: Rep market, Rep probes, RW market, RW probes")

    # RQ2 arguments
    parser.add_argument("--rq2", nargs='+', metavar='DIR',
                       help="RQ2 experiment directories")

    # RQ3 arguments
    parser.add_argument("--rq3", nargs=2, metavar=('REP_COMM', 'RW_COMM'),
                       help="RQ3 directories: Rep+Comm, RW+Comm")

    # Output directory
    parser.add_argument("--output-dir", type=str, default="visualization/table/paper",
                       help="Output directory for all tables")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate RQ1 tables
    if args.rq1:
        print("\n" + "=" * 70)
        print("Generating RQ1 Tables")
        print("=" * 70)

        cmd = [
            sys.executable,
            str(Path(__file__).parent / "generate_rq1_paper_tables.py"),
            "--r-market-dir", args.rq1[0],
            "--r-probe-dir", args.rq1[1],
            "--rw-market-dir", args.rq1[2],
            "--rw-probe-dir", args.rq1[3],
            "--output-dir", str(output_dir / "rq1")
        ]

        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)

    # Generate RQ2 tables
    if args.rq2:
        print("\n" + "=" * 70)
        print("Generating RQ2 Tables")
        print("=" * 70)

        cmd = [
            sys.executable,
            str(Path(__file__).parent / "generate_rq2_paper_tables.py"),
            "--experiment-dirs"
        ] + args.rq2 + [
            "--output-dir", str(output_dir / "rq2")
        ]

        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)

    # Generate RQ3 tables
    if args.rq3:
        print("\n" + "=" * 70)
        print("Generating RQ3 Tables")
        print("=" * 70)

        cmd = [
            sys.executable,
            str(Path(__file__).parent / "generate_rq3_paper_tables.py"),
            "--rep-comm-dir", args.rq3[0],
            "--rw-comm-dir", args.rq3[1],
            "--output-dir", str(output_dir / "rq3")
        ]

        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)

    print("\n" + "=" * 70)
    print("All Paper Tables Generated!")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print("\nTables generated:")
    if args.rq1:
        print("  RQ1:")
        print("    - rq1_summary_stats.tex")
        print("    - rq1_summary_comparison.tex")
        print("    - rq1_product_quality.tex")
    if args.rq2:
        print("  RQ2:")
        print("    - rq2_initial_posts.tex")
        print("    - rq2_product_quality.tex")
        print("    - rq2_profit_decomposition.tex")
    if args.rq3:
        print("  RQ3:")
        print("    - rq3_summary_stats.tex")
        print("    - rq3_product_quality.tex")

    print("\nTo include these tables in your paper:")
    print("1. Copy the .tex files to your paper's sections/ directory")
    print("2. Use \\input{filename} to include each table")
    print("3. Or copy the table code directly into your LaTeX file")


if __name__ == "__main__":
    main()
