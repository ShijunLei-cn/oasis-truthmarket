#!/usr/bin/env python3
"""
Single run analysis command-line interface
Analyzes individual simulation run results and generates visualizations
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.single_run_analysis import analyze_single_run


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze single market simulation database and generate visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s market_sim.db
  %(prog)s experiments/exp_123/run_1.db --out output_dir
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        'db_path',
        help='Path to SQLite database file (e.g., market_sim.db)'
    )
    
    parser.add_argument(
        '--out', '--output',
        dest='out_dir',
        default=None,
        help='Output directory (default: analysis/outputs/<timestamp>)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db_path):
        print(f"Error: Database file not found: {args.db_path}")
        sys.exit(1)
    
    analyze_single_run(args.db_path, args.out_dir)


if __name__ == "__main__":
    main()
