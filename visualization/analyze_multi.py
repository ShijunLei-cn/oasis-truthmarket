#!/usr/bin/env python3
"""
Multi-run analysis command-line interface
Analyzes aggregated results from multiple simulation runs
"""

import argparse
import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.multi_run_analysis import MultiRunAnalyzer
from visualization.core.utils import setup_plot_style


async def analyze_experiment(experiment_id: str):
    """Analyze entire experiment results"""
    print(f"Starting analysis for experiment: {experiment_id}")
    
    analyzer = MultiRunAnalyzer(experiment_id)
    
    # Use the analyze() method which does everything
    analyzer.analyze()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze multi-run experiment results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --experiment-id exp_20251216_120000
  %(prog)s -e exp_20251216_120000
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        '-e', '--experiment-id',
        dest='experiment_id',
        required=True,
        help='Experiment ID (e.g., exp_20251216_120000)'
    )
    
    args = parser.parse_args()
    
    asyncio.run(analyze_experiment(args.experiment_id))


if __name__ == "__main__":
    main()
