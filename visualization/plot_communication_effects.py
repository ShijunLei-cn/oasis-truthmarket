#!/usr/bin/env python3
"""
Command-line interface for communication effects visualization
Plots mean ± std with shaded areas, comparing 4 communication conditions
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.communication_effects import create_communication_effects_plot


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Visualize communication effects in rep-only market',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --experiments-dir experiments
  %(prog)s -e experiments -o output.png
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        '-e', '--experiments-dir',
        dest='experiments_dir',
        default='experiments',
        help='Directory containing experiment folders (default: experiments)'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default=None,
        help='Output file path (default: experiments/communication_effects_rep_only.png)'
    )
    
    args = parser.parse_args()
    
    # Determine output file path
    if args.output_file:
        output_file = args.output_file
    else:
        output_file = os.path.join(args.experiments_dir, 'communication_effects_rep_only.png')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # Create the plot
    print(f"Analyzing experiments in: {args.experiments_dir}")
    print(f"Output will be saved to: {output_file}")
    
    create_communication_effects_plot(args.experiments_dir, output_file)


if __name__ == "__main__":
    main()

