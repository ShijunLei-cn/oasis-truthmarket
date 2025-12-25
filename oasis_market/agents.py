"""
Agent management module for market simulation
Handles agent creation, state management, and ID counter operations
"""

import sys
import itertools
from typing import Dict, List, Optional, Tuple
from prompt import format_seller_history


class AgentManager:
    """Manages agent creation and state in market simulation"""
    
    @staticmethod
    def reset_agent_id_counter():
        """
        Reset agent ID counter to ensure each run starts from 1
        
        Returns:
            None
        """
        # Method 1: Directly import and reset counter in module
        from oasis.social_agent import agents_generator
        agents_generator.id_gen = itertools.count(1)
        print("Agent ID counter reset to 1 (method 1)")
        
        # Method 2: If module is already in sys.modules, reset it too
        if 'oasis.social_agent.agents_generator' in sys.modules:
            module = sys.modules['oasis.social_agent.agents_generator']
            module.id_gen = itertools.count(1)
            print("Agent ID counter reset to 1 (method 2)")
    
    @staticmethod
    def prepare_seller_state(agent, agent_id: int, round_num: int, 
                           history_log: List[Dict], db_manager, 
                           config) -> Tuple[Dict, str]:
        """
        Prepare seller agent state for a round
        
        Args:
            agent: The seller agent
            agent_id: Agent identifier
            round_num: Current round number
            history_log: Historical performance log
            db_manager: Database manager instance
            config: Simulation configuration
            
        Returns:
            Tuple of (state_dict, history_string)
        """
        # Get agent state from database
        state = db_manager.get_agent_state(agent_id, 'seller', round_num=round_num)
        
        # Format history for display
        visible_history_string = format_seller_history(history_log)
        
        # Update agent attributes
        agent.reputation_score = state['reputation_score']
        agent.history_summary = visible_history_string
        # Store budget in agent for potential use
        if 'budget' in state:
            agent.current_budget = state['budget']
        
        return state, visible_history_string
    
    @staticmethod
    def prepare_buyer_state(agent, agent_id: int, round_num: int, 
                          db_manager) -> Dict:
        """
        Prepare buyer agent state for a round
        
        Args:
            agent: The buyer agent
            agent_id: Agent identifier
            round_num: Current round number
            db_manager: Database manager instance
            
        Returns:
            State dictionary
        """
        # Get agent state from database
        state = db_manager.get_agent_state(agent_id, 'buyer', round_num=round_num)
        
        # Update agent attributes
        agent.cumulative_utility = state['cumulative_utility']
        
        return state
    
    @staticmethod
    def update_seller_history(sellers_history: Dict[int, List], 
                            agent_id: int, round_num: int,
                            round_summary: Dict, round_profit: float,
                            total_profit: float, next_reputation: int) -> None:
        """
        Update seller history with round results
        
        Args:
            sellers_history: Dictionary of seller histories
            agent_id: Seller agent ID
            round_num: Current round number
            round_summary: Summary of round performance
            round_profit: Profit earned this round
            total_profit: Total profit so far
            next_reputation: Reputation for next round
        """
        sellers_history[agent_id].append({
            "round": round_num,
            "true_quality": round_summary["true_quality"],
            "advertised_quality": round_summary["advertised_quality"],
            "warrant": round_summary["warrant"],
            "is_sold": round_summary["is_sold"],
            "sold_numbers": round_summary["sold_numbers"],
            "cost": round_summary["cost"],
            "price": round_summary["price"],
            "profit": round_profit,
            "reputation": next_reputation,
            "total_profit": total_profit
        })
    
    @staticmethod
    def store_purchase_info(agent, purchase_info: Dict) -> None:
        """
        Store purchase information in agent for later use
        
        Args:
            agent: Buyer agent
            purchase_info: Dictionary containing purchase details
        """
        agent.last_purchase_info = {
            'transaction_id': purchase_info.get("transaction_id"),
            'product_id': purchase_info.get("product_id"),
            'advertised_quality': purchase_info.get("advertised_quality"),
            'true_quality': purchase_info.get("true_quality"),
            'has_warrant': purchase_info.get("has_warrant"),
            'buyer_utility': purchase_info.get("buyer_utility"),
            'purchase_price': purchase_info.get("purchase_price", 0),
            'seller_id': purchase_info.get("seller_id", 'N/A'),
            'seller_reputation': purchase_info.get("seller_reputation", 0)
        }


# Test cases
if __name__ == "__main__":
    import tempfile
    from database import MarketDatabase
    
    # Test agent ID counter reset
    print("Testing agent ID counter reset...")
    # Note: This test requires oasis package to be installed
    # AgentManager.reset_agent_id_counter()
    print("✓ Agent ID counter reset test skipped (requires oasis package)")
    
    # Test seller history update
    sellers_history = {1: []}
    round_summary = {
        "true_quality": "HQ",
        "advertised_quality": "HQ",
        "warrant": False,
        "is_sold": 1,
        "sold_numbers": 1,
        "cost": 2.0,
        "price": 5.0
    }
    
    AgentManager.update_seller_history(
        sellers_history, 1, 1, round_summary,
        round_profit=3.0, total_profit=3.0, next_reputation=5
    )
    
    assert len(sellers_history[1]) == 1
    assert sellers_history[1][0]["round"] == 1
    assert sellers_history[1][0]["profit"] == 3.0
    print(f"✓ Seller history updated: {sellers_history[1][0]}")
    
    # Test purchase info storage (mock agent)
    class MockAgent:
        def __init__(self):
            self.last_purchase_info = None
    
    agent = MockAgent()
    purchase_info = {
        "transaction_id": 1,
        "product_id": 101,
        "advertised_quality": "HQ",
        "true_quality": "LQ",
        "has_warrant": True,
        "buyer_utility": 0,
        "purchase_price": 5.0,
        "seller_id": 1,
        "seller_reputation": 3
    }
    
    AgentManager.store_purchase_info(agent, purchase_info)
    assert agent.last_purchase_info["transaction_id"] == 1
    assert agent.last_purchase_info["true_quality"] == "LQ"
    print(f"✓ Purchase info stored: {agent.last_purchase_info}")
    
    print("\nAll agent management tests passed!")
