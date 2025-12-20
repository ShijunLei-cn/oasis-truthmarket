"""
Environment test script
Quickly verify that all dependencies and modules are properly configured
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        # Test OASIS framework imports
        import oasis
        print("✓ OASIS framework imported")
    except ImportError as e:
        print(f"✗ OASIS framework import failed: {e}")
        return False
    
    try:
        # Test Camel model imports
        from camel.models import ModelFactory
        print("✓ Camel models imported")
    except ImportError as e:
        print(f"✗ Camel models import failed: {e}")
        return False
    
    try:
        # Test local module imports
        from oasis_market import (
            MarketDatabase,
            AgentManager,
            ActionLogger,
            SimulationLogger,
            MarketSimulation
        )
        print("✓ Local oasis_market modules imported")
    except ImportError as e:
        print(f"✗ Local modules import failed: {e}")
        return False
    
    try:
        # Test config and utils
        from config import SimulationConfig
        from utils import print_round_statistics
        from prompt import SELLER_GENERATION_SYS_PROMPT
        print("✓ Config, utils, and prompt modules imported")
    except ImportError as e:
        print(f"✗ Supporting modules import failed: {e}")
        return False
    
    return True


def test_environment_variables():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("MODEL_API_KEY")
    if api_key:
        print(f"✓ MODEL_API_KEY is set (length: {len(api_key)})")
    else:
        print("✗ MODEL_API_KEY is not set")
        print("  Please set it in .env file")
        return False
    
    base_url = os.getenv("MODEL_BASE_URL")
    if base_url:
        print(f"✓ MODEL_BASE_URL is set: {base_url}")
    else:
        print("○ MODEL_BASE_URL is not set (using default)")
    
    return True


def test_database_operations():
    """Test basic database operations"""
    print("\nTesting database operations...")
    
    import tempfile
    import os
    
    # Use a non-existent database path to test initial state handling
    db_path = tempfile.mktemp(suffix='.db')
    
    # Import database module directly to avoid dependency issues
    try:
        # Try importing through package first
        from oasis_market.database import MarketDatabase
    except ImportError:
        # If that fails, import directly from file
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(base_dir, 'oasis_market'))
        from database import MarketDatabase
    
    try:
        db = MarketDatabase(db_path)
        
        # Test basic operations - database doesn't exist yet, should return initial state
        state = db.get_agent_state(1, 'seller')
        assert state['reputation_score'] == 0
        assert state['total_profit'] == 0
        print("✓ Database operations working (initial state)")
        
        # Test product listings when database doesn't exist
        listings = db.get_product_listings()
        assert "No products" in listings
        print("✓ Product listings query works")
        
        # Test seller round summary when database doesn't exist
        summary = db.get_seller_round_summary(1, 1)
        assert summary['advertised_quality'] is None
        assert summary['sold_numbers'] == 0
        print("✓ Seller round summary query works")
        
        # Test with empty database file (no tables)
        # Create empty database file
        with open(db_path, 'w') as f:
            pass
        
        # Should still return initial state when tables don't exist
        state2 = db.get_agent_state(1, 'seller')
        assert state2['reputation_score'] == 0
        print("✓ Database operations work with empty database (no tables)")
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        return True
        
    except Exception as e:
        print(f"✗ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if os.path.exists(db_path):
            os.remove(db_path)
        return False


def test_configuration():
    """Test simulation configuration"""
    print("\nTesting configuration...")
    
    from config import SimulationConfig
    
    print(f"  NUM_SELLERS: {SimulationConfig.NUM_SELLERS}")
    print(f"  NUM_BUYERS: {SimulationConfig.NUM_BUYERS}")
    print(f"  SIMULATION_ROUNDS: {SimulationConfig.SIMULATION_ROUNDS}")
    print(f"  MARKET_TYPE: {SimulationConfig.MARKET_TYPE}")
    print(f"  MODEL_PLATFORM: {SimulationConfig.MODEL_PLATFORM}")
    print(f"  MODEL_TYPE: {SimulationConfig.MODEL_TYPE}")
    
    if SimulationConfig.NUM_SELLERS > 0 and SimulationConfig.NUM_BUYERS > 0:
        print("✓ Configuration is valid")
        return True
    else:
        print("✗ Invalid configuration")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("OASIS Market Simulation - Environment Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Database Operations", test_database_operations),
        ("Configuration", test_configuration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ Environment is properly configured!")
        print("You can now run simulations with:")
        print("  python run_market_simulation.py")
    else:
        print("\n❌ Environment configuration issues detected.")
        print("Please fix the issues above before running simulations.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
