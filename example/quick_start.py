"""
Quick start script for market simulation
Provides an interactive menu for running different simulation types
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oasis_market.simulation import run_single_simulation
from config import SimulationConfig
from dotenv import load_dotenv

load_dotenv(override=True)


def print_menu():
    """Print interactive menu"""
    print("\n" + "=" * 60)
    print("OASIS Market Simulation - Quick Start")
    print("=" * 60)
    print("\nSelect simulation type:")
    print("1. No Communication")
    print("2. Buyer Communication Only")
    print("3. Seller Communication Only")
    print("4. Both-Side Communication")
    print("5. Custom Configuration")
    print("6. Run Test Environment")
    print("0. Exit")
    print("-" * 60)


async def run_preset_simulation(comm_type: str):
    """Run simulation with preset configuration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = f"quick_start_{comm_type}_{timestamp}.db"
    
    print(f"\nRunning simulation with {comm_type} communication...")
    print(f"Database: {db_path}")
    
    await run_single_simulation(
        db_path,
        market_type=SimulationConfig.MARKET_TYPE,
        communication_type=comm_type
    )
    
    print(f"\n✅ Simulation completed! Results saved to: {db_path}")


async def run_custom_simulation():
    """Run simulation with custom configuration"""
    print("\n--- Custom Configuration ---")
    
    # Get market type
    print("\nSelect market type:")
    print("1. Reputation Only")
    print("2. Reputation and Warrant")
    choice = input("Choice (1-2): ").strip()
    
    market_type = "reputation_only" if choice == "1" else "reputation_and_warrant"
    
    # Get communication type
    print("\nSelect communication type:")
    print("1. None")
    print("2. Buyer")
    print("3. Seller")
    print("4. Both")
    choice = input("Choice (1-4): ").strip()
    
    comm_types = {
        "1": "none",
        "2": "buyer",
        "3": "seller",
        "4": "both"
    }
    comm_type = comm_types.get(choice, "none")
    
    # Get database name
    db_name = input("\nDatabase name (without .db): ").strip()
    if not db_name:
        db_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    db_path = f"{db_name}.db"
    
    print(f"\nRunning custom simulation...")
    print(f"Market Type: {market_type}")
    print(f"Communication: {comm_type}")
    print(f"Database: {db_path}")
    
    await run_single_simulation(db_path, market_type, comm_type)
    
    print(f"\n✅ Simulation completed! Results saved to: {db_path}")


def run_test_environment():
    """Run environment test"""
    print("\nRunning environment test...")
    os.system("python test_environment.py")


async def main():
    """Main interactive loop"""
    while True:
        print_menu()
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "0":
            print("\nExiting...")
            break
        elif choice == "1":
            await run_preset_simulation("none")
        elif choice == "2":
            await run_preset_simulation("buyer")
        elif choice == "3":
            await run_preset_simulation("seller")
        elif choice == "4":
            await run_preset_simulation("both")
        elif choice == "5":
            await run_custom_simulation()
        elif choice == "6":
            run_test_environment()
        else:
            print("\nInvalid choice! Please try again.")
        
        if choice in ["1", "2", "3", "4", "5"]:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("=" * 60)
    print("Welcome to OASIS Market Simulation")
    print("=" * 60)
    print(f"Configuration: {SimulationConfig.NUM_SELLERS} sellers, "
          f"{SimulationConfig.NUM_BUYERS} buyers, "
          f"{SimulationConfig.SIMULATION_ROUNDS} rounds")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and environment setup.")
