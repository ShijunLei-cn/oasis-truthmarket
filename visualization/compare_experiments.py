#!/usr/bin/env python3
"""
Comparison analysis command-line interface
Compares results from different experiments
"""

import argparse
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.comparison_analysis import ComparisonAnalyzer


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Compare results from different experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config-file comparison_config.json
  %(prog)s --exp reputation_only:exp_123 --exp reputation_warrant:exp_456
  %(prog)s -e rep_only:exp_123 -e rep_warrant:exp_456 --out comparison_output
  %(prog)s --help

Config file format (JSON):
  {
    "reputation_only": "exp_20251216_120000",
    "reputation_warrant": "exp_20251216_130000"
  }
        """
    )
    
    parser.add_argument(
        '--config-file',
        dest='config_file',
        help='Path to JSON config file with experiment mappings'
    )
    
    parser.add_argument(
        '-e', '--exp',
        dest='experiments',
        action='append',
        help='Experiment mapping in format "name:experiment_id" (can be used multiple times)'
    )
    
    parser.add_argument(
        '--out', '--output',
        dest='output_dir',
        default=None,
        help='Output directory (default: analysis/comparison_<timestamp>)'
    )
    
    args = parser.parse_args()
    
    # Parse experiment configs
    experiment_configs = {}
    
    if args.config_file:
        if not os.path.exists(args.config_file):
            print(f"Error: Config file not found: {args.config_file}")
            sys.exit(1)
        
        with open(args.config_file, 'r', encoding='utf-8') as f:
            experiment_configs = json.load(f)
    
    if args.experiments:
        for exp_str in args.experiments:
            if ':' not in exp_str:
                print(f"Error: Invalid experiment format: {exp_str}")
                print("Expected format: name:experiment_id")
                sys.exit(1)
            
            name, exp_id = exp_str.split(':', 1)
            experiment_configs[name.strip()] = exp_id.strip()
    
    if not experiment_configs:
        print("Error: No experiments specified. Use --config-file or --exp options.")
        sys.exit(1)
    
    if len(experiment_configs) < 2:
        print("Error: Need at least 2 experiments to compare.")
        sys.exit(1)
    
    print(f"Comparing {len(experiment_configs)} experiments:")
    for name, exp_id in experiment_configs.items():
        print(f"  {name}: {exp_id}")
    
    # Run comparison
    analyzer = ComparisonAnalyzer(experiment_configs, args.output_dir)
    analyzer.generate_all_comparisons()
    
    print(f"\nComparison analysis complete! Results saved to: {analyzer.output_dir}")


if __name__ == "__main__":
    main()
