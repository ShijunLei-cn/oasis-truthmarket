"""
Unified market simulation runner
Supports all communication types through command line arguments
"""

import asyncio
import sys
import os
import argparse
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.simulation import run_single_simulation
from config import SimulationConfig

load_dotenv(override=True)


def parse_arguments():
    """
    Parse command line arguments using argparse
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Run OASIS market simulation with configurable parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s test.db
  %(prog)s test.db --market-type reputation_only --communication buyer
  %(prog)s test.db -m reputation_and_warrant -c both
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        'db_path',
        nargs='?',
        default='market_simulation.db',
        help='Database file path (default: market_simulation.db)'
    )
    
    parser.add_argument(
        '-m', '--market-type',
        dest='market_type',
        choices=['reputation_only', 'reputation_and_warrant'],
        default=None,
        help='Market type: reputation_only or reputation_and_warrant (default: from config)'
    )
    
    parser.add_argument(
        '-c', '--communication',
        dest='communication_type',
        choices=['none', 'seller', 'buyer', 'both'],
        default='none',
        help='Communication type: none, seller, buyer, or both (default: none)'
    )
    
    parser.add_argument(
        '-cc', '--communication-channel-type',
        dest='communication_channel_type',
        choices=['Fake', 'Real'],
        default='Real',
        help='Communication channel type: Fake or Real (default: Fake)'
    )
    
    return parser.parse_args()


async def main():
    """
    Main entry point for market simulation
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Print configuration
    print("=" * 60)
    print("Market Simulation Configuration")
    print("=" * 60)
    print(f"Database: {args.db_path}")
    print(f"Market Type: {args.market_type or SimulationConfig.MARKET_TYPE}")
    print(f"Communication: {args.communication_type}")
    print(f"Communication Channel Type: {args.communication_channel_type}")
    print("=" * 60)
    print(f"Sellers: {SimulationConfig.NUM_SELLERS}")
    print(f"Buyers: {SimulationConfig.NUM_BUYERS}")
    print(f"Rounds: {SimulationConfig.SIMULATION_ROUNDS}")
    print("=" * 60)
    
    # Run simulation
    await run_single_simulation(
        args.db_path,
        market_type=args.market_type,
        communication_type=args.communication_type,
        communication_channel_type=args.communication_channel_type
    )
    


if __name__ == "__main__":
    asyncio.run(main())
