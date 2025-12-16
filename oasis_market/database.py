"""
Database operations module for market simulation
Provides database connectivity and operations for market data
"""

import sqlite3
import os
from typing import Dict, Optional, List, Tuple, Any


class MarketDatabase:
    """Handles all database operations for the market simulation"""
    
    def __init__(self, database_path: str):
        """
        Initialize database connection
        
        Args:
            database_path: Path to the SQLite database file
        """
        self.database_path = database_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file and directory exist"""
        if self.database_path and not os.path.exists(self.database_path):
            db_dir = os.path.dirname(self.database_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
    
    def _table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        if not os.path.exists(self.database_path):
            return False
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_agent_state(self, agent_id: int, role: str, round_num: int = -1) -> Dict:
        """
        Get the state of an agent at a specific round or current state
        
        Args:
            agent_id: Agent identifier
            role: Role of agent ('seller' or 'buyer')
            round_num: Round number to get state for (-1 for current)
            
        Returns:
            Dictionary containing agent state
        """
        if not os.path.exists(self.database_path) or not self._table_exists('user'):
            # Return initial states if database doesn't exist or tables not initialized
            if role == 'seller':
                return {'reputation_score': 0, 'total_profit': 0}
            else:
                return {'cumulative_utility': 0, 'total_utility': 0}
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        state = {}
        if role == 'seller':
            # Get seller basic information
            cursor.execute(
                "SELECT reputation_score, profit_utility_score FROM user WHERE agent_id = ?",
                (agent_id,)
            )
            result = cursor.fetchone()
            state['reputation_score'] = result[0] if result else 0
            state['total_profit'] = result[1] if result else 0
            
            # Get sales information for this round
            if round_num > 0:
                user_id = agent_id
                cursor.execute(
                    "SELECT COUNT(*), SUM(seller_profit) FROM transactions WHERE seller_id = ? AND round_number = ?",
                    (user_id, round_num)
                )
                sales_result = cursor.fetchone()
                state['round_sales'] = sales_result[0] if sales_result else 0
                state['round_profit'] = sales_result[1] if sales_result and sales_result[1] is not None else 0
        
        elif role == 'buyer':
            # Get buyer basic information
            cursor.execute(
                "SELECT profit_utility_score FROM user WHERE agent_id = ?",
                (agent_id,)
            )
            result = cursor.fetchone()
            state['cumulative_utility'] = result[0] if result and result[0] is not None else 0
            state['total_utility'] = result[0] if result and result[0] is not None else 0
            
            # Get purchase information for this round
            if round_num > 0:
                user_id = agent_id
                cursor.execute(
                    "SELECT COUNT(*), SUM(buyer_utility) FROM transactions WHERE buyer_id = ? AND round_number = ?",
                    (user_id, round_num)
                )
                purchase_result = cursor.fetchone()
                state['round_purchases'] = purchase_result[0] if purchase_result else 0
                state['round_utility'] = purchase_result[1] if purchase_result and purchase_result[1] is not None else 0
        
        conn.close()
        return state
    
    def get_seller_round_summary(self, seller_id: int, round_num: int) -> Dict:
        """
        Get seller's product listing information and sales status for a specific round
        
        Args:
            seller_id: Seller agent ID
            round_num: Round number
            
        Returns:
            Dictionary containing seller round summary
        """
        # Initialize summary with default values
        summary = {
            "advertised_quality": None,
            "true_quality": None,
            "warrant": None,
            "is_sold": 0,
            "sold_numbers": 0,
            "cost": 0,
            "price": 0
        }
        
        if not os.path.exists(self.database_path) or not self._table_exists('user'):
            return summary
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # First get user_id from agent_id
        cursor.execute(
            "SELECT user_id FROM user WHERE agent_id = ?",
            (seller_id,)
        )
        user_result = cursor.fetchone()
        if not user_result:
            conn.close()
            return summary
        
        # Check if product table exists
        if not self._table_exists('product'):
            conn.close()
            return summary
            
        user_id = user_result[0]
        
        # Query in product table by user_id and round_number
        cursor.execute(
            "SELECT advertised_quality, true_quality, has_warrant, is_sold, cost, price "
            "FROM product WHERE user_id = ? AND round_number = ? ORDER BY product_id",
            (user_id, round_num)
        )
        all_results = cursor.fetchall()
        
        if all_results:
            one_result = all_results[0]
            summary["advertised_quality"] = one_result[0]
            summary["true_quality"] = one_result[1]
            summary["warrant"] = one_result[2]
            summary["is_sold"] = one_result[3]
            summary["sold_numbers"] = sum(1 for p in all_results if p[3])
            summary["cost"] = one_result[4]
            summary["price"] = one_result[5]
        
        conn.close()
        return summary
    
    def get_product_listings(self) -> str:
        """
        Get current product listings
        
        Returns:
            String description of available products
        """
        if not os.path.exists(self.database_path) or not self._table_exists('product'):
            return "No products are currently on sale."
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        listings = "No products are currently on sale."
        
        # Check if status column exists
        cursor.execute("PRAGMA table_info(product)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'status' not in columns:
            conn.close()
            return "Database schema is incorrect: 'product' table is missing the 'status' column."
        
        cursor.execute(
            """
            SELECT p.product_id, u.agent_id, p.advertised_quality, p.price, p.has_warrant, 
                   COALESCE(u.reputation_score, 0) AS reputation_score
            FROM product p
            LEFT JOIN user u ON u.user_id = p.user_id
            WHERE p.status = 'on_sale'
            """
        )
        products = cursor.fetchall()
        
        if products:
            listings = "Here is the list of products currently on sale:\n"
            for p in products:
                warrant_info = " (Warranted)" if p[4] else ""
                listings += (
                    f"- Product ID: {p[0]}, Seller ID: {p[1]}, "
                    f"Seller Reputation: {p[5]}, "
                    f"Advertised Quality: {p[2]}, Price: ${p[3]:.2f}{warrant_info}\n"
                )
        
        conn.close()
        return listings
    
    def initialize_market_roles(self, agent_graph, num_sellers: int, num_buyers: int):
        """
        Initialize market roles for all agents in the database
        
        Args:
            agent_graph: Graph containing all agents
            num_sellers: Number of seller agents
            num_buyers: Number of buyer agents
        """
        print("Initializing market roles in the database...")
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get information for all agents
        agents_info = []
        actual_agent_ids = []
        for agent_id, agent in agent_graph.get_agents():
            role = agent.user_info.profile.get("other_info", {}).get("role")
            agents_info.append((agent_id, role))
            actual_agent_ids.append(agent_id)
        
        print(f"Found {len(agents_info)} agents to initialize")
        print(f"Actual agent IDs in graph: {sorted(actual_agent_ids)}")
        
        # Set seller roles (first NUM_SELLERS agents)
        for i in range(num_sellers):
            agent_id = i + 1
            cursor.execute(
                "UPDATE user SET role = ?, reputation_score = ?, profit_utility_score = ? WHERE agent_id = ?",
                ('seller', 0, 0.0, agent_id)
            )
            print(f"Set agent {agent_id} as seller")
        
        # Set buyer roles (next NUM_BUYERS agents)
        for i in range(num_buyers):
            agent_id = num_sellers + i + 1
            cursor.execute(
                "UPDATE user SET role = ?, profit_utility_score = ? WHERE agent_id = ?",
                ('buyer', 0.0, agent_id)
            )
            print(f"Set agent {agent_id} as buyer")
        
        conn.commit()
        
        # Verify setup results
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'seller'")
        seller_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'buyer'")
        buyer_count = cursor.fetchone()[0]
        
        print(f"Market roles initialized successfully: {seller_count} sellers, {buyer_count} buyers")
        conn.close()
    
    def compute_next_round_reputation(self, agent_id: int, round_num: int, reputation_lag: int) -> int:
        """
        Calculate reputation that will be shown in the next round
        
        Args:
            agent_id: Seller agent ID
            round_num: Current round number
            reputation_lag: Reputation display lag in rounds
            
        Returns:
            Reputation score for next round
        """
        if not os.path.exists(self.database_path) or not self._table_exists('transactions'):
            return 0
        
        next_round_cutoff = max(0, round_num + 1 - reputation_lag)
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(t.rating) as cnt, COALESCE(SUM(t.rating), 0)
                FROM transactions t
                WHERE t.rating IS NOT NULL AND t.round_number <= ? AND t.seller_id = ?
                """,
                (next_round_cutoff, agent_id)
            )
            result = cursor.fetchone()
            return result[1] if result else 0
    
    def cleanup(self):
        """Clean up database file if it exists"""
        if os.path.exists(self.database_path):
            os.remove(self.database_path)
            print(f"Database cleaned up: {self.database_path}")


# Test cases
if __name__ == "__main__":
    import tempfile
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Test database operations
    db = MarketDatabase(db_path)
    
    # Test getting initial agent state
    seller_state = db.get_agent_state(1, 'seller')
    assert seller_state['reputation_score'] == 0
    assert seller_state['total_profit'] == 0
    print(f"✓ Initial seller state: {seller_state}")
    
    buyer_state = db.get_agent_state(11, 'buyer')
    assert buyer_state['cumulative_utility'] == 0
    assert buyer_state['total_utility'] == 0
    print(f"✓ Initial buyer state: {buyer_state}")
    
    # Test getting product listings when empty
    listings = db.get_product_listings()
    assert listings == "No products are currently on sale."
    print(f"✓ Empty product listings: {listings}")
    
    # Test seller round summary when empty
    summary = db.get_seller_round_summary(1, 1)
    assert summary['advertised_quality'] is None
    assert summary['sold_numbers'] == 0
    print(f"✓ Empty seller summary: {summary}")
    
    # Clean up
    db.cleanup()
    assert not os.path.exists(db_path)
    print("✓ Database cleaned up successfully")
    
    print("\nAll database tests passed!")
