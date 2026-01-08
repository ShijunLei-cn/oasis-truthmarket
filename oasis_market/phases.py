"""
Market phases module for simulation
Handles different phases of the market simulation including seller actions, buyer actions, and communication phases
"""

import random
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from oasis.environment.env_action import LLMAction
from prompt import SELLER_ROUND_PROMPT, BUYER_ROUND_PROMPT, MarketEnv_prompt


class MarketPhase:
    """Base class for market phases"""
    
    def __init__(self, env, agent_graph, db_manager, action_logger, config):
        """
        Initialize market phase
        
        Args:
            env: Environment instance
            agent_graph: Agent graph instance
            db_manager: Database manager instance
            action_logger: Action logger instance
            config: Simulation configuration
        """
        self.env = env
        self.agent_graph = agent_graph
        self.db_manager = db_manager
        self.action_logger = action_logger
        self.config = config
    
    async def execute(self, round_num: int, **kwargs) -> Any:
        """
        Execute the phase
        
        Args:
            round_num: Current round number
            **kwargs: Additional phase-specific arguments
            
        Returns:
            Phase execution results
        """
        raise NotImplementedError("Subclasses must implement execute method")


class SellerListingPhase(MarketPhase):
    """Handles seller product listing phase"""
    
    async def execute(self, round_num: int, sellers_history: Dict) -> None:
        """
        Execute seller listing phase
        
        Args:
            round_num: Current round number
            sellers_history: Dictionary of seller histories
        """
        from .agents import AgentManager
        from .logging import SimulationLogger
        
        SimulationLogger.print_phase_header(round_num, "Seller Action Phase")
        
        seller_actions = {}
        self.env.market_phase = "listing"
        
        for agent_id, agent in self.agent_graph.get_agents():
            if agent.user_info.profile.get("role") == 'seller':
                # Prepare seller state
                state, visible_history_string = AgentManager.prepare_seller_state(
                    agent, agent_id, round_num,
                    sellers_history.get(agent_id, []),
                    self.db_manager, self.config
                )
                
                # Update environment state
                self.env.current_round = round_num
                
                # Prepare round prompt with budget information
                budget = state.get('budget', 10.0)
                total_profit = state.get('total_profit', 0)
                reputation_score = state.get('reputation_score', 0)
                
                # Add budget information to the prompt
                seller_round_prompt = SELLER_ROUND_PROMPT.format(
                    history_summary=visible_history_string
                )
                
                # Tools available for sellers
                listing_tools = ['list_product']
                
                # Conditionally add exit/re-entry tools (skip if config is None)
                exit_round = self.config.EXIT_ROUND if self.config.EXIT_ROUND is not None else None
                reentry_round = self.config.REENTRY_ALLOWED_ROUND if self.config.REENTRY_ALLOWED_ROUND is not None else None
                
                if exit_round is not None and round_num == exit_round:
                    listing_tools.append('exit_market')
                    seller_round_prompt += "\n\nYou are now allowed to exit the market.\n"
                if reentry_round is not None and round_num == reentry_round:
                    listing_tools.append('reenter_market')
                    seller_round_prompt += "\n\nYou are now allowed to re-enter the market.\n"
                
                seller_actions[agent] = LLMAction(
                    extra_action=listing_tools,
                    extra_prompt=seller_round_prompt,
                    level="market"
                )
        
        if seller_actions:
            await self.env.step(seller_actions)
            self.action_logger.save_action_records(self.env, round_num, 'seller_listing')
        
        print("All seller actions are complete.")


class BuyerPurchasePhase(MarketPhase):
    """Handles buyer purchase phase"""
    
    async def execute(self, round_num: int) -> List[Dict]:
        """
        Execute buyer purchase phase
        
        Args:
            round_num: Current round number
            
        Returns:
            List of purchase results
        """
        from .agents import AgentManager
        from .logging import SimulationLogger
        
        SimulationLogger.print_phase_header(round_num, "Buyer Action Phase 1: Purchase")
        
        self.env.market_phase = "purchase"
        purchase_results = []
        
        # Get and shuffle buyers
        agent_lists = self.agent_graph.get_agents()
        buyers = [pair for pair in agent_lists if pair[1].user_info.profile.get("role") == "buyer"]
        random.shuffle(buyers)
        
        for agent_id, agent in buyers:
            buyer_actions = {}
            state = AgentManager.prepare_buyer_state(agent, agent_id, round_num, self.db_manager)
            
            # Prepare round prompt
            buyer_round_prompt = (
                "\n\nIn this phase, you are only allowed to perform the purchase_product_id action to purchase a product. "
                "Based on the market environment, product information, and your preferences, choose whether and which product to purchase. "
                "You cannot perform any other actions during this phase.\n"
            )
            
            # Tools available for buyers in purchase phase
            purchase_tools = ['purchase_product_id']
            buyer_actions[agent] = LLMAction(
                extra_action=purchase_tools,
                extra_prompt=buyer_round_prompt,
                level="market"
            )
            
            results = await self.env.step(buyer_actions)
            self.action_logger.save_action_records(self.env, round_num, 'buyer_purchase')
            
            # Collect results
            if isinstance(results, list):
                purchase_results.extend(results)
            elif isinstance(results, dict):
                purchase_results.append(results)
        
        print("All purchase actions are attempted.")
        return purchase_results


class BuyerRatingPhase(MarketPhase):
    """Handles buyer rating and challenge phase"""
    
    async def execute(self, round_num: int, purchase_results: List[Dict], market_type: str) -> None:
        """
        Execute buyer rating phase
        
        Args:
            round_num: Current round number
            purchase_results: Results from purchase phase
            market_type: Type of market ('reputation_only' or 'reputation_and_warrant')
        """
        from .agents import AgentManager
        from .logging import SimulationLogger
        
        SimulationLogger.print_phase_header(round_num, "Buyer Action Phase 2: Challenge & Rate")
        
        post_purchase_actions = {}
        self.env.market_phase = "rating"
        
        successful_purchases = [res for res in purchase_results if res and res.get("success")]
        
        if successful_purchases:
            for purchase_info in successful_purchases:
                agent_id = purchase_info.get("agent_id")
                if agent_id is None:
                    continue
                
                agent = self.agent_graph.get_agent(agent_id)
                
                # Tools available for buyers in rating phase
                rating_tools = ['rate_transaction']
                if market_type != 'reputation_only':
                    rating_tools.append('challenge_warrant')
                
                # Store purchase information in agent
                AgentManager.store_purchase_info(agent, purchase_info)
                
                # Prepare rating prompt
                if market_type == 'reputation_only':
                    buyer_rating_prompt = (
                        "\n\nIn this phase, you are allowed to perform the rate_transaction action to rate a transaction. "
                        "Based on the market environment, product information, and your preferences, choose whether and which product to rate. "
                        "You cannot perform any other actions during this phase.\n"
                    )
                else:
                    buyer_rating_prompt = (
                        "\n\nIn this phase, you are allowed to perform the rate_transaction action to rate a transaction. "
                        "Or perform the challenge_warrant action to challenge the warrant of a transaction. "
                        "Based on the market environment, product information, and your preferences, choose whether and which product to rate. "
                        "Or challenge the warrant of a transaction. "
                        "You cannot perform any other actions during this phase.\n"
                    )
                
                post_purchase_actions[agent] = LLMAction(
                    extra_action=rating_tools,
                    extra_prompt=buyer_rating_prompt,
                    level="market"
                )
        
        if post_purchase_actions:
            await self.env.step(post_purchase_actions)
            self.action_logger.save_action_records(self.env, round_num, 'buyer_rating')
        
        print("All post-purchase actions are complete.")


class CommunicationPhase(MarketPhase):
    """Handles communication phases for sellers or buyers"""
    
    async def execute(self, round_num: int, role: str) -> None:
        """
        Execute communication phase
        
        Args:
            round_num: Current round number
            role: 'seller' or 'buyer' indicating who is communicating
        """
        from .agents import AgentManager
        from .logging import SimulationLogger
        
        phase_name = f"{role.capitalize()} Communication Phase"
        SimulationLogger.print_phase_header(round_num, phase_name)
        
        communication_actions = {}
        self.env.market_phase = "communication"
        
        for agent_id, agent in self.agent_graph.get_agents():
            if agent.user_info.profile.get("role") == role:
                if role == 'seller':
                    # Prepare seller state for communication
                    state = self.db_manager.get_agent_state(agent_id, 'seller', round_num=round_num)
                    self.env.current_round = round_num
                    
                    communication_prompt = (
                        "\n\nIn this phase, you are allowed to perform some social platform actions to communicate with other sellers. "
                        "You cannot perform any other actions during this phase.\n"
                        "You can share your plan of listing products, product information, your experience, or any other information with other sellers to help them make listing decisions.\n"
                    )
                else:  # buyer
                    # Prepare buyer state for communication
                    state = AgentManager.prepare_buyer_state(agent, agent_id, round_num, self.db_manager)
                    self.env.current_round = round_num
                    
                    # Get buyer's last transaction info if available
                    last_purchase_info = getattr(agent, 'last_purchase_info', {})
                    seller_id = last_purchase_info.get('seller_id', 'N/A')
                    advertised_quality = last_purchase_info.get('advertised_quality', 'N/A')
                    true_quality = last_purchase_info.get('true_quality', 'N/A')
                    
                    communication_prompt = (
                        "\n\nIn this phase, you are allowed to perform some social platform actions to communicate with other buyers. "
                        "You cannot perform any other actions during this phase.\n"
                        "You can share your purchase experience, product information, seller reputation, or any other information with other buyers to help them make purchase decisions.\n"
                    )
                
                # Common communication tools
                communication_tools = ['create_post', 'quote_post', 'like_post', 'dislike_post']
                
                communication_actions[agent] = LLMAction(
                    extra_action=communication_tools,
                    extra_prompt=communication_prompt,
                    level="communication"
                )
        
        if communication_actions:
            await self.env.step(communication_actions)
            self.action_logger.save_action_records(self.env, round_num, f'{role}_communication')
        
        print(f"All {role} communication actions are complete.")


# Test cases
if __name__ == "__main__":
    print("Phase module tests")
    print("This module contains phase execution logic that requires async environment and agent setup.")
    print("Integration tests should be run with the full simulation.")
    
    # Test basic phase structure
    class MockEnv:
        def __init__(self):
            self.market_phase = None
            self.current_round = None
    
    class MockAgentGraph:
        def get_agents(self):
            return []
    
    class MockConfig:
        EXIT_ROUND = 7
        REENTRY_ALLOWED_ROUND = 5
    
    # Create mock instances
    env = MockEnv()
    agent_graph = MockAgentGraph()
    config = MockConfig()
    
    # Test phase initialization
    phase = MarketPhase(env, agent_graph, None, None, config)
    assert phase.env == env
    assert phase.agent_graph == agent_graph
    assert phase.config == config
    print("✓ Phase initialization successful")
    
    # Test specific phases can be instantiated
    seller_phase = SellerListingPhase(env, agent_graph, None, None, config)
    assert isinstance(seller_phase, MarketPhase)
    print("✓ SellerListingPhase instantiated")
    
    buyer_purchase_phase = BuyerPurchasePhase(env, agent_graph, None, None, config)
    assert isinstance(buyer_purchase_phase, MarketPhase)
    print("✓ BuyerPurchasePhase instantiated")
    
    buyer_rating_phase = BuyerRatingPhase(env, agent_graph, None, None, config)
    assert isinstance(buyer_rating_phase, MarketPhase)
    print("✓ BuyerRatingPhase instantiated")
    
    communication_phase = CommunicationPhase(env, agent_graph, None, None, config)
    assert isinstance(communication_phase, MarketPhase)
    print("✓ CommunicationPhase instantiated")
    
    print("\nAll phase tests passed!")
